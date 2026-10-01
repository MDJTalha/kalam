from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "ee55ff66aa77"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("capability_assessments.read", "Read capability assessment cycles and outcomes"),
    ("capability_assessments.manage", "Manage capability assessment instruments and cycles"),
    ("capability_assessments.execute", "Execute assigned capability assessments"),
    ("reassessment.manage", "Manage capability reassessment lifecycle"),
)

def upgrade() -> None:
    op.add_column("assessments", sa.Column("assessment_type", sa.String(40), nullable=False, server_default="knowledge_test"))
    op.add_column("assessments", sa.Column("measurement_method", sa.String(40), nullable=False, server_default="score_based"))
    op.add_column("assessments", sa.Column("validity_days", sa.Integer(), nullable=True))
    op.add_column("assessments", sa.Column("reassessment_interval_days", sa.Integer(), nullable=True))
    op.add_column("assessments", sa.Column("instructions", sa.Text(), nullable=True))
    op.add_column("assessments", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("assessment_attempts", sa.Column("cycle_id", sa.UUID(), nullable=True))
    op.add_column("assessment_attempts", sa.Column("stage", sa.String(20), nullable=False, server_default="standalone"))
    op.add_column("assessment_attempts", sa.Column("demonstrated_level", sa.Numeric(4, 2), nullable=True))
    op.add_column("assessment_attempts", sa.Column("confidence", sa.Integer(), nullable=True))
    op.add_column("assessment_attempts", sa.Column("assessor_id", sa.UUID(), nullable=True))
    op.add_column("assessment_attempts", sa.Column("assessment_method", sa.String(40), nullable=False, server_default="score_based"))
    op.add_column("assessment_attempts", sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("capability_evidence", "demonstrated_level", existing_type=sa.Integer(), type_=sa.Numeric(4, 2), existing_nullable=False)

    op.create_table(
        "assessment_targets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("assessment_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("target_level", sa.Numeric(4, 2), nullable=False, server_default="3.00"),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "target_type", "target_id", name="uq_assessment_target"),
        sa.CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_target_type"),
        sa.CheckConstraint("target_level >= 1 AND target_level <= 5", name="ck_assessment_target_level"),
        sa.CheckConstraint("weight >= 1 AND weight <= 100", name="ck_assessment_target_weight"),
    )
    op.create_index("ix_assessment_targets_tenant_assessment", "assessment_targets", ["tenant_id", "assessment_id"])
    op.create_index("ix_assessment_targets_target", "assessment_targets", ["tenant_id", "target_type", "target_id"])
    op.create_table(
        "assessment_cycles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("assessment_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("required_level", sa.Numeric(4, 2), nullable=False),
        sa.Column("baseline_level", sa.Numeric(4, 2), nullable=True),
        sa.Column("current_level", sa.Numeric(4, 2), nullable=True),
        sa.Column("baseline_attempt_id", sa.UUID(), nullable=True),
        sa.Column("latest_attempt_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="baseline_due"),
        sa.Column("next_reassessment_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("development_plan_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["development_plan_id"], ["development_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_cycle_target_type"),
        sa.CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_assessment_cycle_required_level"),
        sa.CheckConstraint("baseline_level IS NULL OR (baseline_level >= 1 AND baseline_level <= 5)", name="ck_assessment_cycle_baseline_level"),
        sa.CheckConstraint("current_level IS NULL OR (current_level >= 1 AND current_level <= 5)", name="ck_assessment_cycle_current_level"),
    )
    op.create_index("ix_assessment_cycles_tenant_user", "assessment_cycles", ["tenant_id", "user_id"])
    op.create_index("ix_assessment_cycles_target", "assessment_cycles", ["tenant_id", "target_type", "target_id"])
    op.create_index("ix_assessment_cycles_status_due", "assessment_cycles", ["tenant_id", "status", "next_reassessment_due_at"])
    op.create_index("ix_assessment_cycles_baseline_attempt", "assessment_cycles", ["baseline_attempt_id"])
    op.create_index("ix_assessment_cycles_latest_attempt", "assessment_cycles", ["latest_attempt_id"])
    op.create_index("ix_assessment_cycles_development_plan", "assessment_cycles", ["development_plan_id"])
    op.create_table(
        "assessment_reviewer_assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("cycle_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="assigned"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cycle_id"], ["assessment_cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cycle_id", "reviewer_id", name="uq_assessment_cycle_reviewer"),
        sa.CheckConstraint("reviewer_type IN ('self','manager','assessor','peer')", name="ck_assessment_reviewer_type"),
    )
    op.create_index("ix_assessment_reviewer_assignments_tenant_cycle", "assessment_reviewer_assignments", ["tenant_id", "cycle_id"])

    op.create_table(
        "assessment_outcomes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("demonstrated_level", sa.Numeric(4, 2), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("evidence_reference", sa.String(1000), nullable=True),
        sa.Column("assessor_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attempt_id"], ["assessment_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "target_type", "target_id", name="uq_assessment_outcome_target"),
        sa.CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_outcome_target_type"),
        sa.CheckConstraint("demonstrated_level >= 1 AND demonstrated_level <= 5", name="ck_assessment_outcome_level"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_assessment_outcome_confidence"),
    )
    op.create_index("ix_assessment_outcomes_tenant_target", "assessment_outcomes", ["tenant_id", "target_type", "target_id"])
    op.create_foreign_key(
        "fk_assessment_attempt_cycle", "assessment_attempts", "assessment_cycles", ["cycle_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_assessment_attempt_assessor", "assessment_attempts", "users", ["assessor_id"], ["id"], ondelete="SET NULL"
    )

    conn = op.get_bind()
    for key, description in PERMISSIONS:
        conn.execute(sa.text("""
            INSERT INTO permissions (id, key, description)
            SELECT gen_random_uuid(), CAST(:key AS varchar), CAST(:description AS text)
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key = CAST(:key AS varchar))
        """), {"key": key, "description": description})

    role_permissions = {
        "Tenant Owner": ["capability_assessments.read","capability_assessments.manage","capability_assessments.execute","reassessment.manage"],
        "Tenant Administrator": ["capability_assessments.read","capability_assessments.manage","capability_assessments.execute","reassessment.manage"],
        "L&D Administrator": ["capability_assessments.read","capability_assessments.manage","capability_assessments.execute","reassessment.manage"],
        "HR / People Administrator": ["capability_assessments.read","capability_assessments.execute","reassessment.manage"],
        "Manager": ["capability_assessments.read","capability_assessments.execute"],
        "Learner / Employee": ["capability_assessments.read","capability_assessments.execute"],
        "Instructor": ["capability_assessments.execute"],
    }
    for role_name, keys in role_permissions.items():
        for key in keys:
            conn.execute(sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r JOIN permissions p ON p.key = :key
                WHERE r.name = :role_name
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions rp
                    WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  )
            """), {"role_name": role_name, "key": key})
def downgrade() -> None:
    conn = op.get_bind()
    for key, _ in PERMISSIONS:
        conn.execute(sa.text("""
            DELETE FROM role_permissions rp
            USING permissions p
            WHERE rp.permission_id = p.id AND p.key = :key
        """), {"key": key})
        conn.execute(sa.text("DELETE FROM permissions WHERE key = :key"), {"key": key})

    op.drop_constraint("fk_assessment_attempt_assessor", "assessment_attempts", type_="foreignkey")
    op.drop_constraint("fk_assessment_attempt_cycle", "assessment_attempts", type_="foreignkey")
    op.drop_index("ix_assessment_outcomes_tenant_target", table_name="assessment_outcomes")
    op.drop_table("assessment_outcomes")
    op.drop_index("ix_assessment_reviewer_assignments_tenant_cycle", table_name="assessment_reviewer_assignments")
    op.drop_table("assessment_reviewer_assignments")
    op.drop_index("ix_assessment_cycles_development_plan", table_name="assessment_cycles")
    op.drop_index("ix_assessment_cycles_latest_attempt", table_name="assessment_cycles")
    op.drop_index("ix_assessment_cycles_baseline_attempt", table_name="assessment_cycles")
    op.drop_index("ix_assessment_cycles_status_due", table_name="assessment_cycles")
    op.drop_index("ix_assessment_cycles_target", table_name="assessment_cycles")
    op.drop_index("ix_assessment_cycles_tenant_user", table_name="assessment_cycles")
    op.drop_table("assessment_cycles")
    op.drop_index("ix_assessment_targets_target", table_name="assessment_targets")
    op.drop_index("ix_assessment_targets_tenant_assessment", table_name="assessment_targets")
    op.drop_table("assessment_targets")
    op.drop_column("assessment_attempts", "valid_until")
    op.drop_column("assessment_attempts", "assessment_method")
    op.drop_column("assessment_attempts", "assessor_id")
    op.drop_column("assessment_attempts", "confidence")
    op.drop_column("assessment_attempts", "demonstrated_level")
    op.drop_column("assessment_attempts", "stage")
    op.drop_column("assessment_attempts", "cycle_id")
    op.alter_column("capability_evidence", "demonstrated_level", existing_type=sa.Numeric(4,2), type_=sa.Integer(), existing_nullable=False)
    op.drop_column("assessments", "active")
    op.drop_column("assessments", "instructions")
    op.drop_column("assessments", "reassessment_interval_days")
    op.drop_column("assessments", "validity_days")
    op.drop_column("assessments", "measurement_method")
    op.drop_column("assessments", "assessment_type")
