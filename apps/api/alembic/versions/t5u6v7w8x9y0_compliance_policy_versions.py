"""Version compliance policy definitions and preserve assignment version."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "t5u6v7w8x9y0"
down_revision = "s4t5u6v7w8x9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("compliance_requirements", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("compliance_assignments", sa.Column("requirement_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_table(
        "compliance_requirement_versions",
        sa.Column("requirement_id", UUID(as_uuid=True), sa.ForeignKey("compliance_requirements.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_compliance_requirement_versions_tenant_id", "compliance_requirement_versions", ["tenant_id"])
    op.execute("""
        INSERT INTO compliance_requirement_versions
            (requirement_id, version, tenant_id, snapshot, created_at)
        SELECT id, 1, tenant_id,
            jsonb_build_object('name', name, 'description', description,
                'due_days', due_days, 'recurrence_days', recurrence_days,
                'active', active, 'rules', rules),
            created_at
        FROM compliance_requirements
    """)


def downgrade() -> None:
    op.drop_index("ix_compliance_requirement_versions_tenant_id", table_name="compliance_requirement_versions")
    op.drop_table("compliance_requirement_versions")
    op.drop_column("compliance_assignments", "requirement_version")
    op.drop_column("compliance_requirements", "version")
