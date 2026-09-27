"""add assessment attempt feedback

Revision ID: 7f2c9a1d4e6b
Revises: 26990a2c5326
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f2c9a1d4e6b"
down_revision: Union[str, Sequence[str], None] = "26990a2c5326"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assessment_attempts",
        sa.Column("feedback", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assessment_attempts", "feedback")
