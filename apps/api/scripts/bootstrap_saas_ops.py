# ruff: noqa: E402

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Permission, Role, RolePermission, Tenant, User, UserRole
from app.db.session import SessionLocal

OPS_SLUG = os.getenv("SAAS_OPS_TENANT_SLUG", "kalam")
OPS_NAME = os.getenv("SAAS_OPS_TENANT_NAME", "Kalam")
ADMIN_EMAIL = os.getenv("SAAS_OPS_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("SAAS_OPS_ADMIN_PASSWORD")

PERMISSIONS = [
    ("tenant.read", "View tenant"),
    ("tenant.manage", "Manage tenant"),
    ("saas.crm.read", "View Kalam SaaS commercial CRM"),
    ("saas.crm.manage", "Manage Kalam SaaS commercial CRM"),
]
ROLE_PERMISSIONS = {
    "SaaS Administrator": [key for key, _ in PERMISSIONS],
    "Sales Operations": ["tenant.read", "saas.crm.read", "saas.crm.manage"],
    "Sales Viewer": ["tenant.read", "saas.crm.read"],
}


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        if tenant is None:
            tenant = Tenant(name=OPS_NAME, slug=OPS_SLUG, status="active", settings={"workspace_type": "saas_operations"})
            db.add(tenant)
            await db.flush()
        else:
            tenant.name = OPS_NAME
            tenant.status = "active"

        permissions: dict[str, Permission] = {}
        for key, description in PERMISSIONS:
            item = await db.scalar(select(Permission).where(Permission.key == key))
            if item is None:
                item = Permission(key=key, description=description)
                db.add(item)
                await db.flush()
            permissions[key] = item

        roles: dict[str, Role] = {}
        for name, keys in ROLE_PERMISSIONS.items():
            role = await db.scalar(select(Role).where(Role.tenant_id == tenant.id, Role.name == name))
            if role is None:
                role = Role(tenant_id=tenant.id, name=name, description=f"Kalam operator role: {name}", role_kind="platform")
                db.add(role)
                await db.flush()
            roles[name] = role
            for key in keys:
                exists = await db.scalar(select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[key].id,
                ))
                if exists is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permissions[key].id))

        if ADMIN_EMAIL and ADMIN_PASSWORD:
            email = ADMIN_EMAIL.strip().lower()
            user = await db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
            if user is None:
                user = User(
                    tenant_id=tenant.id,
                    email=email,
                    password_hash=hash_password(ADMIN_PASSWORD),
                    first_name="Kognivon",
                    last_name="Operator",
                    job_title="SaaS Administrator",
                    is_active=True,
                )
                db.add(user)
                await db.flush()
            membership = await db.scalar(select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == roles["SaaS Administrator"].id,
            ))
            if membership is None:
                db.add(UserRole(user_id=user.id, role_id=roles["SaaS Administrator"].id))

        await db.commit()
        print(f"SaaS operations tenant ready: {tenant.slug}")
        print("Roles ready: " + ", ".join(ROLE_PERMISSIONS))
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            print("Operator account provisioned from environment variables.")
        else:
            print("No operator account created. Set SAAS_OPS_ADMIN_EMAIL and SAAS_OPS_ADMIN_PASSWORD and rerun when approved.")


if __name__ == "__main__":
    asyncio.run(main())
