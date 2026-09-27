"""Add governed AI provider, model, prompt and policy registry."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "l7m8n9o0p1q2"
down_revision = "k6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("provider_type", sa.String(40), nullable=False),
        sa.Column("endpoint_url", sa.String(1000), nullable=True),
        sa.Column("secret_ref", sa.String(160), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="disabled"),
        sa.Column("capabilities", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ai_provider_tenant_name"),
    )
    op.create_index("ix_ai_providers_tenant_id", "ai_providers", ["tenant_id"])
    op.create_table(
        "ai_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_key", sa.String(180), nullable=False),
        sa.Column("display_name", sa.String(180), nullable=False),
        sa.Column("capabilities", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("limits", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", "model_key", name="uq_ai_model_tenant_key"),
    )
    op.create_index("ix_ai_models_tenant_id", "ai_models", ["tenant_id"])
    op.create_index("ix_ai_models_provider_id", "ai_models", ["provider_id"])
    op.create_table(
        "ai_prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("purpose", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("system_template", sa.Text, nullable=False),
        sa.Column("variables", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", "name", "version", name="uq_ai_prompt_tenant_name_version"),
    )
    op.create_index("ix_ai_prompt_templates_tenant_id", "ai_prompt_templates", ["tenant_id"])
    op.create_table(
        "ai_governance_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("require_grounding", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("employment_decisioning_allowed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("raw_prompt_storage_allowed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("raw_response_storage_allowed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("max_input_chars", sa.Integer, nullable=False, server_default="4000"),
        sa.Column("max_output_tokens", sa.Integer, nullable=False, server_default="1200"),
        sa.Column("allowed_provider_types", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", name="uq_ai_policy_tenant"),
    )
    op.create_index("ix_ai_governance_policies_tenant_id", "ai_governance_policies", ["tenant_id"])
    op.execute(sa.text("""
        INSERT INTO permissions (id, key, description)
        VALUES (gen_random_uuid(), 'ai.manage', 'Manage governed AI providers, models, prompts and policies')
        ON CONFLICT (key) DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE key='ai.manage')"))
    op.execute(sa.text("DELETE FROM permissions WHERE key='ai.manage'"))
    op.drop_table("ai_governance_policies")
    op.drop_table("ai_prompt_templates")
    op.drop_table("ai_models")
    op.drop_table("ai_providers")
