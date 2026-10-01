"""Align Phase 1 capability permissions with privileged tenant roles."""
from alembic import op
import sqlalchemy as sa

revision = "cc33dd44ee55"
down_revision = "bb22cc33dd44"
branch_labels = None
depends_on = None

PERMISSIONS = (
    "strategic_objectives.read",
    "strategic_objectives.manage",
    "competencies.read",
    "competencies.manage",
    "role_requirements.read",
    "role_requirements.manage",
)


def upgrade() -> None:
    conn = op.get_bind()
    for key in PERMISSIONS:
        conn.execute(
            sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r
                CROSS JOIN permissions p
                WHERE r.name IN ('Tenant Owner', 'Tenant Administrator', 'Platform Developer')
                  AND p.key = :permission_key
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions rp
                    WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  )
            """),
            {"permission_key": key},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            DELETE FROM role_permissions rp
            USING roles r, permissions p
            WHERE rp.role_id = r.id
              AND rp.permission_id = p.id
              AND r.name IN ('Tenant Owner', 'Tenant Administrator', 'Platform Developer')
              AND p.key = ANY(:keys)
        """),
        {"keys": list(PERMISSIONS)},
    )
