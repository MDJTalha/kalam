import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.models import (
    CRMAccount,
    CRMContract,
    CRMInvoice,
    CRMPayment,
    Permission,
    Role,
    RolePermission,
    SaaSOffer,
    SaaSPlan,
    SessionRecord,
    Tenant,
    User,
    UserRole,
)
from app.db.session import SessionLocal
from app.main import app

OPS_SLUG = "kalam"
PASSWORD = "SaaSCRMTest!2026"


async def _create_ops_user(email: str, role_name: str = "Sales Operations") -> None:
    async with SessionLocal() as db:
        # Keep test identities separated: commercial staff never receive
        # platform support or tenant lifecycle privileges by implication.
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        if tenant is None:
            tenant = Tenant(
                name="Kalam",
                slug=OPS_SLUG,
                status="active",
                settings={"workspace_type": "saas_operations"},
            )
            db.add(tenant)
            await db.flush()

        permission_definitions = {
            "saas.crm.read": "View Kalam SaaS commercial CRM",
            "saas.crm.manage": "Manage Kalam SaaS commercial CRM",
            "platform.tenants.read": "View platform tenant registry",
            "platform.tenants.manage": "Manage customer tenant lifecycle",
            "platform.health.read": "View platform health",
            "platform.incidents.manage": "Manage platform incidents",
            "platform.support.access": "Use audited support access",
            "platform.audit.read": "View platform audit records",
        }
        permissions: dict[str, Permission] = {}
        for key, description in permission_definitions.items():
            permission = await db.scalar(select(Permission).where(Permission.key == key))
            if permission is None:
                permission = Permission(key=key, description=description)
                db.add(permission)
                await db.flush()
            permissions[key] = permission

        role_permissions = {
            "SaaS Owner": ["saas.crm.read"],
            "Sales Operations": ["saas.crm.read", "saas.crm.manage"],
            "Platform Developer": [
                "platform.tenants.read", "platform.tenants.manage", "platform.health.read",
                "platform.incidents.manage", "platform.support.access", "platform.audit.read",
            ],
        }
        if role_name not in role_permissions:
            raise ValueError(f"Unsupported test role: {role_name}")
        roles: dict[str, Role] = {}
        for name, keys in role_permissions.items():
            role = await db.scalar(select(Role).where(Role.tenant_id == tenant.id, Role.name == name))
            if role is None:
                role = Role(
                    tenant_id=tenant.id, name=name,
                    description=f"Test-only {name} role", role_kind="platform",
                )
                db.add(role)
                await db.flush()
            roles[name] = role
            for key in keys:
                membership = await db.scalar(select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[key].id,
                ))
                if membership is None:
                    db.add(RolePermission(
                        role_id=role.id, permission_id=permissions[key].id
                    ))

        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(PASSWORD),
            first_name="Kalam",
            last_name="Role Test",
            job_title=role_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=roles[role_name].id))
        await db.commit()


async def _cleanup(email: str, plan_code: str, account_slug: str | None = None, offer_code: str | None = None, provisioned_slug: str | None = None) -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        if tenant is None:
            return
        if account_slug:
            await db.execute(delete(CRMAccount).where(CRMAccount.ops_tenant_id == tenant.id, CRMAccount.slug == account_slug))
        if provisioned_slug:
            await db.execute(delete(Tenant).where(Tenant.slug == provisioned_slug))
        if offer_code:
            await db.execute(delete(SaaSOffer).where(SaaSOffer.ops_tenant_id == tenant.id, SaaSOffer.code == offer_code))
        plan = await db.scalar(select(SaaSPlan).where(SaaSPlan.ops_tenant_id == tenant.id, SaaSPlan.code == plan_code))
        if plan is not None:
            await db.execute(delete(SaaSPlan).where(SaaSPlan.id == plan.id))
        user = await db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
        if user is not None:
            await db.execute(delete(SessionRecord).where(SessionRecord.user_id == user.id))
            await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
            await db.execute(delete(User).where(User.id == user.id))
        await db.commit()


async def _tenant_id(slug: str):
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
        assert tenant is not None
        return tenant.id


