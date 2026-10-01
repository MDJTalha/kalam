"""Add SaaS commercial CRM foundation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "v7w8x9y0z1a2"
down_revision = "u6v7w8x9y0z1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saas_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("tagline", sa.String(240)),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(30), server_default="active", nullable=False),
        sa.Column("public_visible", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("billing_model", sa.String(40), server_default="per_user", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("monthly_price_minor", sa.Integer()),
        sa.Column("annual_price_minor", sa.Integer()),
        sa.Column("trial_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("minimum_seats", sa.Integer(), server_default="1", nullable=False),
        sa.Column("maximum_seats", sa.Integer()),
        sa.Column("features", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("limits", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "code", name="uq_saas_plan_ops_code"),
    )
    op.create_index("ix_saas_plans_ops_tenant_id", "saas_plans", ["ops_tenant_id"])

    op.create_table(
        "saas_offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("saas_plans.id", ondelete="SET NULL")),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("discount_type", sa.String(30), server_default="percent", nullable=False),
        sa.Column("discount_value", sa.Integer(), server_default="0", nullable=False),
        sa.Column("public_visible", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "code", name="uq_saas_offer_ops_code"),
    )
    op.create_index("ix_saas_offers_ops_tenant_id", "saas_offers", ["ops_tenant_id"])

    op.create_table(
        "crm_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("managed_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL")),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("saas_plans.id", ondelete="SET NULL")),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("account_type", sa.String(30), server_default="prospect", nullable=False),
        sa.Column("lifecycle_stage", sa.String(30), server_default="lead", nullable=False),
        sa.Column("industry", sa.String(120)),
        sa.Column("country", sa.String(120)),
        sa.Column("website", sa.String(500)),
        sa.Column("employee_band", sa.String(60)),
        sa.Column("public_showcase", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("logo_url", sa.String(1000)),
        sa.Column("testimonial", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("record_metadata", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "slug", name="uq_crm_account_ops_slug"),
    )
    op.create_index("ix_crm_accounts_ops_tenant_id", "crm_accounts", ["ops_tenant_id"])
    op.create_index("ix_crm_accounts_lifecycle_stage", "crm_accounts", ["lifecycle_stage"])

    op.create_table(
        "crm_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("job_title", sa.String(180)),
        sa.Column("phone", sa.String(60)),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_contacts_ops_tenant_id", "crm_contacts", ["ops_tenant_id"])
    op.create_index("ix_crm_contacts_account_id", "crm_contacts", ["account_id"])

    op.create_table(
        "crm_trials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("saas_plans.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(30), server_default="scheduled", nullable=False),
        sa.Column("seats", sa.Integer(), server_default="25", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_trials_ops_tenant_id", "crm_trials", ["ops_tenant_id"])
    op.create_index("ix_crm_trials_account_id", "crm_trials", ["account_id"])
    op.create_index("ix_crm_trials_status", "crm_trials", ["status"])

    op.create_table(
        "crm_subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("managed_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL")),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("saas_plans.id", ondelete="SET NULL")),
        sa.Column("offer_id", UUID(as_uuid=True), sa.ForeignKey("saas_offers.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("billing_cycle", sa.String(20), server_default="annual", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("seats", sa.Integer(), server_default="1", nullable=False),
        sa.Column("list_price_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("discount_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("net_price_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("renews_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("contract_ref", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_subscriptions_ops_tenant_id", "crm_subscriptions", ["ops_tenant_id"])
    op.create_index("ix_crm_subscriptions_account_id", "crm_subscriptions", ["account_id"])
    op.create_index("ix_crm_subscriptions_status", "crm_subscriptions", ["status"])

    op.create_table(
        "crm_opportunities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("stage", sa.String(40), server_default="discovery", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("amount_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("probability_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expected_close_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_opportunities_ops_tenant_id", "crm_opportunities", ["ops_tenant_id"])
    op.create_index("ix_crm_opportunities_account_id", "crm_opportunities", ["account_id"])
    op.create_index("ix_crm_opportunities_stage", "crm_opportunities", ["stage"])

    op.create_table(
        "crm_sales_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("activity_type", sa.String(40), server_default="note", nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("happened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_sales_activities_ops_tenant_id", "crm_sales_activities", ["ops_tenant_id"])
    op.create_index("ix_crm_sales_activities_account_id", "crm_sales_activities", ["account_id"])

    op.create_table(
        "saas_certifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("issuer", sa.String(180), nullable=False),
        sa.Column("registration_number", sa.String(180)),
        sa.Column("status", sa.String(30), server_default="planned", nullable=False),
        sa.Column("public_visible", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("verification_url", sa.String(1000)),
        sa.Column("display_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_saas_certifications_ops_tenant_id", "saas_certifications", ["ops_tenant_id"])


def downgrade() -> None:
    for table in [
        "saas_certifications","crm_sales_activities","crm_opportunities","crm_subscriptions",
        "crm_trials","crm_contacts","crm_accounts","saas_offers","saas_plans",
    ]:
        op.drop_table(table)
