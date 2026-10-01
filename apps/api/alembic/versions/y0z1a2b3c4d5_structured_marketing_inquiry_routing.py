"""Add structured marketing inquiry routing fields."""

from alembic import op
import sqlalchemy as sa

revision = "y0z1a2b3c4d5"
down_revision = "x9y0z1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketing_inquiries", sa.Column("request_type", sa.String(30), nullable=False, server_default="demo"))
    op.add_column("marketing_inquiries", sa.Column("plan_code", sa.String(80), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("source", sa.String(120), nullable=False, server_default="website"))
    op.create_index("ix_marketing_inquiries_request_type", "marketing_inquiries", ["request_type"])
    op.create_index("ix_marketing_inquiries_plan_code", "marketing_inquiries", ["plan_code"])


def downgrade() -> None:
    op.drop_index("ix_marketing_inquiries_plan_code", table_name="marketing_inquiries")
    op.drop_index("ix_marketing_inquiries_request_type", table_name="marketing_inquiries")
    op.drop_column("marketing_inquiries", "source")
    op.drop_column("marketing_inquiries", "plan_code")
    op.drop_column("marketing_inquiries", "request_type")
