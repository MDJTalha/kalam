"""Record reviewer rejection of compliance evidence."""

from alembic import op
import sqlalchemy as sa

revision = "r3s4t5u6v7w8"
down_revision = "q2r3s4t5u6v7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("compliance_evidence", sa.Column("rejected_by", sa.UUID(), nullable=True))
    op.add_column("compliance_evidence", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("compliance_evidence", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.create_foreign_key("fk_compliance_evidence_rejected_by", "compliance_evidence", "users",
                          ["rejected_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_compliance_evidence_rejected_by", "compliance_evidence", ["rejected_by"])


def downgrade() -> None:
    op.drop_index("ix_compliance_evidence_rejected_by", table_name="compliance_evidence")
    op.drop_constraint("fk_compliance_evidence_rejected_by", "compliance_evidence", type_="foreignkey")
    op.drop_column("compliance_evidence", "rejection_reason")
    op.drop_column("compliance_evidence", "rejected_at")
    op.drop_column("compliance_evidence", "rejected_by")
