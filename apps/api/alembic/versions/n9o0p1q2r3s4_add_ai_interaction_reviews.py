"""Add AI interaction human-review evidence."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "n9o0p1q2r3s4"
down_revision = "m8n9o0p1q2r3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_interaction_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_interactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("interaction_id", name="uq_ai_review_interaction"),
    )
    op.create_index("ix_ai_interaction_reviews_tenant_id", "ai_interaction_reviews", ["tenant_id"])
    op.create_index("ix_ai_interaction_reviews_interaction_id", "ai_interaction_reviews", ["interaction_id"])
    op.create_index("ix_ai_interaction_reviews_reviewer_id", "ai_interaction_reviews", ["reviewer_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_interaction_reviews_reviewer_id", table_name="ai_interaction_reviews")
    op.drop_index("ix_ai_interaction_reviews_interaction_id", table_name="ai_interaction_reviews")
    op.drop_index("ix_ai_interaction_reviews_tenant_id", table_name="ai_interaction_reviews")
    op.drop_table("ai_interaction_reviews")