def test_ops_user_can_publish_plan_to_public_catalog():
    suffix = uuid4().hex[:8]
    email = f"crm-test-{suffix}@example.com"
    code = f"test-plan-{suffix}"
    asyncio.run(_create_ops_user(email))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": email,
                "password": PASSWORD,
            })
            assert login.status_code == 200, login.text

            created = client.post("/api/v1/saas/crm/plans", json={
                "code": code,
                "name": "CRM Test Plan",
                "billing_model": "per_user",
                "currency": "USD",
                "monthly_price_minor": 2500,
                "annual_price_minor": 25000,
                "trial_days": 14,
                "minimum_seats": 10,
                "features": ["Test feature"],
                "status": "active",
                "public_visible": True,
            })
            assert created.status_code == 201, created.text

            public = client.get("/api/v1/saas/public/catalog")
            assert public.status_code == 200
            plans = public.json()["plans"]
            assert any(item["code"] == code and item["public_visible"] is True for item in plans)
    finally:
        asyncio.run(_cleanup(email, code))


def test_demo_admin_can_open_isolated_crm_sandbox():
    with TestClient(app, base_url="http://127.0.0.1") as client:
        login = client.post("/api/v1/auth/login", json={
            "tenant_slug": "demo-corporation",
            "email": "admin@demo.corp",
            "password": os.environ["CI_FIXTURE_PASSWORD"],
        })
        assert login.status_code == 200, login.text

        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200, me.text
        permissions = set(me.json().get("permissions", []))
        assert not any(key.startswith("saas.crm.") for key in permissions)

        crm_read_paths = [
            "/api/v1/saas/crm/overview",
            "/api/v1/saas/crm/accounts",
            "/api/v1/saas/crm/tenants",
            "/api/v1/saas/crm/plans",
            "/api/v1/saas/crm/offers",
            "/api/v1/saas/crm/trials",
            "/api/v1/saas/crm/subscriptions",
            "/api/v1/saas/crm/contracts",
            "/api/v1/saas/crm/invoices",
            "/api/v1/saas/crm/payments",
            "/api/v1/saas/crm/forecast",
            "/api/v1/saas/crm/onboarding",
            "/api/v1/saas/crm/renewals?days=180",
            "/api/v1/saas/crm/tasks",
            "/api/v1/saas/crm/team",
            "/api/v1/saas/crm/opportunities",
            "/api/v1/saas/crm/certifications",
        ]
        for path in crm_read_paths:
            response = client.get(path)
            assert response.status_code == 403, f"{path}: {response.status_code} {response.text}"

        tenants = client.get("/api/v1/saas/crm/tenants")
        assert tenants.status_code == 403
        assert client.post(f"/api/v1/saas/crm/accounts/{uuid4()}/provision-tenant", json={}).status_code == 403
        assert client.patch(f"/api/v1/saas/crm/tenants/{uuid4()}", json={"status": "inactive"}).status_code == 403

        inquiries = client.get("/api/v1/marketing/inquiries")
        assert inquiries.status_code == 200, inquiries.text
        assert inquiries.json() == []


async def _cleanup_finance(email: str, account_slug: str) -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        if tenant is None:
            return
        account = await db.scalar(select(CRMAccount).where(CRMAccount.ops_tenant_id == tenant.id, CRMAccount.slug == account_slug))
        if account is not None:
            await db.execute(delete(CRMAccount).where(CRMAccount.id == account.id))
        user = await db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
        if user is not None:
            await db.execute(delete(SessionRecord).where(SessionRecord.user_id == user.id))
            await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
            await db.execute(delete(User).where(User.id == user.id))
        await db.commit()


