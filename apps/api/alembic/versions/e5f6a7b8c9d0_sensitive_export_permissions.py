"""Add explicit permissions for exports containing employee-identifiable records."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

PERMISSIONS = {
    "reports.export.people": "Export employee-identifiable workforce registers",
    "reports.export.learning": "Export employee-linked learning and enrollment registers",
}

ROLE_EXPORTS = {
    "Tenant Administrator": ("reports.export.people", "reports.export.learning"),
    "HR / People Administrator": ("reports.export.people", "reports.export.learning"),
    "L&D Administrator": ("reports.export.learning",),
}


def upgrade() -> None:
    conn = op.get_bind()
    permission_ids = {}
    for key, description in PERMISSIONS.items():
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
        permission_ids[key] = permission_id

    for role_name, keys in ROLE_EXPORTS.items():
        roles = conn.execute(
            sa.text("SELECT id FROM roles WHERE lower(name)=lower(:name)"),
            {"name": role_name},
        ).fetchall()
        for (role_id,) in roles:
            for key in keys:
                permission_id = permission_ids[key]
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
    # Keep grant revocation explicit; blindly removing these grants could alter
    # role assignments made after this migration was deployed.
    pass
