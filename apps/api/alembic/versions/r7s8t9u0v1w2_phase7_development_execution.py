from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "r7s8t9u0v1w2"
down_revision = "h5i6j7k8l9m0"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("development_interventions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("development_plans.id", ondelete="SET NULL")),
        sa.Column("recommendation_id", UUID(as_uuid=True), sa.ForeignKey("development_recommendations.id", ondelete="SET NULL")),
        sa.Column("assignee_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("intervention_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_development_interventions_tenant_user_status", "development_interventions", ["tenant_id", "user_id", "status"])
    op.create_index("ix_development_interventions_assignee_status", "development_interventions", ["tenant_id", "assignee_id", "status"])
    op.create_table("development_interactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_id", UUID(as_uuid=True), sa.ForeignKey("development_interventions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("facilitator_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("interaction_type", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("action_items", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_development_interactions_intervention_created", "development_interactions", ["intervention_id", "created_at"])
    op.create_table("development_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_id", UUID(as_uuid=True), sa.ForeignKey("development_interventions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("verified_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_development_evidence_intervention_observed", "development_evidence", ["intervention_id", "observed_at"])

def downgrade():
    op.drop_index("ix_development_evidence_intervention_observed", table_name="development_evidence")
    op.drop_table("development_evidence")
    op.drop_index("ix_development_interactions_intervention_created", table_name="development_interactions")
    op.drop_table("development_interactions")
    op.drop_index("ix_development_interventions_assignee_status", table_name="development_interventions")
    op.drop_index("ix_development_interventions_tenant_user_status", table_name="development_interventions")
    op.drop_table("development_interventions")
