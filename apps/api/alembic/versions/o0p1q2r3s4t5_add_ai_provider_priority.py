"""Add governed AI provider priority for deterministic failover."""
from alembic import op
import sqlalchemy as sa

revision = "o0p1q2r3s4t5"
down_revision = "n9o0p1q2r3s4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_providers",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
    )
    op.alter_column("ai_providers", "priority", server_default=None)


def downgrade() -> None:
    op.drop_column("ai_providers", "priority")
