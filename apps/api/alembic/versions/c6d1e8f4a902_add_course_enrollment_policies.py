"""add course enrollment policies and audiences

Revision ID: c6d1e8f4a902
Revises: a4c7d9e2b651
Create Date: 2026-09-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c6d1e8f4a902"
down_revision: Union[str, Sequence[str], None] = "a4c7d9e2b651"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("enrollment_policy", sa.String(length=30), nullable=False, server_default="open"),
    )
    op.add_column("courses", sa.Column("capacity", sa.Integer(), nullable=True))
    op.add_column(
        "courses",
        sa.Column("audience_org_units", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_courses_enrollment_policy", "courses", ["enrollment_policy"])


def downgrade() -> None:
    op.drop_index("ix_courses_enrollment_policy", table_name="courses")
    op.drop_column("courses", "audience_org_units")
    op.drop_column("courses", "capacity")
    op.drop_column("courses", "enrollment_policy")
