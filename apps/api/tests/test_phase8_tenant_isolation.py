import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.models import (
    Course,
    FileObject,
    Integration,
    Permission,
    Role,
    RolePermission,
    SavedReport,
    Tenant,
    User,
    UserRole,
    WebhookEndpoint,
)
from app.db.session import SessionLocal
from app.main import app
from app.services.storage import get_storage


PASSWORD = "Phase8Tenant!2026"


async def _seed_fixture() -> tuple[str, str, str, str, str, str]:
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


async def _seed_file_fixture() -> tuple[str, str, str, str, str, str, str, str]:
    suffix = uuid4().hex[:10]
    slug_a = f"phase8-file-a-{suffix}"
    slug_b = f"phase8-file-b-{suffix}"
    email_a = f"phase8-file-a-{suffix}@example.com"
    email_b = f"phase8-file-b-{suffix}@example.com"
    object_key = ""
    async with SessionLocal() as db:
        tenant_a = Tenant(name="Phase 8 File Tenant A", slug=slug_a, status="active")
        tenant_b = Tenant(name="Phase 8 File Tenant B", slug=slug_b, status="active")
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        permissions = {}
        for key in ("files.read", "files.manage"):
            permission = await db.scalar(select(Permission).where(Permission.key == key))
            assert permission is not None, f"required permission missing: {key}"
            permissions[key] = permission

        role_a = Role(tenant_id=tenant_a.id, name=f"File Tester A {suffix}")
        role_b = Role(tenant_id=tenant_b.id, name=f"File Tester B {suffix}")
        user_a = User(
            tenant_id=tenant_a.id,
            email=email_a,
            password_hash=hash_password(PASSWORD),
            first_name="File",
            last_name="A",
            is_active=True,
        )
        user_b = User(
            tenant_id=tenant_b.id,
            email=email_b,
            password_hash=hash_password(PASSWORD),
            first_name="File",
            last_name="B",
            is_active=True,
        )
        db.add_all([role_a, role_b, user_a, user_b])
        await db.flush()
        db.add_all([
            UserRole(user_id=user_a.id, role_id=role_a.id),
            UserRole(user_id=user_b.id, role_id=role_b.id),
            RolePermission(role_id=role_a.id, permission_id=permissions["files.read"].id),
            RolePermission(role_id=role_a.id, permission_id=permissions["files.manage"].id),
            RolePermission(role_id=role_b.id, permission_id=permissions["files.read"].id),
            RolePermission(role_id=role_b.id, permission_id=permissions["files.manage"].id),
        ])
        object_key = f"{tenant_a.id}/phase8-{suffix}.txt"
        item = FileObject(
            tenant_id=tenant_a.id,
            uploaded_by=user_a.id,
            object_key=object_key,
            original_name="tenant-a.txt",
            mime_type="text/plain",
            size_bytes=11,
            status="available",
            record_metadata={"scanner": "test", "scan_result": "clean"},
        )
        db.add(item)
        await db.commit()
        return slug_a, email_a, slug_b, email_b, str(item.id), str(tenant_a.id), str(tenant_b.id), object_key


def test_file_access_cannot_cross_tenant_boundary() -> None:
    (
        slug_a,
        email_a,
        slug_b,
        email_b,
        file_id,
        tenant_a_id,
        tenant_b_id,
        object_key,
    ) = asyncio.run(_seed_file_fixture())
    path = get_storage().path_for(object_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"tenant-a-data")
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            own_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_a, "email": email_a, "password": PASSWORD},
            )
            assert own_login.status_code == 200, own_login.text
            own_list = client.get("/api/v1/files")
            assert own_list.status_code == 200, own_list.text
            assert any(item["id"] == file_id for item in own_list.json())
            own_download = client.get(f"/api/v1/files/{file_id}/download")
            assert own_download.status_code == 200, own_download.text
            assert own_download.content == b"tenant-a-data"

            client.post("/api/v1/auth/logout")
            other_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_b, "email": email_b, "password": PASSWORD},
            )
            assert other_login.status_code == 200, other_login.text
            cross_list = client.get("/api/v1/files")
            assert cross_list.status_code == 200, cross_list.text
            assert all(item["id"] != file_id for item in cross_list.json())
            cross_download = client.get(f"/api/v1/files/{file_id}/download")
            assert cross_download.status_code == 404, cross_download.text
            cross_scan = client.patch(f"/api/v1/files/{file_id}/scan-result?clean=true")
            assert cross_scan.status_code == 404, cross_scan.text
    finally:
        path.unlink(missing_ok=True)
        asyncio.run(_delete_tenant(tenant_a_id))
        asyncio.run(_delete_tenant(tenant_b_id))


