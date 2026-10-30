import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.models import Course, Tenant, User
from app.db.session import SessionLocal
from app.main import app

PASSWORD = "Phase8Tenant!2026"


async def _seed_fixture() -> tuple[str, str, str, str, str, str, str]:
    suffix = uuid4().hex[:10]
    slug_a = f"phase8-a-{suffix}"
    slug_b = f"phase8-b-{suffix}"
    email_a = f"phase8-a-{suffix}@example.com"
    email_b = f"phase8-b-{suffix}@example.com"
    async with SessionLocal() as db:
        tenant_a = Tenant(name="Phase 8 Tenant A", slug=slug_a, status="active")
        tenant_b = Tenant(name="Phase 8 Tenant B", slug=slug_b, status="active")
        db.add_all([tenant_a, tenant_b])
        await db.flush()
        db.add_all([
            User(tenant_id=tenant_a.id, email=email_a, password_hash=hash_password(PASSWORD),
                 first_name="Tenant", last_name="A", is_active=True),
            User(tenant_id=tenant_b.id, email=email_b, password_hash=hash_password(PASSWORD),
                 first_name="Tenant", last_name="B", is_active=True),
            Course(tenant_id=tenant_a.id, title="Tenant A Published Course",
                   slug=f"phase8-course-{suffix}", status="published", visibility="tenant",
                   enrollment_policy="open", tags=[], prerequisites=[],
                   audience_org_units=[], record_metadata={}),
        ])
        await db.commit()
        course = await db.scalar(select(Course).where(Course.tenant_id == tenant_a.id))
        assert course is not None
        return slug_a, email_a, slug_b, email_b, str(course.id), str(tenant_a.id), str(tenant_b.id)


async def _delete_tenant(tenant_id: str) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


def test_course_detail_cannot_cross_tenant_boundary() -> None:
    slug_a, email_a, slug_b, email_b, course_id, tenant_a_id, tenant_b_id = asyncio.run(_seed_fixture())
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            own_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_a, "email": email_a, "password": PASSWORD},
            )
            assert own_login.status_code == 200, own_login.text
            own = client.get(f"/api/v1/courses/{course_id}")
            assert own.status_code == 200, own.text
            assert own.json()["id"] == course_id

            client.post("/api/v1/auth/logout")
            other_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_b, "email": email_b, "password": PASSWORD},
            )
            assert other_login.status_code == 200, other_login.text
            cross = client.get(f"/api/v1/courses/{course_id}")
            assert cross.status_code == 404, cross.text
    finally:
        asyncio.run(_delete_tenant(tenant_a_id))
        asyncio.run(_delete_tenant(tenant_b_id))
