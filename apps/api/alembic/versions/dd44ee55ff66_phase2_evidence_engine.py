from alembic import op
import sqlalchemy as sa

revision = "dd44ee55ff66"
down_revision = "cc33dd44ee55"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("evidence.read", "Read capability evidence"),
    ("evidence.manage", "Create capability evidence"),
    ("evidence.verify", "Verify or reject capability evidence"),
)

def upgrade() -> None:
    op.create_table(
        "capability_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("evidence_type", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.String(length=160), nullable=True),
        sa.Column("demonstrated_level", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessor_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("record_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("verified_by", sa.UUID(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("demonstrated_level >= 1 AND demonstrated_level <= 5", name="ck_capability_evidence_level"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_capability_evidence_confidence"),
    )
    op.create_index("ix_capability_evidence_tenant_user", "capability_evidence", ["tenant_id", "user_id"])
    op.create_index("ix_capability_evidence_target", "capability_evidence", ["tenant_id", "target_type", "target_id"])

    op.create_table(
        "assessment_competencies",
        sa.Column("assessment_id", sa.UUID(), nullable=False),
        sa.Column("competency_id", sa.UUID(), nullable=False),
        sa.Column("target_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("assessment_id", "competency_id"),
        sa.UniqueConstraint("assessment_id", "competency_id", name="uq_assessment_competency"),
        sa.CheckConstraint("target_level >= 1 AND target_level <= 5", name="ck_assessment_competency_target_level"),
    )

    conn = op.get_bind()
    for key, description in PERMISSIONS:
        conn.execute(sa.text("""
            INSERT INTO permissions (id, key, description)
            SELECT gen_random_uuid(), CAST(:key AS varchar), CAST(:description AS text)
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key = CAST(:key AS varchar))
        """), {"key": key, "description": description})
        conn.execute(sa.text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r CROSS JOIN permissions p
            WHERE r.name IN ('Tenant Owner', 'Tenant Administrator', 'Platform Developer')
              AND p.key = :key
              AND NOT EXISTS (
                SELECT 1 FROM role_permissions rp
                WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
        """), {"key": key})

def downgrade() -> None:
    conn = op.get_bind()
    for key, _ in PERMISSIONS:
        conn.execute(sa.text("""
            DELETE FROM role_permissions rp USING permissions p
            WHERE rp.permission_id = p.id AND p.key = :key
        """), {"key": key})
        conn.execute(sa.text("DELETE FROM permissions WHERE key = :key"), {"key": key})
    op.drop_table("assessment_competencies")
    op.drop_index("ix_capability_evidence_target", table_name="capability_evidence")
    op.drop_index("ix_capability_evidence_tenant_user", table_name="capability_evidence")
    op.drop_table("capability_evidence")

