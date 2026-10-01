"""Add support case conversation history."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g8h9i0j1k2l3"
down_revision = "f7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_case_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="requester"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["support_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_case_messages_case_created", "support_case_messages", ["case_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_support_case_messages_case_created", table_name="support_case_messages")
    op.drop_table("support_case_messages")
