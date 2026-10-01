"""Add SaaS CRM commercial tasks."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "b3c4d5e6f7g8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crm_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ops_tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("crm_accounts.id", ondelete="CASCADE")),
        sa.Column("subscription_id", UUID(as_uuid=True), sa.ForeignKey("crm_subscriptions.id", ondelete="CASCADE")),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("task_type", sa.String(50), server_default="follow_up", nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(30), server_default="open", nullable=False),
        sa.Column("priority", sa.String(20), server_default="normal", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("source_key", sa.String(180)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ops_tenant_id", "source_key", name="uq_crm_task_ops_source_key"),
    )
    op.create_index("ix_crm_tasks_ops_tenant_id", "crm_tasks", ["ops_tenant_id"])
    op.create_index("ix_crm_tasks_account_id", "crm_tasks", ["account_id"])
    op.create_index("ix_crm_tasks_subscription_id", "crm_tasks", ["subscription_id"])
    op.create_index("ix_crm_tasks_owner_user_id", "crm_tasks", ["owner_user_id"])
    op.create_index("ix_crm_tasks_task_type", "crm_tasks", ["task_type"])
    op.create_index("ix_crm_tasks_status", "crm_tasks", ["status"])
    op.create_index("ix_crm_tasks_priority", "crm_tasks", ["priority"])
    op.create_index("ix_crm_tasks_due_at", "crm_tasks", ["due_at"])


def downgrade() -> None:
    op.drop_table("crm_tasks")
