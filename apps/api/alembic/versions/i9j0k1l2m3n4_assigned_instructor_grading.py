"""Separate instructor session-scoped grading from assessment administration."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "i9j0k1l2m3n4"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    key = "assessments.grade_assigned"
    description = "Review and grade assessments for assigned instructor sessions"
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

    instructors = conn.execute(
        sa.text("SELECT id FROM roles WHERE lower(name)='instructor'")
    ).fetchall()
    for (role_id,) in instructors:
        conn.execute(
            sa.text("""
                DELETE FROM role_permissions
                WHERE role_id=:role_id
                  AND permission_id IN (
                      SELECT id FROM permissions WHERE key='assessments.manage'
                  )
            """),
            {"role_id": role_id},
        )
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
    # Do not restore tenant-wide assessment administration to instructors on
    # rollback. An explicit access review is required for any permission reset.
    pass