async def _seed_sensitive_fixture() -> tuple[str, str, str, str, str, str, str, str, str]:
    suffix = uuid4().hex[:10]
    slug_a = f"phase8-sensitive-a-{suffix}"
    slug_b = f"phase8-sensitive-b-{suffix}"
    email_a = f"phase8-sensitive-a-{suffix}@example.com"
    email_b = f"phase8-sensitive-b-{suffix}@example.com"
    async with SessionLocal() as db:
        tenant_a = Tenant(name="Phase 8 Sensitive Tenant A", slug=slug_a, status="active")
        tenant_b = Tenant(name="Phase 8 Sensitive Tenant B", slug=slug_b, status="active")
        db.add_all([tenant_a, tenant_b])
        await db.flush()
        role_a = Role(tenant_id=tenant_a.id, name=f"Phase8 Integrations A {suffix}")
        role_b = Role(tenant_id=tenant_b.id, name=f"Phase8 Integrations B {suffix}")
        user_a = User(tenant_id=tenant_a.id, email=email_a, password_hash=hash_password(PASSWORD),
                      first_name="Sensitive", last_name="A", is_active=True)
        user_b = User(tenant_id=tenant_b.id, email=email_b, password_hash=hash_password(PASSWORD),
                      first_name="Sensitive", last_name="B", is_active=True)
        db.add_all([role_a, role_b, user_a, user_b])
        await db.flush()
        integration_permission = await db.scalar(select(Permission).where(Permission.key == "integrations.manage"))
        report_permission = await db.scalar(select(Permission).where(Permission.key == "reports.read"))
        assert integration_permission is not None
        assert report_permission is not None
        db.add_all([
            RolePermission(role_id=role_a.id, permission_id=integration_permission.id),
            RolePermission(role_id=role_a.id, permission_id=report_permission.id),
            RolePermission(role_id=role_b.id, permission_id=integration_permission.id),
            RolePermission(role_id=role_b.id, permission_id=report_permission.id),
            UserRole(user_id=user_a.id, role_id=role_a.id),
            UserRole(user_id=user_b.id, role_id=role_b.id),
            Integration(tenant_id=tenant_a.id, provider="email", status="configured", config={"host": "tenant-a.example"}),
            WebhookEndpoint(tenant_id=tenant_a.id, url="https://tenant-a.example/webhook",
                            secret_encrypted="encrypted-test-secret", secret_key_id="test-key",
                            event_types=["course.completed"], active=True),
        ])
        report = SavedReport(
            tenant_id=tenant_a.id, owner_id=user_a.id, name=f"Tenant A Report {suffix}",
            report_type="executive_summary", definition={}, visibility="private", enabled=True,
        )
        db.add(report)
        await db.flush()
        await db.commit()
        integration = await db.scalar(select(Integration).where(Integration.tenant_id == tenant_a.id))
        webhook = await db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.tenant_id == tenant_a.id))
        assert integration is not None and webhook is not None
        return (
            slug_a, email_a, slug_b, email_b, str(tenant_a.id), str(tenant_b.id),
            str(integration.id), str(webhook.id), str(report.id),
        )


def test_sensitive_resources_cannot_cross_tenant_boundary() -> None:
    (
        slug_a, email_a, slug_b, email_b, tenant_a_id, tenant_b_id,
        integration_id, webhook_id, report_id,
    ) = asyncio.run(_seed_sensitive_fixture())
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            own_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_a, "email": email_a, "password": PASSWORD},
            )
            assert own_login.status_code == 200, own_login.text
            own_integrations = client.get("/api/v1/integrations")
            assert own_integrations.status_code == 200, own_integrations.text
            assert any(item["id"] == integration_id for item in own_integrations.json())

            client.post("/api/v1/auth/logout")
            other_login = client.post(
                "/api/v1/auth/login",
                json={"tenant_slug": slug_b, "email": email_b, "password": PASSWORD},
            )
            assert other_login.status_code == 200, other_login.text
            assert all(item["id"] != integration_id for item in client.get("/api/v1/integrations").json())
            assert client.post("/api/v1/integrations/email/test").status_code == 404
            assert client.post(f"/api/v1/webhooks/{webhook_id}/rotate-secret").status_code == 404
            assert client.post(f"/api/v1/reports/saved/{report_id}/run").status_code == 404
    finally:
        asyncio.run(_delete_tenant(tenant_a_id))
        asyncio.run(_delete_tenant(tenant_b_id))
