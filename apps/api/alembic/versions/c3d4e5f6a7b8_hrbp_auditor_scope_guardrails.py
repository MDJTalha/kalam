"""Remove unscoped HRBP and auditor grants from existing tenant role rows."""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND lower(r.name)='hr business partner'
          AND p.key IN ('users.read','reports.read','development.manage')
    """))
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND lower(r.name)='auditor'
          AND p.key='reports.read'
    """))


def downgrade() -> None:
    # Deliberately do not restore broad, unscoped access on rollback.
    pass
