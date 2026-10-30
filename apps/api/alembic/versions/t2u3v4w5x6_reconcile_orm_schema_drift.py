"""Align schema with ORM metadata without dropping established composite indexes.

Revision ID: t2u3v4w5x6
Revises: s1t2u3v4w5x6
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "t2u3v4w5x6"
down_revision = "s1t2u3v4w5x6"
branch_labels = None
depends_on = None

# The existing composite indexes are intentionally preserved. Their matching
# declarations live in app.db.models; the indexes below are the single-column
# indexes explicitly declared by the ORM but missing from the migrated schema.
INDEXES = (
    ("ix_assessment_attempts_assessor_id", "assessment_attempts", ["assessor_id"]),
    ("ix_assessment_attempts_cycle_id", "assessment_attempts", ["cycle_id"]),
    ("ix_assessment_attempts_valid_until", "assessment_attempts", ["valid_until"]),
    ("ix_assessment_cycles_assessment_id", "assessment_cycles", ["assessment_id"]),
    ("ix_assessment_cycles_baseline_attempt_id", "assessment_cycles", ["baseline_attempt_id"]),
    ("ix_assessment_cycles_development_plan_id", "assessment_cycles", ["development_plan_id"]),
    ("ix_assessment_cycles_latest_attempt_id", "assessment_cycles", ["latest_attempt_id"]),
    ("ix_assessment_cycles_next_reassessment_due_at", "assessment_cycles", ["next_reassessment_due_at"]),
    ("ix_assessment_cycles_status", "assessment_cycles", ["status"]),
    ("ix_assessment_cycles_target_id", "assessment_cycles", ["target_id"]),
    ("ix_assessment_cycles_tenant_id", "assessment_cycles", ["tenant_id"]),
    ("ix_assessment_cycles_user_id", "assessment_cycles", ["user_id"]),
    ("ix_assessment_outcomes_assessor_id", "assessment_outcomes", ["assessor_id"]),
    ("ix_assessment_outcomes_attempt_id", "assessment_outcomes", ["attempt_id"]),
    ("ix_assessment_outcomes_target_id", "assessment_outcomes", ["target_id"]),
    ("ix_assessment_outcomes_tenant_id", "assessment_outcomes", ["tenant_id"]),
    ("ix_assessment_reviewer_assignments_cycle_id", "assessment_reviewer_assignments", ["cycle_id"]),
    ("ix_assessment_reviewer_assignments_reviewer_id", "assessment_reviewer_assignments", ["reviewer_id"]),
    ("ix_assessment_reviewer_assignments_tenant_id", "assessment_reviewer_assignments", ["tenant_id"]),
    ("ix_assessment_targets_assessment_id", "assessment_targets", ["assessment_id"]),
    ("ix_assessment_targets_target_id", "assessment_targets", ["target_id"]),
    ("ix_assessment_targets_tenant_id", "assessment_targets", ["tenant_id"]),
    ("ix_capability_evidence_assessor_id", "capability_evidence", ["assessor_id"]),
    ("ix_capability_evidence_target_id", "capability_evidence", ["target_id"]),
    ("ix_capability_evidence_tenant_id", "capability_evidence", ["tenant_id"]),
    ("ix_capability_evidence_user_id", "capability_evidence", ["user_id"]),
    ("ix_capability_evidence_verified_by", "capability_evidence", ["verified_by"]),
    ("ix_capability_gaps_role_requirement_id", "capability_gaps", ["role_requirement_id"]),
    ("ix_capability_gaps_target_id", "capability_gaps", ["target_id"]),
    ("ix_capability_gaps_tenant_id", "capability_gaps", ["tenant_id"]),
    ("ix_capability_gaps_user_id", "capability_gaps", ["user_id"]),
    ("ix_capability_risks_capability_id", "capability_risks", ["capability_id"]),
    ("ix_capability_risks_tenant_id", "capability_risks", ["tenant_id"]),
    ("ix_development_evidence_intervention_id", "development_evidence", ["intervention_id"]),
    ("ix_development_evidence_tenant_id", "development_evidence", ["tenant_id"]),
    ("ix_development_interactions_intervention_id", "development_interactions", ["intervention_id"]),
    ("ix_development_interactions_tenant_id", "development_interactions", ["tenant_id"]),
    ("ix_development_interventions_assignee_id", "development_interventions", ["assignee_id"]),
    ("ix_development_interventions_plan_id", "development_interventions", ["plan_id"]),
    ("ix_development_interventions_recommendation_id", "development_interventions", ["recommendation_id"]),
    ("ix_development_interventions_tenant_id", "development_interventions", ["tenant_id"]),
    ("ix_development_interventions_user_id", "development_interventions", ["user_id"]),
    ("ix_development_recommendations_capability_gap_id", "development_recommendations", ["capability_gap_id"]),
    ("ix_development_recommendations_tenant_id", "development_recommendations", ["tenant_id"]),
    ("ix_development_recommendations_user_id", "development_recommendations", ["user_id"]),
)

JSONB_COLUMNS = (
    ("capability_evidence", "record_metadata"),
    ("capability_risks", "explanation"),
    ("development_evidence", "metadata_json"),
    ("development_interactions", "action_items"),
    ("development_interventions", "metadata_json"),
    ("development_recommendations", "metadata_json"),
)


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns, unique=False)

    for table, column in JSONB_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=postgresql.JSON(astext_type=sa.Text()),
            type_=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=False,
            postgresql_using=f'"{column}"::jsonb',
        )


def downgrade() -> None:
    for table, column in reversed(JSONB_COLUMNS):
        op.alter_column(
            table,
            column,
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            type_=postgresql.JSON(astext_type=sa.Text()),
            existing_nullable=False,
            postgresql_using=f'"{column}"::json',
        )
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)
