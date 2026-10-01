"""Add SaaS customer onboarding workflow."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "z1a2b3c4d5e6"
down_revision = "y0z1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crm_onboarding_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("managed_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL")),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("category", sa.String(50), server_default="general", nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_onboarding_items_ops_tenant_id", "crm_onboarding_items", ["ops_tenant_id"])
    op.create_index("ix_crm_onboarding_items_account_id", "crm_onboarding_items", ["account_id"])
    op.create_index("ix_crm_onboarding_items_managed_tenant_id", "crm_onboarding_items", ["managed_tenant_id"])
    op.create_index("ix_crm_onboarding_items_owner_user_id", "crm_onboarding_items", ["owner_user_id"])
    op.create_index("ix_crm_onboarding_items_category", "crm_onboarding_items", ["category"])
    op.create_index("ix_crm_onboarding_items_status", "crm_onboarding_items", ["status"])


def downgrade() -> None:
    op.drop_table("crm_onboarding_items")
