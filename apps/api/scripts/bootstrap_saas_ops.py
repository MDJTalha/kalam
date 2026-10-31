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

from app.core.role_catalog import PERMISSION_DESCRIPTIONS, PLATFORM_ROLE_PERMISSIONS
from app.core.security import hash_password
from app.db.models import Permission, Role, RolePermission, Tenant, User, UserRole
from app.db.session import SessionLocal

OPS_SLUG = os.getenv("SAAS_OPS_TENANT_SLUG", "kalam")
OPS_NAME = os.getenv("SAAS_OPS_TENANT_NAME", "Kalam")
ADMIN_EMAIL = os.getenv("SAAS_OPS_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("SAAS_OPS_ADMIN_PASSWORD")
SUPER_ADMIN_EMAIL = os.getenv("SAAS_SUPER_ADMIN_EMAIL")
SUPER_ADMIN_PASSWORD = os.getenv("SAAS_SUPER_ADMIN_PASSWORD")


async def _ensure_operator(
    db,
    tenant: Tenant,
    role: Role,
    *,
    email: str,
    password: str | None,
    first_name: str,
    last_name: str,
    job_title: str,
    require_password_for_new: bool,
) -> str:
    normalized_email = email.strip().lower()
    user = await db.scalar(
        select(User).where(User.tenant_id == tenant.id, User.email == normalized_email)
    )
    action = "existing"
    if user is None:
        if not password:
            if require_password_for_new:
                raise RuntimeError(f"A secure initial password is required to create {normalized_email}")
            return "not_created"
        if require_password_for_new and len(password) < 16:
            raise RuntimeError("SaaS Super Admin initial password must be at least 16 characters")
        user = User(
            tenant_id=tenant.id,
            email=normalized_email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        action = "created"

    membership = await db.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if membership is None:
        db.add(UserRole(user_id=user.id, role_id=role.id))
        action = "created_and_assigned" if action == "created" else "assigned"
    return action


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == OPS_SLUG))
        if tenant is None:
            tenant = Tenant(
                name=OPS_NAME,
                slug=OPS_SLUG,
                status="active",
                settings={"workspace_type": "saas_operations"},
            )
            db.add(tenant)
            await db.flush()
        else:
            tenant.name = OPS_NAME
            tenant.status = "active"
            tenant.settings = {**(tenant.settings or {}), "workspace_type": "saas_operations"}

        permissions: dict[str, Permission] = {}
        for key, description in PERMISSION_DESCRIPTIONS.items():
            item = await db.scalar(select(Permission).where(Permission.key == key))
            if item is None:
                item = Permission(key=key, description=description)
                db.add(item)
                await db.flush()
            elif not item.description:
                item.description = description
            permissions[key] = item

        roles: dict[str, Role] = {}
        for name, keys in PLATFORM_ROLE_PERMISSIONS.items():
            role = await db.scalar(
                select(Role).where(Role.tenant_id == tenant.id, Role.name == name)
            )
            if role is None:
                role = Role(
                    tenant_id=tenant.id,
                    name=name,
                    description=f"Kalam platform role: {name}",
                    role_kind="platform",
                )
                db.add(role)
                await db.flush()
            else:
                role.description = f"Kalam platform role: {name}"
                role.role_kind = "platform"
            roles[name] = role

            for key in keys:
                permission = permissions[key]
                exists = await db.scalar(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                if exists is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        if ADMIN_EMAIL:
            if not ADMIN_PASSWORD:
                print("SaaS Administrator account not provisioned: SAAS_OPS_ADMIN_PASSWORD is not set.")
            else:
                result = await _ensure_operator(
                    db, tenant, roles["SaaS Administrator"],
                    email=ADMIN_EMAIL, password=ADMIN_PASSWORD,
                    first_name="Kalam", last_name="Administrator",
                    job_title="SaaS Administrator", require_password_for_new=False,
                )
                print(f"SaaS Administrator account: {result}")

        if SUPER_ADMIN_EMAIL:
            if not SUPER_ADMIN_PASSWORD:
                print("SaaS Super Admin account not provisioned: SAAS_SUPER_ADMIN_PASSWORD is not set.")
            else:
                result = await _ensure_operator(
                    db, tenant, roles["SaaS Super Admin"],
                    email=SUPER_ADMIN_EMAIL, password=SUPER_ADMIN_PASSWORD,
                    first_name="SaaS", last_name="Super Admin",
                    job_title="SaaS Super Admin", require_password_for_new=True,
                )
                print(f"SaaS Super Admin account: {result}")

        await db.commit()
        print(f"SaaS operations tenant ready: {tenant.slug}")
        print("Platform roles ready: " + ", ".join(PLATFORM_ROLE_PERMISSIONS))
        if not SUPER_ADMIN_EMAIL:
            print("No Super Admin identity created. Set SAAS_SUPER_ADMIN_EMAIL and SAAS_SUPER_ADMIN_PASSWORD to provision it securely.")


if __name__ == "__main__":
    asyncio.run(main())
