"""Record submitter/requester and reviewer attribution for compliance separation of duties."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "compliance_evidence",
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_compliance_evidence_submitted_by",
        "compliance_evidence",
        ["submitted_by"],
    )
    op.execute(sa.text("""
        UPDATE compliance_evidence
        SET submitted_by=user_id
        WHERE submitted_by IS NULL
    """))

    op.add_column(
        "compliance_exceptions",
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_compliance_exceptions_requested_by",
        "compliance_exceptions",
        ["requested_by"],
    )
    op.add_column(
        "compliance_exceptions",
        sa.Column(
            "rejected_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_compliance_exceptions_rejected_by",
        "compliance_exceptions",
        ["rejected_by"],
    )
    op.add_column(
        "compliance_exceptions",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("compliance_exceptions", "rejected_at")
    op.drop_index("ix_compliance_exceptions_rejected_by", table_name="compliance_exceptions")
    op.drop_column("compliance_exceptions", "rejected_by")
    op.drop_index("ix_compliance_exceptions_requested_by", table_name="compliance_exceptions")
    op.drop_column("compliance_exceptions", "requested_by")
    op.drop_index("ix_compliance_evidence_submitted_by", table_name="compliance_evidence")
    op.drop_column("compliance_evidence", "submitted_by")
