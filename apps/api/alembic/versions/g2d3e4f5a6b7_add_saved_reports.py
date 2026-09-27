"""add saved reports and schedules

Revision ID: g2d3e4f5a6b7
Revises: f1c2d3e4a5b6
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g2d3e4f5a6b7"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("report_type", sa.String(80), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="private"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_saved_report_tenant_name"),
    )
    op.create_index("ix_saved_reports_tenant_id", "saved_reports", ["tenant_id"])
    op.create_index("ix_saved_reports_owner_id", "saved_reports", ["owner_id"])
    op.create_table(
        "report_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("saved_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("saved_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recipients", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_report_schedules_tenant_id", "report_schedules", ["tenant_id"])
    op.create_index("ix_report_schedules_saved_report_id", "report_schedules", ["saved_report_id"])


def downgrade() -> None:
    op.drop_table("report_schedules")
    op.drop_table("saved_reports")