def test_finance_invoice_payment_reconciliation_and_guards():
    suffix = uuid4().hex[:8]
    email = f"finance-test-{suffix}@example.com"
    account_slug = f"finance-account-{suffix}"
    asyncio.run(_create_ops_user(email))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": email,
                "password": PASSWORD,
            })
            assert login.status_code == 200, login.text

            account_response = client.post("/api/v1/saas/crm/accounts", json={
                "name": "Finance Test Account",
                "slug": account_slug,
                "account_type": "client",
                "lifecycle_stage": "customer",
            })
            assert account_response.status_code == 201, account_response.text
            account_id = account_response.json()["id"]
            page = client.get("/api/v1/saas/crm/page/accounts", params={"q": account_slug, "limit": 1, "offset": 0})
            assert page.status_code == 200 and page.json()["total"] == 1
            assert page.json()["items"][0]["id"] == account_id
            next_page = client.get("/api/v1/saas/crm/page/accounts", params={"q": account_slug, "limit": 1, "offset": 1})
            assert next_page.status_code == 200 and next_page.json()["items"] == []
            # Tenant lifecycle is not a commercial write; Sales Operations
            # must be rejected before target-tenant existence is disclosed.
            assert client.patch(f"/api/v1/saas/crm/tenants/{uuid4()}", json={"status": "inactive"}).status_code == 403
            export = client.get("/api/v1/saas/crm/export/accounts.csv", params={"q": account_slug, "stage": "customer"})
            assert export.status_code == 200, export.text
            assert account_slug in export.text
            assert client.get("/api/v1/saas/crm/export/accounts.csv", params={"q": "nonexistent-account-zz"}).text.count(account_slug) == 0
            contract = client.post("/api/v1/saas/crm/contracts", json={
                "account_id": account_id, "reference": f"CON-{suffix}",
                "status": "draft", "currency": "USD",
                "ends_at": (datetime.now(UTC) + timedelta(days=20)).isoformat(),
            })
            assert contract.status_code == 201, contract.text
            contract_page = client.get("/api/v1/saas/crm/page/contracts", params={
                "account_id": account_id, "status": "draft", "limit": 1,
            })
            assert contract_page.status_code == 200, contract_page.text
            assert contract_page.json()["total"] == 1
            assert contract_page.json()["counts"]["draft_review"] == 1
            assert contract_page.json()["counts"]["expiring_90_days"] == 1
            assert contract_page.json()["items"][0]["id"] == contract.json()["id"]
            beyond_contracts = client.get("/api/v1/saas/crm/page/contracts", params={
                "account_id": account_id, "status": "draft", "limit": 1, "offset": 1,
            })
            assert beyond_contracts.status_code == 200 and beyond_contracts.json()["items"] == []

            invoice_response = client.post("/api/v1/saas/crm/invoices", json={
                "account_id": account_id,
                "invoice_number": f"INV-{suffix}",
                "status": "issued",
                "currency": "USD",
                "amount_minor": 10000,
                "tax_minor": 1000,
            })
            assert invoice_response.status_code == 201, invoice_response.text
            assert invoice_response.json()["total_minor"] == 11000
            invoice_id = invoice_response.json()["id"]
            assert client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"status": "paid"}).status_code == 422
            assert client.post("/api/v1/saas/crm/invoices", json={
                "account_id": account_id, "invoice_number": f"BAD-{suffix}",
                "status": "paid", "currency": "USD", "amount_minor": 100,
            }).status_code == 422
            paged_invoices = client.get("/api/v1/saas/crm/page/invoices", params={"account_id": account_id, "status": "issued", "limit": 1})
            assert paged_invoices.status_code == 200, paged_invoices.text
            assert paged_invoices.json()["total"] == 1
            assert paged_invoices.json()["items"][0]["id"] == invoice_id

            invoices = client.get("/api/v1/saas/crm/invoices")
            assert invoices.status_code == 200, invoices.text
            invoice = next(item for item in invoices.json() if item["id"] == invoice_id)
            assert invoice["outstanding_minor"] == 11000

            wrong_currency = client.post("/api/v1/saas/crm/payments", json={
                "invoice_id": invoice_id,
                "amount_minor": 1000,
                "currency": "PKR",
            })
            assert wrong_currency.status_code == 422

            first_payment = client.post("/api/v1/saas/crm/payments", json={
                "invoice_id": invoice_id,
                "amount_minor": 6000,
                "currency": "USD",
                "method": "bank_transfer",
            })
            assert first_payment.status_code == 201, first_payment.text
            assert first_payment.json()["invoice_status"] == "partially_paid"
            paged_payments = client.get("/api/v1/saas/crm/page/payments", params={"account_id": account_id, "status": "received", "limit": 1})
            assert paged_payments.status_code == 200, paged_payments.text
            assert paged_payments.json()["total"] == 1
            assert paged_payments.json()["items"][0]["invoice_id"] == invoice_id

            forecast = client.get("/api/v1/saas/crm/forecast")
            assert forecast.status_code == 200, forecast.text
            usd_receivables = next(item for item in forecast.json()["open_invoices"] if item["currency"] == "USD")
            assert usd_receivables["outstanding_minor"] >= 5000

            overpayment = client.post("/api/v1/saas/crm/payments", json={
                "invoice_id": invoice_id,
                "amount_minor": 6000,
                "currency": "USD",
            })
            assert overpayment.status_code == 422

            final_payment = client.post("/api/v1/saas/crm/payments", json={
                "invoice_id": invoice_id,
                "amount_minor": 5000,
                "currency": "USD",
            })
            assert final_payment.status_code == 201, final_payment.text
            assert final_payment.json()["invoice_status"] == "paid"

            invoices = client.get("/api/v1/saas/crm/invoices")
            invoice = next(item for item in invoices.json() if item["id"] == invoice_id)
            assert invoice["paid_minor"] == 11000
            assert invoice["outstanding_minor"] == 0
            assert invoice["status"] == "paid"
            assert invoice["account_name"] == "Finance Test Account"
            finance_overview = client.get("/api/v1/saas/crm/finance/overview")
            assert finance_overview.status_code == 200, finance_overview.text
            summary = finance_overview.json()
            assert summary["invoice_counts"]["paid"] >= 1
            assert summary["payment_count"] >= 2
            assert any(
                row["currency"] == "USD" and row["amount_minor"] >= 11000
                for row in summary["received_by_currency"]
            )
            assert client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"amount_minor": 1}).status_code == 422
            assert client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"status": "draft"}).status_code == 422
            payments = client.get("/api/v1/saas/crm/payments").json()
            assert all(p["invoice_number"] == f"INV-{suffix}" and p["account_name"] == "Finance Test Account" for p in payments)

            cannot_void_paid = client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"status": "void"})
            assert cannot_void_paid.status_code == 422

            reverse_first = client.patch(
                f"/api/v1/saas/crm/payments/{first_payment.json()['id']}",
                json={"status": "reversed"},
            )
            assert reverse_first.status_code == 200, reverse_first.text
            assert reverse_first.json()["invoice_status"] == "partially_paid"
            assert client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"amount_minor": 3000}).status_code == 422
            assert client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"amount_minor": 4000}).status_code == 200
            assert client.patch(f"/api/v1/saas/crm/payments/{first_payment.json()['id']}", json={"status": "received"}).status_code == 422

            reverse_final = client.patch(
                f"/api/v1/saas/crm/payments/{final_payment.json()['id']}",
                json={"status": "reversed"},
            )
            assert reverse_final.status_code == 200, reverse_final.text
            assert reverse_final.json()["invoice_status"] == "issued"

            can_void_after_reversal = client.patch(f"/api/v1/saas/crm/invoices/{invoice_id}", json={"status": "void"})
            assert can_void_after_reversal.status_code == 200, can_void_after_reversal.text
            assert can_void_after_reversal.json()["status"] == "void"
            assert client.patch(f"/api/v1/saas/crm/payments/{first_payment.json()['id']}", json={"status": "received"}).status_code == 422
    finally:
        asyncio.run(_cleanup_finance(email, account_slug))


