"""Add integration connection-check evidence fields."""
from alembic import op
import sqlalchemy as sa

revision = "k6b7c8d9e0f1"
down_revision = "j5a6b7c8d9e0"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("integrations", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("integrations", sa.Column("last_check_status", sa.String(length=30), nullable=True))
    op.add_column("integrations", sa.Column("last_check_message", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("integrations", "last_check_message")
    op.drop_column("integrations", "last_check_status")
    op.drop_column("integrations", "last_checked_at")
