from alembic import op
import sqlalchemy as sa
from uuid import uuid4

revision = "m2n3o4p5q6r7"
down_revision = "l1m2n3o4p5q6"
branch_labels = None
depends_on = None

TENANT_OWNER_PERMISSIONS = ["tenant.read", "reports.read", "audit.read"]


def upgrade():
    conn = op.get_bind()
    permission_rows = conn.execute(
        sa.text("SELECT id,key FROM permissions WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": TENANT_OWNER_PERMISSIONS},
    ).fetchall()
    permission_ids = {row.key: row.id for row in permission_rows}
    tenants = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug <> 'kalam'")
    ).fetchall()
    for (tenant_id,) in tenants:
        role_id = conn.execute(
            sa.text("SELECT id FROM roles WHERE tenant_id=:tenant AND name='Tenant Owner'"),
            {"tenant": tenant_id},
        ).scalar()
        if role_id is None:
            role_id = uuid4()
            conn.execute(
                sa.text("""
                    INSERT INTO roles (id, tenant_id, name, description, role_kind)
                    VALUES (:id, :tenant, 'Tenant Owner', :description, 'predefined')
                """),
                {
                    "id": role_id,
                    "tenant": tenant_id,
                    "description": "Kalam predefined tenant role: Tenant Owner",
                },
            )
        else:
            conn.execute(
                sa.text("UPDATE roles SET role_kind='predefined', description=:description WHERE id=:id"),
                {"id": role_id, "description": "Kalam predefined tenant role: Tenant Owner"},
            )
        for key in TENANT_OWNER_PERMISSIONS:
            permission_id = permission_ids.get(key)
            if permission_id:
                conn.execute(
                    sa.text("""
                        INSERT INTO role_permissions (role_id, permission_id)
                        SELECT :role, :permission
                        WHERE NOT EXISTS (
                            SELECT 1 FROM role_permissions
                            WHERE role_id=:role AND permission_id=:permission
                        )
                    """),
                    {"role": role_id, "permission": permission_id},
                )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM role_permissions rp USING roles r WHERE rp.role_id=r.id AND r.name='Tenant Owner'")
    )
    conn.execute(sa.text("DELETE FROM roles WHERE name='Tenant Owner'"))
