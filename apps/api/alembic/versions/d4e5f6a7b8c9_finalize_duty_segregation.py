"""Finalize restricted HRBP scope and segregated SaaS operator grants."""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # HR Business Partner currently has no assigned business-unit portfolio.
    # Retain direct-report access only until org-unit scope assignments and
    # row-level filters exist consistently across all people/capability APIs.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND lower(r.name)='hr business partner'
          AND p.key IN (
              'users.read','reports.read','development.manage',
              'capabilities.read','capability_gaps.read','capability_risk.read'
          )
    """))

    # Sales owns the commercial pipeline, not technical customer lifecycle.
    # Customer success is responsible for onboarding, trials and tenant status.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND r.name='Sales Operations'
          AND p.key='saas.customer_success.manage'
    """))

    # The SaaS Administrator may operate team lifecycle but cannot define
    # custom platform roles; that authority is reserved for SaaS Super Admin.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND r.name='SaaS Administrator'
          AND p.key='saas.roles.manage'
    """))


def downgrade() -> None:
    # Do not restore unscoped HRBP data access or combine sales and customer-
    # success administration on rollback.
    pass
