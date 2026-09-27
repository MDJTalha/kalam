"""store webhook secrets encrypted at rest

Revision ID: b7d4e8f1a2c3
Revises: f1c2d3e4a5b6
"""

from alembic import op
import sqlalchemy as sa

revision = "b7d4e8f1a2c3"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "webhook_endpoints",
        sa.Column("secret_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "webhook_endpoints",
        sa.Column("secret_key_id", sa.String(length=80), nullable=True),
    )
    # Existing rows contain only a one-way hash, which cannot be used to
    # reconstruct the original webhook secret. Disable them until an operator
    # rotates each endpoint and distributes the newly issued secret.
    op.execute(
        "UPDATE webhook_endpoints "
        "SET active = FALSE "
        "WHERE secret_encrypted IS NULL"
    )
    op.drop_column("webhook_endpoints", "secret_hash")


def downgrade() -> None:
    op.add_column(
        "webhook_endpoints",
        sa.Column("secret_hash", sa.String(length=128), nullable=True),
    )
    op.drop_column("webhook_endpoints", "secret_key_id")
    op.drop_column("webhook_endpoints", "secret_encrypted")
