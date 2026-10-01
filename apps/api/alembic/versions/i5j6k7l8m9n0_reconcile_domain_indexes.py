"""Reconcile ORM index metadata with the database schema."""

from alembic import op


revision = "i5j6k7l8m9n0"
down_revision = "h9i0j1k2l3m4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_ai_prompt_templates_created_by", "ai_prompt_templates", ["created_by"])
    op.create_index("ix_crm_accounts_managed_tenant_id", "crm_accounts", ["managed_tenant_id"])
    op.create_index("ix_crm_accounts_owner_user_id", "crm_accounts", ["owner_user_id"])
    op.create_index("ix_crm_accounts_plan_id", "crm_accounts", ["plan_id"])
    op.create_index("ix_crm_opportunities_owner_user_id", "crm_opportunities", ["owner_user_id"])
    op.create_index("ix_crm_sales_activities_actor_user_id", "crm_sales_activities", ["actor_user_id"])
    op.create_index("ix_crm_subscriptions_managed_tenant_id", "crm_subscriptions", ["managed_tenant_id"])
    op.create_index("ix_crm_subscriptions_offer_id", "crm_subscriptions", ["offer_id"])
    op.create_index("ix_crm_subscriptions_plan_id", "crm_subscriptions", ["plan_id"])
    op.create_index("ix_crm_trials_plan_id", "crm_trials", ["plan_id"])
    op.create_index("ix_saas_offers_plan_id", "saas_offers", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_saas_offers_plan_id", table_name="saas_offers")
    op.drop_index("ix_crm_trials_plan_id", table_name="crm_trials")
    op.drop_index("ix_crm_subscriptions_plan_id", table_name="crm_subscriptions")
    op.drop_index("ix_crm_subscriptions_offer_id", table_name="crm_subscriptions")
    op.drop_index("ix_crm_subscriptions_managed_tenant_id", table_name="crm_subscriptions")
    op.drop_index("ix_crm_sales_activities_actor_user_id", table_name="crm_sales_activities")
    op.drop_index("ix_crm_opportunities_owner_user_id", table_name="crm_opportunities")
    op.drop_index("ix_crm_accounts_plan_id", table_name="crm_accounts")
    op.drop_index("ix_crm_accounts_owner_user_id", table_name="crm_accounts")
    op.drop_index("ix_crm_accounts_managed_tenant_id", table_name="crm_accounts")
    op.drop_index("ix_ai_prompt_templates_created_by", table_name="ai_prompt_templates")
