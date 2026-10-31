"""Align HRBP direct-report development and Quality data boundaries."""

from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # HRBP may manage plans/milestones/feedback only for direct reports.
    # The API checks team.read and manager_id before allowing target-user access.
    conn.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r CROSS JOIN permissions p
        WHERE lower(r.name)='hr business partner'
          AND p.key='development.manage'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id=r.id AND rp.permission_id=p.id
          )
    """))

    # Quality & Compliance owns compliance operations, not the employee
    # directory or general workforce analytics and exports.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND lower(r.name)='quality & compliance'
          AND p.key IN ('users.read','reports.read')
    """))


def downgrade() -> None:
    # Keep the restricted Quality role and direct-report HRBP scope on rollback.
    pass
