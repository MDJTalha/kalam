"""Add explicit authorization for employee-linked compliance CSV exports."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "l2m3n4o5p6q7"
down_revision = "m1n2o3p4q5r6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    key = "reports.export.compliance"
    description = "Export employee-linked compliance assignment records"
    permission_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key=:key"),
        {"key": key},
    ).scalar()
    if permission_id is None:
        permission_id = uuid4()
        conn.execute(
            sa.text("""
                INSERT INTO permissions (id,key,description)
                VALUES (:id,:key,:description)
            """),
            {"id": permission_id, "key": key, "description": description},
        )
    role_names = ("Tenant Administrator", "HR / People Administrator", "Quality & Compliance")
    for role_name in role_names:
        roles = conn.execute(
            sa.text("SELECT id FROM roles WHERE lower(name)=lower(:name)"),
            {"name": role_name},
        ).fetchall()
        for (role_id,) in roles:
            conn.execute(
                sa.text("""
                    INSERT INTO role_permissions (role_id,permission_id)
                    SELECT :role_id,:permission_id
                    WHERE NOT EXISTS (
                        SELECT 1 FROM role_permissions
                        WHERE role_id=:role_id AND permission_id=:permission_id
                    )
                """),
                {"role_id": role_id, "permission_id": permission_id},
            )


def downgrade() -> None:
    # Do not silently revoke this grant from assigned users. Revert by explicit
    # role permission review if a rollback is ever required.
    pass
