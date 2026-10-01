"""Align predefined tenant permissions with administration surfaces."""
from alembic import op
import sqlalchemy as sa

revision = "n3o4p5q6r7s8"
down_revision = "m2n3o4p5q6r7"
branch_labels = None
depends_on = None

ROLE_PERMISSIONS = {
    "HR / People Administrator": ["compliance.manage"],
    "L&D Administrator": ["users.read"],
}


def upgrade():
    conn = op.get_bind()
    for role_name, keys in ROLE_PERMISSIONS.items():
        for key in keys:
            conn.execute(sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r CROSS JOIN permissions p
                WHERE r.name=:role_name
                  AND p.key=:permission_key
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions rp
                    WHERE rp.role_id=r.id AND rp.permission_id=p.id
                  )
            """), {"role_name": role_name, "permission_key": key})


def downgrade():
    conn = op.get_bind()
    for role_name, keys in ROLE_PERMISSIONS.items():
        for key in keys:
            conn.execute(sa.text("""
                DELETE FROM role_permissions
                WHERE role_id IN (SELECT id FROM roles WHERE name=:role_name)
                  AND permission_id IN (SELECT id FROM permissions WHERE key=:permission_key)
            """), {"role_name": role_name, "permission_key": key})
