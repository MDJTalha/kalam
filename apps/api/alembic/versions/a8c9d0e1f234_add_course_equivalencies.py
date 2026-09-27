"""add tenant-scoped course equivalencies

Revision ID: a8c9d0e1f234
Revises: b7d4e8f1a2c3
"""

from alembic import op
import sqlalchemy as sa

revision = "a8c9d0e1f234"
down_revision = "b7d4e8f1a2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_equivalencies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("equivalent_course_id", sa.UUID(), nullable=False),
        sa.Column("equivalency_type", sa.String(length=40), nullable=False, server_default="full"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equivalent_course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "course_id", "equivalent_course_id", name="uq_course_equivalency_tenant_pair"),
        sa.CheckConstraint("course_id <> equivalent_course_id", name="ck_course_equivalency_distinct_courses"),
    )
    op.create_index("ix_course_equivalencies_tenant_id", "course_equivalencies", ["tenant_id"])
    op.create_index("ix_course_equivalencies_course_id", "course_equivalencies", ["course_id"])
    op.create_index("ix_course_equivalencies_equivalent_course_id", "course_equivalencies", ["equivalent_course_id"])


def downgrade() -> None:
    op.drop_index("ix_course_equivalencies_equivalent_course_id", table_name="course_equivalencies")
    op.drop_index("ix_course_equivalencies_course_id", table_name="course_equivalencies")
    op.drop_index("ix_course_equivalencies_tenant_id", table_name="course_equivalencies")
    op.drop_table("course_equivalencies")
