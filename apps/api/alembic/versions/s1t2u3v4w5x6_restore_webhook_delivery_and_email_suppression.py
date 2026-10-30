"""Restore durable webhook delivery state and track suppressed notification email."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "s1t2u3v4w5x6"
down_revision = "k1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhook_endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("webhook_id", "notification_id", name="uq_webhook_delivery_notification"),
    )
    op.create_index("ix_webhook_deliveries_status_next", "webhook_deliveries", ["status", "next_attempt_at"])
    op.add_column(
        "notifications",
        sa.Column("email_suppressed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_email_suppressed_at", "notifications", ["email_suppressed_at"])
    op.add_column(
        "notifications",
        sa.Column("email_failed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_email_failed_at", "notifications", ["email_failed_at"])
    op.add_column(
        "notifications",
        sa.Column("email_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "notifications",
        sa.Column("email_next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_email_next_attempt_at", "notifications", ["email_next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_email_next_attempt_at", table_name="notifications")
    op.drop_column("notifications", "email_next_attempt_at")
    op.drop_column("notifications", "email_attempts")
    op.drop_index("ix_notifications_email_failed_at", table_name="notifications")
    op.drop_column("notifications", "email_failed_at")
    op.drop_index("ix_notifications_email_suppressed_at", table_name="notifications")
    op.drop_column("notifications", "email_suppressed_at")
    op.drop_index("ix_webhook_deliveries_status_next", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
