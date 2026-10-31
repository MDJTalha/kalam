"""Tighten manager and regional-executive data scopes."""

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        INSERT INTO permissions (id, key, description)
        SELECT gen_random_uuid(), 'team.read',
               'View the current user''s direct reports and team learning signals'
        WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key='team.read')
    """))

    # Managers receive only the dedicated direct-report capability. The
    # generic users.read and reports.read permissions currently expose the
    # full tenant directory and tenant-wide reports, respectively.
    conn.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r CROSS JOIN permissions p
        WHERE lower(r.name)='manager'
          AND p.key='team.read'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id=r.id AND rp.permission_id=p.id
          )
    """))
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id AND rp.permission_id=p.id
          AND lower(r.name)='manager'
          AND p.key IN ('users.read','reports.read')
    """))

    # HR/People and HRBP retain their existing workforce-wide remit but also
    # receive the dedicated team endpoint where they have direct reports.
    conn.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r CROSS JOIN permissions p
        WHERE lower(r.name) IN ('tenant administrator','hr / people administrator','hr business partner')
          AND p.key='team.read'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id=r.id AND rp.permission_id=p.id
          )
    """))

    # A regional executive must not be granted tenant-wide reports until a
    # region/org-unit scope model is implemented across the read APIs.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r
        WHERE rp.role_id=r.id
          AND lower(r.name)='regional executive'
    """))
    conn.execute(sa.text("""
        UPDATE roles
        SET description='Unavailable until regional row-level data scope is implemented'
        WHERE lower(name)='regional executive'
    """))

    # Remove the former all-purpose CRM grants from operator roles. Their new
    # domain grants are added by the canonical role-catalogue migration.
    conn.execute(sa.text("""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id=r.id
          AND rp.permission_id=p.id
          AND r.name IN (
              'SaaS Administrator', 'Sales Operations', 'Sales Viewer',
              'SaaS Finance Administrator', 'Customer Success Manager'
          )
          AND p.key IN ('saas.crm.read','saas.crm.manage')
    """))


def downgrade() -> None:
    # Keep the team.read permission definition and existing role grants on
    # rollback. Restoring tenant-wide Manager/Regional Executive access would
    # reintroduce the confidentiality exposure this migration closes.
    pass
