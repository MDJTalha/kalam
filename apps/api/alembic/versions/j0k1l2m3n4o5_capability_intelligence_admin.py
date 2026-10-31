"""Grant capability intelligence administration to accountable tenant roles."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None

PERMISSIONS = {
    "capability_gaps.manage": "Recalculate and administer tenant capability-gap intelligence",
    "capability_risk.manage": "Recalculate and administer tenant capability-risk intelligence",
}
ROLE_NAMES = (
    "Tenant Administrator",
    "HR / People Administrator",
    "L&D Administrator",
)


def upgrade() -> None:
    conn = op.get_bind()
    ids = {}
    for key, description in PERMISSIONS.items():
        permission_id = conn.execute(
            sa.text("SELECT id FROM permissions WHERE key=:key"),
            {"key": key},
        ).scalar()
        if permission_id is None:
            permission_id = uuid4()
            conn.execute(
                sa.text("INSERT INTO permissions (id,key,description) VALUES (:id,:key,:description)"),
                {"id": permission_id, "key": key, "description": description},
            )
        ids[key] = permission_id

    for role_name in ROLE_NAMES:
        rows = conn.execute(
            sa.text("SELECT id FROM roles WHERE lower(name)=lower(:name)"),
            {"name": role_name},
        ).fetchall()
        for (role_id,) in rows:
            for key, permission_id in ids.items():
                conn.execute(
                    sa.text("""
                        INSERT INTO role_permissions (role_id, permission_id)
                        SELECT :role_id, :permission_id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM role_permissions
                            WHERE role_id=:role_id AND permission_id=:permission_id
                        )
                    """),
                    {"role_id": role_id, "permission_id": permission_id},
                )


def downgrade() -> None:
    # Preserve assigned governance grants during rollback. Revoke explicitly
    # after checking each tenant's operational coverage.
    pass
