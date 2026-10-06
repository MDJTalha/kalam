import asyncio
import os
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Tenant, User, Role, UserRole
from app.core.security import hash_password

EMAIL = "developer@kalam.global"
INITIAL_PASSWORD = os.getenv("KALAM_PLATFORM_DEVELOPER_INITIAL_PASSWORD")


async def main():
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "kalam"))
        role = (
            await db.scalar(
                select(Role).where(
                    Role.tenant_id == tenant.id, Role.name == "Platform Developer"
                )
            )
            if tenant
            else None
        )
        if not tenant or tenant.status != "active" or not role:
            raise RuntimeError("Required active Kalam tenant/Platform Developer role missing")
        role.role_kind = "platform"
        user = await db.scalar(
            select(User).where(User.tenant_id == tenant.id, User.email == EMAIL)
        )
        action = "role_repaired"
        if user is None:
            if not INITIAL_PASSWORD or len(INITIAL_PASSWORD) < 16:
                raise RuntimeError(
                    "Set KALAM_PLATFORM_DEVELOPER_INITIAL_PASSWORD (at least 16 characters) to create the developer account"
                )
            user = User(
                tenant_id=tenant.id,
                email=EMAIL,
                password_hash=hash_password(INITIAL_PASSWORD),
                first_name="Platform",
                last_name="Developer",
                job_title="Platform Developer",
                is_active=True,
            )
            db.add(user)
            await db.flush()
            action = "created"
        link = await db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id, UserRole.role_id == role.id
            )
        )
        if link is None:
            db.add(UserRole(user_id=user.id, role_id=role.id))
        await db.commit()
        print("ACTION=" + action)
        print("EMAIL=" + EMAIL)
        print("TENANT=kalam")
        print("USER_ID=" + str(user.id))


asyncio.run(main())