def test_renewal_task_generation_is_deduplicated():
    suffix = uuid4().hex[:8]
    email = f"renewal-test-{suffix}@example.com"
    account_slug = f"renewal-account-{suffix}"
    asyncio.run(_create_ops_user(email))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": email,
                "password": PASSWORD,
            })
            assert login.status_code == 200, login.text

            account_response = client.post("/api/v1/saas/crm/accounts", json={
                "name": "Renewal Test Account",
                "slug": account_slug,
                "account_type": "client",
                "lifecycle_stage": "customer",
            })
            assert account_response.status_code == 201, account_response.text
            account_id = account_response.json()["id"]

            renews_at = datetime.now(UTC) + timedelta(days=100)
            subscription = client.post("/api/v1/saas/crm/subscriptions", json={
                "account_id": account_id,
                "status": "active",
                "billing_cycle": "annual",
                "currency": "USD",
                "seats": 25,
                "list_price_minor": 120000,
                "discount_minor": 0,
                "net_price_minor": 1,
                "renews_at": renews_at.isoformat(),
            })
            assert subscription.status_code == 201, subscription.text

            first = client.post("/api/v1/saas/crm/tasks/generate-renewals?horizon_days=120")
            assert first.status_code == 200, first.text
            assert first.json()["created"] == 3

            tasks = client.get(f"/api/v1/saas/crm/tasks?account_id={account_id}&task_type=renewal")
            assert tasks.status_code == 200, tasks.text
            assert len(tasks.json()) == 3
            assert {task["priority"] for task in tasks.json()} == {"normal", "high", "urgent"}
            task_page = client.get("/api/v1/saas/crm/page/tasks", params={
                "account_id": account_id, "task_type": "renewal", "limit": 2,
            })
            assert task_page.status_code == 200, task_page.text
            assert task_page.json()["total"] == 3
            assert task_page.json()["counts"]["open"] == 3
            assert len(task_page.json()["items"]) == 2
            next_page = client.get("/api/v1/saas/crm/page/tasks", params={
                "account_id": account_id, "task_type": "renewal", "limit": 2, "offset": 2,
            })
            assert next_page.status_code == 200 and len(next_page.json()["items"]) == 1
            completed_page = client.get("/api/v1/saas/crm/page/tasks", params={
                "account_id": account_id, "task_type": "renewal", "status": "completed",
            })
            assert completed_page.status_code == 200 and completed_page.json()["total"] == 0

            second = client.post("/api/v1/saas/crm/tasks/generate-renewals?horizon_days=120")
            assert second.status_code == 200, second.text
            assert second.json()["created"] == 0
            assert second.json()["skipped"] >= 3
            later = renews_at + timedelta(days=10)
            updated_subscription = client.patch(
                f"/api/v1/saas/crm/subscriptions/{subscription.json()['id']}",
                json={"renews_at": later.isoformat()},
            )
            assert updated_subscription.status_code == 200, updated_subscription.text
            refreshed = client.post("/api/v1/saas/crm/tasks/generate-renewals?horizon_days=120")
            assert refreshed.status_code == 200 and refreshed.json()["updated"] == 3
            tasks = client.get(f"/api/v1/saas/crm/tasks?account_id={account_id}&task_type=renewal").json()
            assert all("renewal date " + later.date().isoformat() in task["description"] for task in tasks)
    finally:
        asyncio.run(_cleanup_finance(email, account_slug))


