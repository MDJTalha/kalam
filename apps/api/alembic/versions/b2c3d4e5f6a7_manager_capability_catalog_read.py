"""Allow Managers to read the tenant capability catalogue.

Manager access remains read-only for capability definitions. Sensitive capability
framework administration, competency/objective catalogues, assessments, and
employee-specific capability records retain their separate permissions.
"""
from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    permission_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key = :key"),
        {"key": "capabilities.read"},
    ).scalar()
    if permission_id is None:
        permission_id = uuid4()
        conn.execute(
            sa.text(
                "INSERT INTO permissions (id, key, description) "
                "VALUES (:id, :key, :description)"
            ),
            {
                "id": permission_id,
                "key": "capabilities.read",
                "description": "Read the tenant capability catalogue",
            },
        )

    conn.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, :permission_id FROM roles r "
            "WHERE lower(r.name) = 'manager' "
            "AND r.role_kind IN ('predefined', 'legacy') "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM role_permissions rp "
            "  WHERE rp.role_id = r.id AND rp.permission_id = :permission_id"
            ")"
        ),
        {"permission_id": permission_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    permission_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key = :key"),
        {"key": "capabilities.read"},
    ).scalar()
    if permission_id is None:
        return
    conn.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id = :permission_id "
            "AND role_id IN (SELECT id FROM roles WHERE lower(name) = 'manager' "
            "AND role_kind IN ('predefined', 'legacy'))"
        ),
        {"permission_id": permission_id},
    )
