"""Backfill SaaS CRM permissions for upgraded installations."""

from alembic import op
import sqlalchemy as sa

revision = "w8x9y0z1a2b3"
down_revision = "v7w8x9y0z1a2"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("saas.crm.read", "View Kognivon SaaS commercial CRM"),
    ("saas.crm.manage", "Manage Kognivon SaaS commercial CRM"),
)


def upgrade() -> None:
    for key, description in PERMISSIONS:
        op.execute(
            sa.text(
                "INSERT INTO permissions (id, key, description) "
                "SELECT gen_random_uuid(), :key, :description "
                "WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key = :key)"
            ).bindparams(key=key, description=description)
        )
        op.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
                "WHERE r.name = 'Tenant Admin' AND p.key = :key "
                "AND NOT EXISTS (SELECT 1 FROM role_permissions rp "
                "WHERE rp.role_id = r.id AND rp.permission_id = p.id)"
            ).bindparams(key=key)
        )


def downgrade() -> None:
    keys = tuple(key for key, _ in PERMISSIONS)
    op.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE key IN :keys)"
        ).bindparams(sa.bindparam("keys", expanding=True, value=keys))
    )
    op.execute(
        sa.text("DELETE FROM permissions WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True, value=keys)
        )
    )