def test_plan_offer_subscription_and_trial_guards():
    suffix = uuid4().hex[:8]
    email = f"terms-test-{suffix}@example.com"
    developer_email = f"terms-developer-{suffix}@example.com"
    code = f"terms-plan-{suffix}"
    slug = f"terms-account-{suffix}"
    offer_code = f"terms-offer-{suffix}"
    asyncio.run(_create_ops_user(email, "Sales Operations"))
    asyncio.run(_create_ops_user(developer_email, "Platform Developer"))
    demo_tenant_id = str(asyncio.run(_tenant_id("demo-corporation")))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG, "email": email, "password": PASSWORD,
            })
            assert login.status_code == 200, login.text
            plan = client.post("/api/v1/saas/crm/plans", json={
                "code": code, "name": "Terms Test Plan", "currency": "USD",
                "minimum_seats": 10, "maximum_seats": 100, "trial_days": 14,
                "status": "active", "monthly_price_minor": 10000,
            })
            assert plan.status_code == 201, plan.text
            plan_id = plan.json()["id"]
            account = client.post("/api/v1/saas/crm/accounts", json={
                "name": "Terms Test Account", "slug": slug,
                "lifecycle_stage": "qualified",
            })
            assert account.status_code == 201, account.text
            account_id = account.json()["id"]
            assert client.post("/api/v1/saas/crm/accounts", json={
                "name": "Bad tenant link", "slug": f"bad-{slug}",
                "managed_tenant_id": demo_tenant_id,
            }).status_code == 422
            assert client.patch(f"/api/v1/saas/crm/accounts/{account_id}", json={
                "managed_tenant_id": demo_tenant_id,
            }).status_code == 422
            assert client.patch(f"/api/v1/saas/crm/tenants/{demo_tenant_id}", json={
                "status": "inactive",
            }).status_code == 403
            invalid_bounds = client.patch(f"/api/v1/saas/crm/plans/{plan_id}", json={"maximum_seats": 5})
            assert invalid_bounds.status_code == 422
            base = {
                "account_id": account_id, "plan_id": plan_id, "status": "active",
                "billing_cycle": "monthly", "currency": "USD", "seats": 20,
                "list_price_minor": 10000, "discount_minor": 0,
            }
            assert client.post("/api/v1/saas/crm/subscriptions", json={**base, "currency": "PKR"}).status_code == 422
            assert client.post("/api/v1/saas/crm/subscriptions", json={**base, "seats": 5}).status_code == 422
            assert client.post("/api/v1/saas/crm/subscriptions", json={
                **base, "managed_tenant_id": str(uuid4()),
            }).status_code == 422
            offer = client.post("/api/v1/saas/crm/offers", json={
                "code": offer_code, "title": "Twenty percent", "plan_id": plan_id,
                "discount_type": "percent", "discount_value": 20,
                "status": "active",
            })
            assert offer.status_code == 201, offer.text
            subscription = client.post("/api/v1/saas/crm/subscriptions", json={
                **base, "offer_id": offer.json()["id"],
            })
            assert subscription.status_code == 201, subscription.text
            page = client.get("/api/v1/saas/crm/page/subscriptions", params={
                "account_id": account_id, "status": "active", "limit": 1,
            })
            assert page.status_code == 200 and page.json()["total"] == 1
            assert page.json()["items"][0]["id"] == subscription.json()["id"]
            next_page = client.get("/api/v1/saas/crm/page/subscriptions", params={
                "account_id": account_id, "status": "active", "limit": 1, "offset": 1,
            })
            assert next_page.status_code == 200 and next_page.json()["items"] == []
            subscriptions = client.get("/api/v1/saas/crm/subscriptions").json()
            item = next(x for x in subscriptions if x["id"] == subscription.json()["id"])
            assert item["discount_minor"] == 2000 and item["net_price_minor"] == 8000
            assert client.patch(f"/api/v1/saas/crm/subscriptions/{item['id']}", json={
                "discount_minor": 1,
            }).status_code == 422
            assert client.post("/api/v1/saas/crm/trials", json={
                "account_id": account_id, "plan_id": plan_id,
                "seats": 20, "status": "active",
            }).status_code == 422
            scheduled = client.post("/api/v1/saas/crm/trials", json={
                "account_id": account_id, "plan_id": plan_id,
                "seats": 20, "status": "scheduled",
            })
            assert scheduled.status_code == 201, scheduled.text
            assert client.patch(f"/api/v1/saas/crm/trials/{scheduled.json()['id']}", json={
                "status": "active",
            }).status_code == 422
            # Sales Operations can manage the CRM opportunity/account but
            # cannot provision or suspend a customer workspace.
            denied_provision = client.post(
                f"/api/v1/saas/crm/accounts/{account_id}/provision-tenant", json={}
            )
            assert denied_provision.status_code == 403

            developer_login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": developer_email,
                "password": PASSWORD,
            })
            assert developer_login.status_code == 200, developer_login.text
            developer_profile = client.get("/api/v1/auth/me").json()
            assert [role["name"] for role in developer_profile["roles"]] == ["Platform Developer"]
            assert "platform.tenants.manage" in developer_profile["permissions"]
            assert "saas.crm.manage" not in developer_profile["permissions"]
            provisioned = client.post(
                f"/api/v1/saas/crm/accounts/{account_id}/provision-tenant", json={}
            )
            assert provisioned.status_code == 201, provisioned.text
            tenant_id = provisioned.json()["id"]
            # The Developer can operate tenants, not the commercial CRM register.
            assert client.get("/api/v1/saas/crm/tenants").status_code == 403
            assert client.get(f"/api/v1/saas/crm/tenants/{tenant_id}/users").status_code == 200

            # Tenant suspension is a platform operation; reactivation restores
            # login eligibility without reviving revoked sessions.
            suspended = client.patch(
                f"/api/v1/saas/crm/tenants/{tenant_id}", json={"status": "suspended"}
            )
            assert suspended.status_code == 200, suspended.text
            assert suspended.json()["status"] == "suspended"
            assert client.patch(
                f"/api/v1/saas/crm/tenants/{tenant_id}", json={"status": "active"}
            ).status_code == 200

            sales_login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": email,
                "password": PASSWORD,
            })
            assert sales_login.status_code == 200
            linked = client.get("/api/v1/saas/crm/tenants")
            assert linked.status_code == 200
            assert any(row["crm_account_id"] == account_id for row in linked.json())
            started = datetime.now(UTC) - timedelta(days=1)
            ends = started + timedelta(days=14)
            active = client.patch(f"/api/v1/saas/crm/trials/{scheduled.json()['id']}", json={
                "status": "active", "starts_at": started.isoformat(), "ends_at": ends.isoformat(),
            })
            assert active.status_code == 200, active.text
    finally:
        asyncio.run(_cleanup(email, code, slug, offer_code, slug))
        asyncio.run(_cleanup(developer_email, code))



