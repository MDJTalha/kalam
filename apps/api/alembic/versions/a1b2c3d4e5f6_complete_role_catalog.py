"""Provision the canonical tenant and SaaS platform role catalogue."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

from app.core.role_catalog import (
    PERMISSION_DESCRIPTIONS,
    PLATFORM_ROLE_PERMISSIONS,
    TENANT_ROLE_PERMISSIONS,
)

revision = "a1b2c3d4e5f6"
down_revision = "z1a2b3c4d5e6"
branch_labels = None
depends_on = None


def _ensure_role(conn, tenant_id, name, description, role_kind):
    role_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE tenant_id=:tenant_id AND name=:name"),
        {"tenant_id": tenant_id, "name": name},
    ).scalar()
    if role_id is None:
        role_id = uuid4()
        conn.execute(
            sa.text("""
                INSERT INTO roles (id, tenant_id, name, description, role_kind)
                VALUES (:id, :tenant_id, :name, :description, :role_kind)
            """),
            {
                "id": role_id,
                "tenant_id": tenant_id,
                "name": name,
                "description": description,
                "role_kind": role_kind,
            },
        )
    else:
        conn.execute(
            sa.text("""
                UPDATE roles
                SET description=:description, role_kind=:role_kind
                WHERE id=:id
            """),
            {"id": role_id, "description": description, "role_kind": role_kind},
        )
    return role_id


def _ensure_role_permissions(conn, role_id, keys, permission_ids):
    for key in keys:
        permission_id = permission_ids.get(key)
        if permission_id is None:
            raise RuntimeError(f"Role catalogue references missing permission: {key}")
        conn.execute(
            sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT :role_id, :permission_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM role_permissions
                    WHERE role_id=:role_id AND permission_id=:permission_id
                )
            """),
            {"role_id": role_id, "permission_id": permission_id},
        )


def upgrade() -> None:
    conn = op.get_bind()

    for key, description in PERMISSION_DESCRIPTIONS.items():
        conn.execute(
            sa.text("""
                INSERT INTO permissions (id, key, description)
                SELECT :id, :key, :description
                WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key=:key)
            """),
            {"id": uuid4(), "key": key, "description": description},
        )

    permission_rows = conn.execute(
        sa.text("SELECT id, key FROM permissions")
    ).fetchall()
    permission_ids = {row.key: row.id for row in permission_rows}

    # Customer workspaces receive the tenant role catalogue. Existing roles are
    # preserved and only missing default grants are added.
    tenant_ids = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug <> 'kalam'")
    ).fetchall()
    for (tenant_id,) in tenant_ids:
        for name, keys in TENANT_ROLE_PERMISSIONS.items():
            role_id = _ensure_role(
                conn,
                tenant_id,
                name,
                f"Kalam predefined tenant role: {name}",
                "predefined",
            )
            _ensure_role_permissions(conn, role_id, keys, permission_ids)

    # Internal SaaS roles live only in the configured operations tenant.
    ops_tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug='kalam'")
    ).scalar()
    if ops_tenant_id is not None:
        for name, keys in PLATFORM_ROLE_PERMISSIONS.items():
            role_id = _ensure_role(
                conn,
                ops_tenant_id,
                name,
                f"Kalam platform role: {name}",
                "platform",
            )
            _ensure_role_permissions(conn, role_id, keys, permission_ids)


def downgrade() -> None:
    # Deliberately non-destructive: roles and permission grants may have been
    # assigned to users after upgrade. Removing them automatically could lock
    # out tenant administrators or invalidate active SaaS operations accounts.
    pass
