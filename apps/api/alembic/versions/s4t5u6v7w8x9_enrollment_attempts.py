"""Preserve completed course attempts while allowing one active attempt."""

from alembic import op
import sqlalchemy as sa

revision = "s4t5u6v7w8x9"
down_revision = "r3s4t5u6v7w8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_enrollment_tenant_course_user", "enrollments", type_="unique")
    op.create_index(
        "uq_enrollment_active_tenant_course_user", "enrollments",
        ["tenant_id", "course_id", "user_id"], unique=True,
        postgresql_where=sa.text("status NOT IN ('completed', 'rejected')"),
    )


def downgrade() -> None:
    duplicates = op.get_bind().execute(sa.text("""
        SELECT count(*) FROM (
            SELECT 1 FROM enrollments GROUP BY tenant_id, course_id, user_id HAVING count(*) > 1
        ) repeated
    """)).scalar_one()
    if duplicates:
        raise RuntimeError("Cannot restore the old enrollment uniqueness constraint while historical attempts exist")
    op.drop_index("uq_enrollment_active_tenant_course_user", table_name="enrollments")
    op.create_unique_constraint("uq_enrollment_tenant_course_user", "enrollments",
                                ["tenant_id", "course_id", "user_id"])
