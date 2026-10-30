"""Add platform incident lifecycle."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "9a7b8c9d0e1f"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "platform_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("incident_number", sa.String(32), nullable=False, unique=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("impact", sa.String(500), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("severity IN ('sev1', 'sev2', 'sev3', 'sev4')", name="ck_platform_incidents_severity"),
        sa.CheckConstraint("status IN ('open', 'investigating', 'mitigated', 'resolved')", name="ck_platform_incidents_status"),
    )
    op.create_index("ix_platform_incidents_status_severity", "platform_incidents", ["status", "severity"])

def downgrade() -> None:
    op.drop_index("ix_platform_incidents_status_severity", table_name="platform_incidents")
    op.drop_table("platform_incidents")
