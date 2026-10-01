"""Extend notifications with enterprise metadata."""

from alembic import op
import sqlalchemy as sa

revision = "h9i0j1k2l3m4"
down_revision = "g8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("category", sa.String(length=32), nullable=False, server_default="system"))
    op.add_column("notifications", sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"))
    op.add_column("notifications", sa.Column("action_href", sa.String(length=320), nullable=True))
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "read_at", "created_at"])
    op.create_index("ix_notifications_user_category", "notifications", ["user_id", "category"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_category", table_name="notifications")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_column("notifications", "action_href")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "category")
