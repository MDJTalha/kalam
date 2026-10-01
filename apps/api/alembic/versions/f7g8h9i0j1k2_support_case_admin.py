"""Extend support cases for administration."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7g8h9i0j1k2"
down_revision = "e6f7g8h9i0j1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("support_cases", sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("support_cases", sa.Column("internal_note", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_support_cases_assigned_to_user_id_users",
        "support_cases", "users", ["assigned_to_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_support_cases_assigned_status", "support_cases", ["assigned_to_user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_support_cases_assigned_status", table_name="support_cases")
    op.drop_constraint("fk_support_cases_assigned_to_user_id_users", "support_cases", type_="foreignkey")
    op.drop_column("support_cases", "internal_note")
    op.drop_column("support_cases", "assigned_to_user_id")