async def _seed_cross_tenant_finance_rows(suffix: str) -> tuple[str, str, str, str]:
    async with SessionLocal() as db:
        ops_tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        assert ops_tenant is not None
        foreign_tenant = Tenant(
            name=f"Finance Isolation {suffix}",
            slug=f"finance-isolation-{suffix}",
            status="active",
        )
        db.add(foreign_tenant)
        await db.flush()

        account = CRMAccount(
            ops_tenant_id=foreign_tenant.id,
            name=f"Foreign Finance Account {suffix}",
            slug=f"foreign-finance-{suffix}",
            account_type="client",
            lifecycle_stage="customer",
        )
        db.add(account)
        await db.flush()

        contract_reference = f"FOREIGN-CON-{suffix}"
        invoice_number = f"FOREIGN-INV-{suffix}"
        contract = CRMContract(
            ops_tenant_id=ops_tenant.id,
            account_id=account.id,
            reference=contract_reference,
            status="active",
            currency="USD",
            total_value_minor=100,
        )
        invoice = CRMInvoice(
            ops_tenant_id=ops_tenant.id,
            account_id=account.id,
            invoice_number=invoice_number,
            status="issued",
            currency="USD",
            amount_minor=100,
            total_minor=100,
        )
        db.add_all([contract, invoice])
        await db.flush()
        db.add(CRMPayment(
            ops_tenant_id=ops_tenant.id,
            account_id=account.id,
            invoice_id=invoice.id,
            amount_minor=25,
            currency="USD",
            status="received",
            reference=f"FOREIGN-PAY-{suffix}",
        ))
        await db.commit()
        return foreign_tenant.slug, str(account.id), contract_reference, invoice_number


