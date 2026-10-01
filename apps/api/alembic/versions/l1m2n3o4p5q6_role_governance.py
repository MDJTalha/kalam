"""Add governed tenant role metadata and predefined tenant roles."""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4

revision = "l1m2n3o4p5q6"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None

PREDEFINED = {
    "Tenant Administrator": ["tenant.read","tenant.manage","users.read","users.manage","reports.read","audit.read","integrations.manage"],
    "HR / People Administrator": ["users.read","users.manage","reports.read"],
    "L&D Administrator": ["courses.read","courses.manage","learning.access","assessments.manage","certificates.manage","reports.read","skills.manage","development.manage"],
    "Manager": ["users.read","courses.read","learning.access","reports.read","development.manage"],
    "Instructor": ["courses.read","learning.access","assessments.manage"],
    "Learner / Employee": ["courses.read","learning.access","development.manage"],
}

def upgrade():
    op.add_column("roles", sa.Column("role_kind", sa.String(20), nullable=False, server_default="custom"))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE roles r SET role_kind='platform' FROM tenants t WHERE r.tenant_id=t.id AND t.slug='kalam'"))
    conn.execute(sa.text("""
        UPDATE roles SET role_kind='predefined'
        WHERE lower(name) IN ('manager','instructor','learner','tenant administrator','hr / people administrator','l&d administrator')
    """))
    conn.execute(sa.text("""
        UPDATE roles SET role_kind='legacy'
        WHERE lower(name) IN ('tenant admin','hr/l&d admin','global executive','regional executive','hr business partner','quality & compliance','auditor')
    """))
    conn.execute(sa.text("UPDATE roles SET name='Tenant Administrator', description='Kalam predefined tenant role: Tenant Administrator', role_kind='predefined' WHERE name='Tenant Admin' AND tenant_id IN (SELECT id FROM tenants WHERE slug <> 'kalam')"))
    tenants = conn.execute(sa.text("SELECT id FROM tenants WHERE slug <> 'kalam'")).fetchall()
    permission_rows = conn.execute(sa.text("SELECT id,key FROM permissions WHERE key IN :keys").bindparams(sa.bindparam("keys", expanding=True)), {"keys": sorted({k for v in PREDEFINED.values() for k in v})}).fetchall()
    permission_ids = {row.key: row.id for row in permission_rows}
    for (tenant_id,) in tenants:
        for name, keys in PREDEFINED.items():
            existing = conn.execute(sa.text("SELECT id FROM roles WHERE tenant_id=:tenant AND name=:name"), {"tenant":tenant_id,"name":name}).scalar()
            if existing is None:
                role_id = uuid4()
                conn.execute(sa.text("INSERT INTO roles (id,tenant_id,name,description,role_kind) VALUES (:id,:tenant,:name,:description,'predefined')"), {"id":role_id,"tenant":tenant_id,"name":name,"description":f"Kalam predefined tenant role: {name}"})
            else:
                role_id = existing
                conn.execute(sa.text("UPDATE roles SET role_kind='predefined', description=:description WHERE id=:id"), {"id":role_id,"description":f"Kalam predefined tenant role: {name}"})
            for key in keys:
                pid = permission_ids.get(key)
                if pid:
                    conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT :role,:perm WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=:role AND permission_id=:perm)"), {"role":role_id,"perm":pid})
    conn.execute(sa.text("UPDATE roles SET name='Tenant Administrator', description='Kalam predefined tenant role: Tenant Administrator', role_kind='predefined' WHERE name='Tenant Admin' AND tenant_id IN (SELECT id FROM tenants WHERE slug <> 'kalam')"))
    conn.execute(sa.text("DELETE FROM role_permissions rp USING roles r WHERE rp.role_id=r.id AND r.name='Tenant Administrator' AND r.tenant_id IN (SELECT id FROM tenants WHERE slug <> 'kalam')"))
    for (tenant_id,) in tenants:
        role_id = conn.execute(sa.text("SELECT id FROM roles WHERE tenant_id=:tenant AND name='Tenant Administrator'"), {"tenant":tenant_id}).scalar()
        for key in PREDEFINED["Tenant Administrator"]:
            pid = permission_ids.get(key)
            if pid:
                conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT :role,:perm WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=:role AND permission_id=:perm)"), {"role":role_id,"perm":pid})

def downgrade():
    op.drop_column("roles","role_kind")
