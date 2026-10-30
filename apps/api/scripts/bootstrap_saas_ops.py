# ruff: noqa: E402

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.models import Permission, Role, RolePermission, Tenant, User, UserRole
from app.db.session import SessionLocal

OPS_SLUG = os.getenv("SAAS_OPS_TENANT_SLUG", "kalam")
OPS_NAME = os.getenv("SAAS_OPS_TENANT_NAME", "Kalam")
ADMIN_EMAIL = os.getenv("SAAS_OPS_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("SAAS_OPS_ADMIN_PASSWORD")

PERMISSIONS = [
    ("saas.crm.read", "View Kalam SaaS commercial CRM"),
    ("saas.crm.manage", "Manage Kalam SaaS commercial CRM"),
    ("platform.tenants.read", "View the platform tenant registry"),
    ("platform.tenants.manage", "Provision, suspend and reactivate customer tenants"),
    ("platform.health.read", "View platform service health"),
    ("platform.incidents.manage", "Investigate and manage platform incidents"),
    ("platform.support.access", "Start audited, time-limited customer support access"),
    ("platform.audit.read", "View platform operational audit records"),
]
ROLE_PERMISSIONS = {
    "SaaS Owner": ["saas.crm.read"],
    "Platform Developer": [
        "platform.tenants.read", "platform.tenants.manage", "platform.health.read",
        "platform.incidents.manage", "platform.support.access", "platform.audit.read",
    ],
    "Sales Operations": ["saas.crm.read", "saas.crm.manage"],
    "Sales Viewer": ["saas.crm.read"],
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

        # Preserve existing Owner memberships when upgrading the legacy
        # SaaS Administrator role name to the business-oriented SaaS Owner.
        legacy_owner = await db.scalar(
            select(Role).where(Role.tenant_id == tenant.id, Role.name == "SaaS Administrator")
        )
        current_owner = await db.scalar(
            select(Role).where(Role.tenant_id == tenant.id, Role.name == "SaaS Owner")
        )
        if legacy_owner is not None and current_owner is None:
            legacy_owner.name = "SaaS Owner"
            legacy_owner.description = "Kalam business owner: commercial read access only"
            legacy_owner.role_kind = "platform"
        elif legacy_owner is not None and current_owner is not None:
            old_links = (await db.execute(
                select(UserRole.user_id).where(UserRole.role_id == legacy_owner.id)
            )).scalars().all()
            for user_id in old_links:
                exists = await db.scalar(select(UserRole).where(
                    UserRole.user_id == user_id, UserRole.role_id == current_owner.id
                ))
                if exists is None:
                    db.add(UserRole(user_id=user_id, role_id=current_owner.id))
            await db.execute(delete(UserRole).where(UserRole.role_id == legacy_owner.id))
            await db.execute(delete(RolePermission).where(RolePermission.role_id == legacy_owner.id))
            await db.delete(legacy_owner)

        roles: dict[str, Role] = {}
        for name, keys in ROLE_PERMISSIONS.items():
            role = await db.scalar(select(Role).where(Role.tenant_id == tenant.id, Role.name == name))
            if role is None:
                role = Role(tenant_id=tenant.id, name=name, description=f"Kalam operator role: {name}", role_kind="platform")
                db.add(role)
                await db.flush()
            else:
                role.role_kind = "platform"
            roles[name] = role
            await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
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
                    job_title="SaaS Owner",
                    is_active=True,
                )
                db.add(user)
                await db.flush()
            membership = await db.scalar(select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == roles["SaaS Owner"].id,
            ))
            if membership is None:
                db.add(UserRole(user_id=user.id, role_id=roles["SaaS Owner"].id))

        await db.commit()
        print(f"SaaS operations tenant ready: {tenant.slug}")
        print("Roles ready: " + ", ".join(ROLE_PERMISSIONS))
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            print("Operator account provisioned from environment variables.")
        else:
            print("No operator account created. Set SAAS_OPS_ADMIN_EMAIL and SAAS_OPS_ADMIN_PASSWORD and rerun when approved.")


if __name__ == "__main__":
    asyncio.run(main())
