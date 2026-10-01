"""Phase 2 evidence provenance uniqueness."""

from alembic import op
import sqlalchemy as sa

revision = "ee55ff66aa77"
down_revision = "dd44ee55ff66"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_unique_constraint(
        "uq_capability_evidence_source_provenance",
        "capability_evidence",
        ["tenant_id", "user_id", "target_type", "target_id", "source_type", "source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_capability_evidence_source_provenance",
        "capability_evidence",
        type_="unique",
    )
