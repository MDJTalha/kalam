"""Add saved-report management permission."""
from alembic import op
import sqlalchemy as sa

revision = "i4f5a6b7c8d9"
down_revision = "h3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("INSERT INTO permissions (id, key, description) SELECT gen_random_uuid(), 'reports.manage', 'Create and manage saved reports and schedules' WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key = 'reports.manage')"))
    op.execute(sa.text("INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.name IN ('Tenant Admin', 'HR/L&D Admin') AND p.key = 'reports.manage' AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id)"))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE key = 'reports.manage')"))
    op.execute(sa.text("DELETE FROM permissions WHERE key = 'reports.manage'"))
