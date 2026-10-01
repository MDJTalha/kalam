import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Tenant, User, Role, Permission, RolePermission, UserRole

async def main():
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "demo-corporation"))
        user = await db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == "admin@demo.corp"))
        perms = (await db.execute(
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        )).all()
        print(sorted({row[0] for row in perms if row[0].startswith("saas.crm")}))

asyncio.run(main())
