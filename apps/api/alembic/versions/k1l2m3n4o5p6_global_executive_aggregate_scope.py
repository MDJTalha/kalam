"""Restrict Global Executive to aggregate enterprise reporting."""

from alembic import op
import sqlalchemy as sa

revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND lower(r.name)='global executive'
          AND p.key IN (
              'users.read',
              'capability_gaps.read',
              'capability_risk.read',
              'development.manage',
              'compliance.manage'
          )
    """))


def downgrade() -> None:
    # Do not automatically restore individual-employee access. Any broadened
    # executive data scope must receive a fresh privacy and business-purpose review.
    pass