async def _delete_cross_tenant_finance_tenant(slug: str) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Tenant).where(Tenant.slug == slug))
        await db.commit()


def test_finance_read_models_exclude_cross_tenant_relationships():
    suffix = uuid4().hex[:8]
    email = f"finance-isolation-{suffix}@example.com"
    foreign_slug = None
    try:
        asyncio.run(_create_ops_user(email))
        foreign_slug, account_id, contract_reference, invoice_number = asyncio.run(
            _seed_cross_tenant_finance_rows(suffix)
        )
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": OPS_SLUG,
                "email": email,
                "password": PASSWORD,
            })
            assert login.status_code == 200, login.text

            contracts = client.get("/api/v1/saas/crm/contracts")
            assert contracts.status_code == 200, contracts.text
            assert all(row["reference"] != contract_reference for row in contracts.json())

            contract_page = client.get(
                "/api/v1/saas/crm/page/contracts",
                params={"account_id": account_id},
            )
            assert contract_page.status_code == 200, contract_page.text
            assert contract_page.json()["total"] == 0
            assert contract_page.json()["items"] == []

            invoices = client.get("/api/v1/saas/crm/invoices")
            assert invoices.status_code == 200, invoices.text
            assert all(row["invoice_number"] != invoice_number for row in invoices.json())

            invoice_page = client.get(
                "/api/v1/saas/crm/page/invoices",
                params={"account_id": account_id},
            )
            assert invoice_page.status_code == 200, invoice_page.text
            assert invoice_page.json()["total"] == 0
            assert invoice_page.json()["items"] == []

            payments = client.get(
                "/api/v1/saas/crm/payments",
                params={"account_id": account_id},
            )
            assert payments.status_code == 200, payments.text
            assert all(row["reference"] != f"FOREIGN-PAY-{suffix}" for row in payments.json())

            payment_page = client.get(
                "/api/v1/saas/crm/page/payments",
                params={"account_id": account_id},
            )
            assert payment_page.status_code == 200, payment_page.text
            assert payment_page.json()["total"] == 0
            assert payment_page.json()["items"] == []
    finally:
        if foreign_slug is not None:
            asyncio.run(_delete_cross_tenant_finance_tenant(foreign_slug))
        asyncio.run(_cleanup(email, f"unused-plan-{suffix}"))
