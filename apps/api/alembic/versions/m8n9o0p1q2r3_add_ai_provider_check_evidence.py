"""Add AI provider connection-check evidence."""
from alembic import op
import sqlalchemy as sa

revision = "m8n9o0p1q2r3"
down_revision = "l7m8n9o0p1q2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_providers", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ai_providers", sa.Column("last_check_status", sa.String(30), nullable=True))
    op.add_column("ai_providers", sa.Column("last_check_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_providers", "last_check_message")
    op.drop_column("ai_providers", "last_check_status")
    op.drop_column("ai_providers", "last_checked_at")
