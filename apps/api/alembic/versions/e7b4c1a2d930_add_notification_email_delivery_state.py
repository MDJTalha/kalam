"""add notification email delivery state

Revision ID: e7b4c1a2d930
Revises: d4a8c2e9f671
Create Date: 2026-09-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e7b4c1a2d930"
down_revision: Union[str, Sequence[str], None] = "d4a8c2e9f671"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_notifications_email_sent_at", "notifications", ["email_sent_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_email_sent_at", table_name="notifications")
    op.drop_column("notifications", "email_sent_at")
