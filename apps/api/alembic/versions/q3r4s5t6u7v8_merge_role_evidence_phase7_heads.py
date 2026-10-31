"""Merge Phase 7 development execution with capability evidence governance."""

from alembic import op

revision = "q3r4s5t6u7v8"
down_revision = ("p2q3r4s5t6u7", "r7s8t9u0v1w2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a graph merge only. Both parent revisions have already applied
    # their schema and permission changes before this revision is recorded.
    pass


def downgrade() -> None:
    # Keep the merged graph intact on downgrade; reversing either parent
    # independently would discard application data and governance controls.
    pass
