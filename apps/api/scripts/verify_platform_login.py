import asyncio
import httpx
import os
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User, Tenant
from app.core.security import verify_password

TEMP = os.getenv("KALAM_DEVELOPER_VERIFY_PASSWORD")


async def main():
    if not TEMP:
        print(
            "LOGIN_CHECK=SKIPPED (set KALAM_DEVELOPER_VERIFY_PASSWORD in the process environment)"
        )
        return
    async with SessionLocal() as db:
        u = await db.scalar(
            select(User)
            .join(Tenant, Tenant.id == User.tenant_id)
            .where(User.email == "developer@kalam.global", Tenant.slug == "kalam")
        )
        print(
            "PASSWORD_HASH_MATCH="
            + str(bool(u and verify_password(TEMP, u.password_hash)))
        )
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=10) as c:
        r = await c.post(
            "/api/v1/auth/login",
            json={
                "tenant_slug": "kalam",
                "email": "developer@kalam.global",
                "password": TEMP,
            },
        )
        print("LOGIN_STATUS=" + str(r.status_code))
        print("LOGIN_BODY=" + r.text)


asyncio.run(main())
