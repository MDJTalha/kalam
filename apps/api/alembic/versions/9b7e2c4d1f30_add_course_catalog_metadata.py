"""add course catalog metadata

Revision ID: 9b7e2c4d1f30
Revises: 8a4d1e6c9b72
Create Date: 2026-09-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9b7e2c4d1f30"
down_revision: Union[str, Sequence[str], None] = "8a4d1e6c9b72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_course_category_tenant_name"),
    )
    op.create_index("ix_course_categories_tenant_id", "course_categories", ["tenant_id"])
    op.add_column("courses", sa.Column("category_id", sa.UUID(), nullable=True))
    op.add_column("courses", sa.Column("owner_id", sa.UUID(), nullable=True))
    op.add_column("courses", sa.Column("visibility", sa.String(length=30), nullable=False, server_default="tenant"))
    op.add_column("courses", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("courses", sa.Column("prerequisites", sa.JSON(), nullable=False, server_default="[]"))
    op.create_index("ix_courses_category_id", "courses", ["category_id"])
    op.create_index("ix_courses_owner_id", "courses", ["owner_id"])
    op.create_foreign_key("fk_courses_category_id", "courses", "course_categories", ["category_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_courses_owner_id", "courses", "users", ["owner_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_courses_owner_id", "courses", type_="foreignkey")
    op.drop_constraint("fk_courses_category_id", "courses", type_="foreignkey")
    op.drop_index("ix_courses_owner_id", table_name="courses")
    op.drop_index("ix_courses_category_id", table_name="courses")
    op.drop_column("courses", "prerequisites")
    op.drop_column("courses", "tags")
    op.drop_column("courses", "visibility")
    op.drop_column("courses", "owner_id")
    op.drop_column("courses", "category_id")
    op.drop_index("ix_course_categories_tenant_id", table_name="course_categories")
    op.drop_table("course_categories")
