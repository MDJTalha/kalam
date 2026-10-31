"""Grant Quality & Compliance access to organization metadata without people records."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "n1p2q3r4s5t6"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    key = "organization.read"
    description = "View tenant role and organization-unit metadata without employee records"
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
        WHERE lower(r.name)='quality & compliance'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id=r.id AND rp.permission_id=:permission_id
          )
    """), {"permission_id": permission_id})


def downgrade() -> None:
    # Preserve the metadata-only grant during rollback; revoke it explicitly
    # after reviewing any Quality & Compliance policies that depend on it.
    pass
