"""Add provider-reported token usage to AI interactions."""
from alembic import op
import sqlalchemy as sa

revision = "p1q2r3s4t5u6"
down_revision = "o0p1q2r3s4t5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_interactions", sa.Column("input_tokens", sa.Integer(), nullable=True))
    op.add_column("ai_interactions", sa.Column("output_tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_interactions", "output_tokens")
    op.drop_column("ai_interactions", "input_tokens")
