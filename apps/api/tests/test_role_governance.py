from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.models import (
    Permission,
    Role,
    RolePermission,
    SessionRecord,
    Tenant,
    User,
    UserRole,
)
from app.db.session import SessionLocal
from app.main import app

OPS_SLUG = "kalam"
TEST_PASSWORD = "RoleGovernance!2026"


async def _create_role_user(email: str, role_name: str) -> None:
    role_permissions = {
        "SaaS Owner": ["saas.crm.read"],
        "Sales Viewer": ["saas.crm.read"],
        "Sales Operations": ["saas.crm.read", "saas.crm.manage"],
        "Platform Developer": [
            "platform.tenants.read",
            "platform.tenants.manage",
            "platform.health.read",
            "platform.incidents.manage",
            "platform.support.access",
            "platform.audit.read",
        ],
    }
    if role_name not in role_permissions:
        raise ValueError(f"Unsupported role fixture: {role_name}")

    descriptions = {
        key: key.replace(".", " ").replace("_", " ").capitalize()
        for keys in role_permissions.values()
        for key in keys
    }
    async with SessionLocal() as db:
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

        permissions: dict[str, Permission] = {}
        for key, description in descriptions.items():
            item = await db.scalar(select(Permission).where(Permission.key == key))
            if item is None:
                item = Permission(key=key, description=description)
                db.add(item)
                await db.flush()
            permissions[key] = item

        roles: dict[str, Role] = {}
        for name, keys in role_permissions.items():
            role = await db.scalar(
                select(Role).where(Role.tenant_id == tenant.id, Role.name == name)
            )
            if role is None:
                role = Role(
                    tenant_id=tenant.id,
                    name=name,
                    description=f"Role governance test: {name}",
                    role_kind="platform",
                )
                db.add(role)
                await db.flush()
            roles[name] = role
            for key in keys:
                existing = await db.scalar(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permissions[key].id,
                    )
                )
                if existing is None:
                    db.add(RolePermission(
                        role_id=role.id,
                        permission_id=permissions[key].id,
                    ))

        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            first_name="Role",
            last_name="Governance",
            job_title=role_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=roles[role_name].id))
        await db.commit()


async def _delete_role_user(email: str) -> None:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            return
        await db.execute(delete(SessionRecord).where(SessionRecord.user_id == user.id))
        await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()


def _login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": OPS_SLUG, "email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text


def test_saas_owner_is_read_only_and_cannot_enter_platform_operations() -> None:
    email = f"owner-{uuid4().hex[:10]}@example.com"
    asyncio.run(_create_role_user(email, "SaaS Owner"))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            _login(client, email)
            profile = client.get("/api/v1/auth/me")
            assert profile.status_code == 200
            assert [role["name"] for role in profile.json()["roles"]] == ["SaaS Owner"]
            assert profile.json()["permissions"] == ["saas.crm.read"]

            read_access = client.get("/api/v1/saas/crm/plans")
            assert read_access.status_code == 200, read_access.text
            assert client.get("/api/v1/support/developer/health").status_code == 403
            assert client.get("/api/v1/support/developer/audit").status_code == 403
            assert client.get("/api/v1/support/developer/incidents").status_code == 403

            write_access = client.post(
                "/api/v1/saas/crm/plans",
                json={
                    "code": f"owner-test-{uuid4().hex[:8]}",
                    "name": "Owner must not publish",
                    "currency": "USD",
                    "minimum_seats": 1,
                    "trial_days": 0,
                    "status": "draft",
                    "public_visible": False,
                },
            )
            assert write_access.status_code == 403, write_access.text
            assert client.get("/api/v1/support/developer/tenants").status_code == 403
    finally:
        asyncio.run(_delete_role_user(email))


