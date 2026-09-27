"""Create a separate public inquiry queue for the Kognivon team."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "u6v7w8x9y0z1"
down_revision = "t5u6v7w8x9y0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketing_inquiries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("work_email", sa.String(320), nullable=False),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("job_title", sa.String(160), nullable=True),
        sa.Column("message", sa.String(1200), nullable=True),
        sa.Column("status", sa.String(24), server_default="new", nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('new', 'contacted', 'closed')", name="ck_marketing_inquiry_status"),
    )
    op.create_index("ix_marketing_inquiries_work_email", "marketing_inquiries", ["work_email"])
    op.create_index("ix_marketing_inquiries_status", "marketing_inquiries", ["status"])
    op.create_index("ix_marketing_inquiries_created_at", "marketing_inquiries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_marketing_inquiries_created_at", table_name="marketing_inquiries")
    op.drop_index("ix_marketing_inquiries_status", table_name="marketing_inquiries")
    op.drop_index("ix_marketing_inquiries_work_email", table_name="marketing_inquiries")
    op.drop_table("marketing_inquiries")
