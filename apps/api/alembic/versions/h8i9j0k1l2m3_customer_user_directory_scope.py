"""Restrict customer-employee directory visibility to customer success and Super Admin."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "h8i9j0k1l2m3"
down_revision = "r2s3t4u5v6w7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    key = "saas.customer_users.read"
    description = "View customer-tenant employee accounts and access status"
    permission_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key=:key"),
        {"key": key},
    ).scalar()
    if permission_id is None:
        permission_id = uuid4()
        conn.execute(
            sa.text("""
                INSERT INTO permissions (id, key, description)
                VALUES (:id, :key, :description)
            """),
            {"id": permission_id, "key": key, "description": description},
        )

    conn.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, :permission_id
        FROM roles r
        WHERE lower(r.name) IN ('saas super admin','customer success manager')
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id=r.id AND rp.permission_id=:permission_id
          )
    """), {"permission_id": permission_id})

    # Sales Operators see only their owner pool. Business owners can review
    # commercial aggregates but do not need named internal employee rosters.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id AND rp.permission_id=p.id
          AND (
              (r.name='SaaS Business Owner' AND p.key='saas.team.read')
              OR (r.name='Sales Operations' AND p.key='saas.customer_success.read')
          )
    """))


def downgrade() -> None:
    # Keep access restrictions in place on downgrade; role assignments must be
    # reviewed explicitly if reverting this privacy boundary.
    pass
