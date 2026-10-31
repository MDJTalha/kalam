"""Separate capability evidence capture, verification and read-only reference access."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p2q3r4s5t6u7"
down_revision = "n1p2q3r4s5t6"
branch_labels = None
depends_on = None

PERMISSIONS = {
    "evidence.manage": "Capture and administer capability evidence",
    "evidence.verify": "Independently verify or reject submitted capability evidence",
    "competencies.read": "View governed competency definitions and proficiency levels",
}


def upgrade() -> None:
    conn = op.get_bind()
    op.add_column(
        "capability_evidence",
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_capability_evidence_submitted_by",
        "capability_evidence",
        ["submitted_by"],
    )
    permission_ids = {};
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

    for (role_id,) in conn.execute(
        sa.text("SELECT id FROM roles WHERE lower(name)='l&d administrator'")
    ).fetchall():
        for key in PERMISSIONS:
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

    for (role_id,) in conn.execute(
        sa.text("SELECT id FROM roles WHERE lower(name)='auditor'")
    ).fetchall():
        permission_id = permission_ids["competencies.read"]
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

    # Historical submitter attribution is reconstructed only from the original
    # evidence-created audit event; do not infer the submitter from the subject.
    conn.execute(sa.text("""
        UPDATE capability_evidence evidence
        SET submitted_by = event.actor_id
        FROM (
            SELECT DISTINCT ON (entity_id)
                entity_id, actor_id
            FROM audit_logs
            WHERE entity_type='capability_evidence'
              AND action='capability.evidence.created'
            ORDER BY entity_id, created_at ASC
        ) event
        WHERE evidence.submitted_by IS NULL
          AND evidence.id::text = event.entity_id
    """))


def downgrade() -> None:
    # Preserve the attribution in deployed environments; reverting this field
    # would discard evidence provenance and reopen reviewer self-conflict risk.
    pass