def test_platform_developer_has_platform_permissions_but_no_commercial_crm() -> None:
    email = f"developer-{uuid4().hex[:10]}@example.com"
    asyncio.run(_create_role_user(email, "Platform Developer"))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            _login(client, email)
            profile = client.get("/api/v1/auth/me")
            assert profile.status_code == 200
            roles = [role["name"] for role in profile.json()["roles"]]
            permissions = set(profile.json()["permissions"])
            assert roles == ["Platform Developer"]
            assert "platform.tenants.read" in permissions
            assert "platform.tenants.manage" in permissions
            assert "saas.crm.read" not in permissions
            assert "saas.crm.manage" not in permissions

            tenants = client.get("/api/v1/support/developer/tenants")
            assert tenants.status_code == 200, tenants.text
            health = client.get("/api/v1/support/developer/health")
            assert health.status_code == 200, health.text
            assert set(health.json()["checks"]) == {"database", "redis"}
            assert health.json()["status"] in {"ready", "degraded"}
            platform_audit = client.get("/api/v1/support/developer/audit?limit=10")
            assert platform_audit.status_code == 200, platform_audit.text
            assert isinstance(platform_audit.json(), list)
            incident = client.post(
                "/api/v1/support/developer/incidents",
                json={
                    "title": "Role governance regression incident",
                    "description": "Validate platform incident creation and audited lifecycle updates.",
                    "severity": "sev3",
                    "impact": "Automated test only",
                },
            )
            assert incident.status_code == 201, incident.text
            incident_id = incident.json()["id"]
            assert incident.json()["status"] == "open"
            transition = client.patch(
                f"/api/v1/support/developer/incidents/{incident_id}",
                json={"status": "investigating", "severity": "sev2"},
            )
            assert transition.status_code == 200, transition.text
            assert transition.json()["status"] == "investigating"
            assert transition.json()["severity"] == "sev2"
            incident_list = client.get("/api/v1/support/developer/incidents?limit=10")
            assert incident_list.status_code == 200, incident_list.text
            assert any(row["id"] == incident_id for row in incident_list.json())
            crm = client.get("/api/v1/saas/crm/plans")
            assert crm.status_code == 403, crm.text
    finally:
        asyncio.run(_delete_role_user(email))


def test_sales_viewer_is_read_only_and_cannot_enter_platform_operations() -> None:
    email = f"sales-viewer-{uuid4().hex[:10]}@example.com"
    asyncio.run(_create_role_user(email, "Sales Viewer"))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            _login(client, email)
            profile = client.get("/api/v1/auth/me")
            assert profile.status_code == 200
            assert [role["name"] for role in profile.json()["roles"]] == ["Sales Viewer"]
            assert profile.json()["permissions"] == ["saas.crm.read"]
            assert client.get("/api/v1/saas/crm/plans").status_code == 200
            denied = client.post(
                "/api/v1/saas/crm/plans",
                json={
                    "code": f"viewer-test-{uuid4().hex[:8]}",
                    "name": "Viewer must not publish",
                    "currency": "USD",
                    "minimum_seats": 1,
                    "trial_days": 0,
                    "status": "draft",
                    "public_visible": False,
                },
            )
            assert denied.status_code == 403
            assert client.get("/api/v1/support/developer/tenants").status_code == 403
    finally:
        asyncio.run(_delete_role_user(email))


def test_unscoped_hrbp_and_regional_templates_do_not_grant_tenant_wide_access() -> None:
    from app.api.routes.saas_commercial import PREDEFINED_TENANT_ROLES

    sensitive_permissions = {
        "users.read",
        "users.manage",
        "reports.read",
        "capability_gaps.read",
        "capability_risk.read",
    }
    assert PREDEFINED_TENANT_ROLES["HR Business Partner"] == [
        "courses.read", "learning.access", "development.manage"
    ]
    assert PREDEFINED_TENANT_ROLES["Regional Executive"] == [
        "tenant.read", "courses.read", "learning.access"
    ]
    for role_name in ("HR Business Partner", "Regional Executive"):
        assert not (set(PREDEFINED_TENANT_ROLES[role_name]) & sensitive_permissions)


def test_sales_operations_can_manage_crm_without_platform_access() -> None:
    suffix = uuid4().hex[:8]
    email = f"sales-ops-{suffix}@example.com"
    plan_code = f"sales-ops-{suffix}"
    asyncio.run(_create_role_user(email, "Sales Operations"))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            _login(client, email)
            profile = client.get("/api/v1/auth/me")
            assert profile.status_code == 200
            permissions = set(profile.json()["permissions"])
            assert permissions == {"saas.crm.read", "saas.crm.manage"}

            read_access = client.get("/api/v1/saas/crm/plans")
            assert read_access.status_code == 200, read_access.text
            create_access = client.post(
                "/api/v1/saas/crm/plans",
                json={
                    "code": plan_code,
                    "name": "Sales Operations QA Plan",
                    "billing_model": "per_user",
                    "currency": "USD",
                    "monthly_price_minor": 2500,
                    "annual_price_minor": 25000,
                    "trial_days": 14,
                    "minimum_seats": 10,
                    "features": ["QA-only feature"],
                    "status": "draft",
                    "public_visible": False,
                },
            )
            assert create_access.status_code == 201, create_access.text

            assert client.get("/api/v1/support/developer/tenants").status_code == 403
            assert client.get("/api/v1/support/developer/health").status_code == 403
            assert client.get("/api/v1/support/developer/audit").status_code == 403
            assert client.get("/api/v1/support/developer/incidents").status_code == 403
    finally:
        asyncio.run(_delete_role_user(email))
