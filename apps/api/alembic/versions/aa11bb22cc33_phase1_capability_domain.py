"""Phase 1 capability domain model: strategy, competencies and governed role requirements."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "aa11bb22cc33"
down_revision = "n3o4p5q6r7s8"
branch_labels = None
depends_on = "c2d3e4f5a6b7"


def upgrade() -> None:
    op.create_table(
        "proficiency_levels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.UniqueConstraint("tenant_id", "level", name="uq_proficiency_level_tenant_level"),
        sa.CheckConstraint("level >= 1 AND level <= 5", name="ck_proficiency_level_range"),
    )
    op.create_index("ix_proficiency_levels_tenant_id", "proficiency_levels", ["tenant_id"])

    op.create_table(
        "strategic_objectives",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("business_unit_id", UUID(as_uuid=True), sa.ForeignKey("org_units.id", ondelete="SET NULL")),
        sa.Column("objective", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("strategic_category", sa.String(120)),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "objective", name="uq_strategic_objective_tenant_name"),
        sa.CheckConstraint("priority >= 1 AND priority <= 5", name="ck_strategic_objective_priority"),
    )
    op.create_index("ix_strategic_objectives_tenant_id", "strategic_objectives", ["tenant_id"])
    op.create_index("ix_strategic_objectives_owner_id", "strategic_objectives", ["owner_id"])
    op.create_index("ix_strategic_objectives_business_unit_id", "strategic_objectives", ["business_unit_id"])

    op.create_table(
        "strategic_objective_capabilities",
        sa.Column("objective_id", UUID(as_uuid=True), sa.ForeignKey("strategic_objectives.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("capability_id", UUID(as_uuid=True), sa.ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("required_level", sa.Integer(), server_default="3", nullable=False),
        sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_objective_capability_required_level"),
        sa.CheckConstraint("weight >= 1 AND weight <= 100", name="ck_objective_capability_weight"),
    )
    op.create_index("ix_objective_capabilities_capability_id", "strategic_objective_capabilities", ["capability_id"])

    op.create_table(
        "competencies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("type", sa.String(40), server_default="behavioral", nullable=False),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_competency_tenant_code"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_competency_tenant_name"),
    )
    op.create_index("ix_competencies_tenant_id", "competencies", ["tenant_id"])

    op.create_table(
        "competency_levels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("competency_id", UUID(as_uuid=True), sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("behavioral_indicators", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.UniqueConstraint("competency_id", "level", name="uq_competency_level"),
        sa.CheckConstraint("level >= 1 AND level <= 5", name="ck_competency_level_range"),
    )
    op.create_index("ix_competency_levels_competency_id", "competency_levels", ["competency_id"])

    op.create_table(
        "capability_competencies",
        sa.Column("capability_id", UUID(as_uuid=True), sa.ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competency_id", UUID(as_uuid=True), sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("weight >= 1 AND weight <= 100", name="ck_capability_competency_weight"),
    )
    op.create_index("ix_capability_competencies_competency_id", "capability_competencies", ["competency_id"])

    op.create_table(
        "role_requirements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability_id", UUID(as_uuid=True), sa.ForeignKey("capabilities.id", ondelete="CASCADE")),
        sa.Column("competency_id", UUID(as_uuid=True), sa.ForeignKey("competencies.id", ondelete="CASCADE")),
        sa.Column("skill_id", UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE")),
        sa.Column("required_level", sa.Integer(), nullable=False),
        sa.Column("criticality", sa.String(20), server_default="medium", nullable=False),
        sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "((capability_id IS NOT NULL)::int + (competency_id IS NOT NULL)::int + (skill_id IS NOT NULL)::int) = 1",
            name="ck_role_requirement_single_target",
        ),
        sa.CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_role_requirement_level"),
        sa.CheckConstraint("weight >= 1 AND weight <= 100", name="ck_role_requirement_weight"),
    )
    op.create_index("ix_role_requirements_tenant_id", "role_requirements", ["tenant_id"])
    op.create_index("ix_role_requirements_role_id", "role_requirements", ["role_id"])
    op.create_index("ix_role_requirements_capability_id", "role_requirements", ["capability_id"])
    op.create_index("ix_role_requirements_competency_id", "role_requirements", ["competency_id"])
    op.create_index("ix_role_requirements_skill_id", "role_requirements", ["skill_id"])

    op.execute("""
        INSERT INTO proficiency_levels (id, tenant_id, level, name, definition)
        SELECT gen_random_uuid(), id, v.level, v.name, v.definition
        FROM tenants
        CROSS JOIN (VALUES
            (1, 'Foundational', 'Understands the fundamentals and performs with significant guidance.'),
            (2, 'Developing', 'Applies the capability in familiar situations with limited guidance.'),
            (3, 'Proficient', 'Consistently performs the capability independently to the expected standard.'),
            (4, 'Advanced', 'Handles complex situations and improves practice for others.'),
            (5, 'Expert', 'Demonstrates deep mastery and provides authoritative leadership or expertise.')
        ) AS v(level, name, definition)
        ON CONFLICT (tenant_id, level) DO NOTHING
    """)

    op.execute("""
        INSERT INTO role_requirements
            (id, tenant_id, role_id, skill_id, required_level, criticality, weight)
        SELECT gen_random_uuid(), r.tenant_id, rs.role_id, rs.skill_id,
               rs.required_proficiency, 'medium', 1
        FROM role_skill_requirements rs
        JOIN roles r ON r.id = rs.role_id
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO permissions (id, key, description) VALUES
            (gen_random_uuid(), 'strategic_objectives.read', 'View strategic objectives'),
            (gen_random_uuid(), 'strategic_objectives.manage', 'Manage strategic objectives'),
            (gen_random_uuid(), 'competencies.read', 'View competency framework'),
            (gen_random_uuid(), 'competencies.manage', 'Manage competency framework'),
            (gen_random_uuid(), 'role_requirements.read', 'View governed role requirements'),
            (gen_random_uuid(), 'role_requirements.manage', 'Manage governed role requirements')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("role_requirements")
    op.drop_table("capability_competencies")
    op.drop_table("competency_levels")
    op.drop_table("competencies")
    op.drop_table("strategic_objective_capabilities")
    op.drop_table("strategic_objectives")
    op.drop_table("proficiency_levels")
