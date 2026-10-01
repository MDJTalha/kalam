"""Scope notification deduplication to each tenant."""

from alembic import op
import sqlalchemy as sa


revision = "j6k7l8m9n0o1"
down_revision = "i5j6k7l8m9n0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_notifications_dedupe_key", table_name="notifications")
    op.create_index("ix_notifications_dedupe_key", "notifications", ["dedupe_key"])
    op.create_unique_constraint(
        "uq_notifications_tenant_dedupe_key",
        "notifications",
        ["tenant_id", "dedupe_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_notifications_tenant_dedupe_key", "notifications", type_="unique")
    op.drop_index("ix_notifications_dedupe_key", table_name="notifications")
    op.create_index("ix_notifications_dedupe_key", "notifications", ["dedupe_key"], unique=True)
