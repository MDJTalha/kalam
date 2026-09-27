"""add assessment grading controls

Revision ID: 8a4d1e6c9b72
Revises: 7f2c9a1d4e6b
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a4d1e6c9b72"
down_revision: Union[str, Sequence[str], None] = "7f2c9a1d4e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assessment_attempts",
        sa.Column("graded_by", sa.UUID(), nullable=True),
    )
    op.add_column(
        "assessment_attempts",
        sa.Column("grade_override", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "assessment_attempts",
        sa.Column("grade_override_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_assessment_attempts_graded_by",
        "assessment_attempts",
        ["graded_by"],
    )
    op.create_foreign_key(
        "fk_assessment_attempts_graded_by",
        "assessment_attempts",
        "users",
        ["graded_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_assessment_attempts_graded_by",
        "assessment_attempts",
        type_="foreignkey",
    )
    op.drop_index("ix_assessment_attempts_graded_by", table_name="assessment_attempts")
    op.drop_column("assessment_attempts", "grade_override_reason")
    op.drop_column("assessment_attempts", "grade_override")
    op.drop_column("assessment_attempts", "graded_by")
