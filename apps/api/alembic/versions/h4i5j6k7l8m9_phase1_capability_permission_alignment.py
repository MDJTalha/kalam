"""Align Phase 1 capability framework permissions with tenant roles."""
from alembic import op
import sqlalchemy as sa

revision = "h4i5j6k7l8m9"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None

ROLE_PERMISSIONS = {
    "Tenant Owner": ("capabilities.read", "capabilities.manage"),
    "Tenant Administrator": ("capabilities.read", "capabilities.manage"),
    "L&D Administrator": ("capabilities.read", "capabilities.manage"),
    "HR / People Administrator": ("capabilities.read", "capabilities.manage"),
    "Manager": ("capabilities.read",),
}


def upgrade() -> None:
    conn = op.get_bind()
    for role_name, keys in ROLE_PERMISSIONS.items():
        for key in keys:
            conn.execute(
                sa.text("""
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM roles r
                    CROSS JOIN permissions p
                    WHERE r.name = :role_name
                      AND p.key = :permission_key
                      AND NOT EXISTS (
                          SELECT 1
                          FROM role_permissions rp
                          WHERE rp.role_id = r.id
                            AND rp.permission_id = p.id
                      )
                """),
                {"role_name": role_name, "permission_key": key},
            )


def downgrade() -> None:
    conn = op.get_bind()
    for role_name, keys in ROLE_PERMISSIONS.items():
        for key in keys:
            conn.execute(
                sa.text("""
                    DELETE FROM role_permissions rp
                    USING roles r, permissions p
                    WHERE rp.role_id = r.id
                      AND rp.permission_id = p.id
                      AND r.name = :role_name
                      AND p.key = :permission_key
                """),
                {"role_name": role_name, "permission_key": key},
            )
