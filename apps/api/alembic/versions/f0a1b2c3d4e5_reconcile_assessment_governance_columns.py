"""reconcile assessment governance columns

Revision ID: f0a1b2c3d4e5
Revises: ee55ff66aa77
Create Date: 2026-09-30
"""

from typing import Sequence, Union


revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = ("ee55ff66aa77", "f6a7b8c9d0e1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
