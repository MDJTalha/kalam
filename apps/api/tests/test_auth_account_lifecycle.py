import asyncio
from datetime import timedelta
from secrets import token_urlsafe
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password, session_token_hash, utcnow
from app.db.models import Invitation, Role, Tenant, User
from app.db.session import SessionLocal
from app.main import app


PASSWORD = "AuthRegression!2026"


async def _create_tenant_user() -> tuple[str, str, str]:
    suffix = uuid4().hex[:10]
    slug = f"auth-regression-{suffix}"
    email = f"auth-regression-{suffix}@example.com"
    async with SessionLocal() as db:
        tenant = Tenant(name="Auth Regression Tenant", slug=slug, status="active")
        db.add(tenant)
        await db.flush()
        db.add(User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(PASSWORD),
            first_name="Auth",
            last_name="Regression",
            is_active=True,
        ))
        await db.commit()
    return slug, email, str(tenant.id)


async def _set_tenant_status(tenant_id: str, status: str) -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
        assert tenant is not None
        tenant.status = status
        await db.commit()


async def _delete_tenant(tenant_id: str) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


def test_existing_session_is_rejected_after_tenant_deactivation():
    slug, email, tenant_id = asyncio.run(_create_tenant_user())
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            login = client.post("/api/v1/auth/login", json={
                "tenant_slug": slug,
                "email": email,
                "password": PASSWORD,
            })
            assert login.status_code == 200, login.text
            assert client.get("/api/v1/auth/me").status_code == 200

            asyncio.run(_set_tenant_status(tenant_id, "inactive"))

            assert client.get("/api/v1/auth/me").status_code == 401
    finally:
        asyncio.run(_delete_tenant(tenant_id))


def test_invitation_acceptance_rejects_inactive_or_mismatched_role_tenants():
    suffix = uuid4().hex[:10]
    tenant_a_id = None
    tenant_b_id = None
    token_mismatch = token_urlsafe(36)
    token_inactive = token_urlsafe(36)
    async def seed() -> tuple[str, str]:
        nonlocal tenant_a_id, tenant_b_id
        async with SessionLocal() as db:
            tenant_a = Tenant(name="Invitation Tenant A", slug=f"invite-a-{suffix}", status="active")
            tenant_b = Tenant(name="Invitation Tenant B", slug=f"invite-b-{suffix}", status="active")
            db.add_all([tenant_a, tenant_b])
            await db.flush()
            role_a = Role(tenant_id=tenant_a.id, name=f"Invite Role A {suffix}")
            role_b = Role(tenant_id=tenant_b.id, name=f"Invite Role B {suffix}")
            db.add_all([role_a, role_b])
            await db.flush()
            db.add_all([
                Invitation(
                    tenant_id=tenant_a.id,
                    email=f"mismatch-{suffix}@example.com",
                    role_id=role_b.id,
                    token_hash=session_token_hash(token_mismatch),
                    expires_at=utcnow() + timedelta(days=1),
                ),
                Invitation(
                    tenant_id=tenant_a.id,
                    email=f"inactive-{suffix}@example.com",
                    role_id=role_a.id,
                    token_hash=session_token_hash(token_inactive),
                    expires_at=utcnow() + timedelta(days=1),
                ),
            ])
            tenant_a_id, tenant_b_id = str(tenant_a.id), str(tenant_b.id)
            await db.commit()
        return tenant_a_id, tenant_b_id

    tenant_a_id, tenant_b_id = asyncio.run(seed())
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            mismatch = client.post("/api/v1/auth/invitations/accept", json={
                "token": token_mismatch,
                "first_name": "Mismatch",
                "last_name": "Role",
                "password": PASSWORD,
            })
            assert mismatch.status_code == 400, mismatch.text

            asyncio.run(_set_tenant_status(tenant_a_id, "inactive"))
            inactive = client.post("/api/v1/auth/invitations/accept", json={
                "token": token_inactive,
                "first_name": "Inactive",
                "last_name": "Tenant",
                "password": PASSWORD,
            })
            assert inactive.status_code == 400, inactive.text
    finally:
        asyncio.run(_delete_tenant(tenant_a_id))
        asyncio.run(_delete_tenant(tenant_b_id))
