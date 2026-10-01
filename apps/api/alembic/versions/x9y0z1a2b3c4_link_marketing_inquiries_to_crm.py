"""Link marketing inquiries to CRM conversions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "x9y0z1a2b3c4"
down_revision = "w8x9y0z1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketing_inquiries", sa.Column("crm_account_id", UUID(as_uuid=True), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_marketing_inquiries_crm_account_id",
        "marketing_inquiries",
        "crm_accounts",
        ["crm_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_marketing_inquiries_crm_account_id", "marketing_inquiries", ["crm_account_id"])


def downgrade() -> None:
    op.drop_index("ix_marketing_inquiries_crm_account_id", table_name="marketing_inquiries")
    op.drop_constraint("fk_marketing_inquiries_crm_account_id", "marketing_inquiries", type_="foreignkey")
    op.drop_column("marketing_inquiries", "converted_at")
    op.drop_column("marketing_inquiries", "crm_account_id")
