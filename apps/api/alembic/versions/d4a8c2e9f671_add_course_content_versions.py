"""add course content version history

Revision ID: d4a8c2e9f671
Revises: c6d1e8f4a902
Create Date: 2026-09-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4a8c2e9f671"
down_revision: Union[str, Sequence[str], None] = "c6d1e8f4a902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_content_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "version_number", name="uq_course_content_version"),
    )
    op.create_index(
        "ix_course_content_versions_tenant_id",
        "course_content_versions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_course_content_versions_lesson_id",
        "course_content_versions",
        ["lesson_id"],
    )
    op.create_index(
        "ix_course_content_versions_changed_by",
        "course_content_versions",
        ["changed_by"],
    )


def downgrade() -> None:
    op.drop_index("ix_course_content_versions_changed_by", table_name="course_content_versions")
    op.drop_index("ix_course_content_versions_lesson_id", table_name="course_content_versions")
    op.drop_index("ix_course_content_versions_tenant_id", table_name="course_content_versions")
    op.drop_table("course_content_versions")
