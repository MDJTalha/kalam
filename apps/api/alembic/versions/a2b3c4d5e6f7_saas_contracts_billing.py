"""Add SaaS contracts, invoices and payments."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "a2b3c4d5e6f7"
down_revision = "z1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crm_contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", UUID(as_uuid=True), sa.ForeignKey("crm_subscriptions.id", ondelete="SET NULL")),
        sa.Column("reference", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("total_value_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("signed_at", sa.DateTime(timezone=True)),
        sa.Column("renewal_terms", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "reference", name="uq_crm_contract_ops_reference"),
    )
    op.create_index("ix_crm_contracts_ops_tenant_id", "crm_contracts", ["ops_tenant_id"])
    op.create_index("ix_crm_contracts_account_id", "crm_contracts", ["account_id"])
    op.create_index("ix_crm_contracts_subscription_id", "crm_contracts", ["subscription_id"])
    op.create_index("ix_crm_contracts_status", "crm_contracts", ["status"])

    op.create_table(
        "crm_invoices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", UUID(as_uuid=True), sa.ForeignKey("crm_subscriptions.id", ondelete="SET NULL")),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("crm_contracts.id", ondelete="SET NULL")),
        sa.Column("invoice_number", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("amount_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tax_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("external_ref", sa.String(180)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "invoice_number", name="uq_crm_invoice_ops_number"),
    )
    op.create_index("ix_crm_invoices_ops_tenant_id", "crm_invoices", ["ops_tenant_id"])
    op.create_index("ix_crm_invoices_account_id", "crm_invoices", ["account_id"])
    op.create_index("ix_crm_invoices_subscription_id", "crm_invoices", ["subscription_id"])
    op.create_index("ix_crm_invoices_contract_id", "crm_invoices", ["contract_id"])
    op.create_index("ix_crm_invoices_status", "crm_invoices", ["status"])
    op.create_index("ix_crm_invoices_due_at", "crm_invoices", ["due_at"])

    op.create_table(
        "crm_payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", UUID(as_uuid=True), sa.ForeignKey("crm_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(30), server_default="received", nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("method", sa.String(60)),
        sa.Column("reference", sa.String(180)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_payments_ops_tenant_id", "crm_payments", ["ops_tenant_id"])
    op.create_index("ix_crm_payments_account_id", "crm_payments", ["account_id"])
    op.create_index("ix_crm_payments_invoice_id", "crm_payments", ["invoice_id"])
    op.create_index("ix_crm_payments_status", "crm_payments", ["status"])


def downgrade() -> None:
    op.drop_table("crm_payments")
    op.drop_table("crm_invoices")
    op.drop_table("crm_contracts")
