"""add notification dedupe key

Revision ID: a4c7d9e2b651
Revises: 9b7e2c4d1f30
Create Date: 2026-09-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a4c7d9e2b651"
down_revision: Union[str, Sequence[str], None] = "9b7e2c4d1f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("dedupe_key", sa.String(length=240), nullable=True))
    op.create_index("ix_notifications_dedupe_key", "notifications", ["dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_notifications_dedupe_key", table_name="notifications")
    op.drop_column("notifications", "dedupe_key")
