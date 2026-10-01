"""Add enterprise inquiry qualification fields."""

from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7g8h9"
down_revision = "b3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketing_inquiries", sa.Column("country_code", sa.String(2), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("country_name", sa.String(120), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("organization_size", sa.String(60), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("business_phone", sa.String(80), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("primary_objective", sa.String(180), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("evaluation_timeline", sa.String(80), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("utm_source", sa.String(120), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("utm_medium", sa.String(120), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("utm_campaign", sa.String(160), nullable=True))
    op.add_column("marketing_inquiries", sa.Column("landing_path", sa.String(300), nullable=True))
    op.create_index("ix_marketing_inquiries_country_code", "marketing_inquiries", ["country_code"])
    op.create_index("ix_marketing_inquiries_primary_objective", "marketing_inquiries", ["primary_objective"])


def downgrade() -> None:
    op.drop_index("ix_marketing_inquiries_primary_objective", table_name="marketing_inquiries")
    op.drop_index("ix_marketing_inquiries_country_code", table_name="marketing_inquiries")
    op.drop_column("marketing_inquiries", "landing_path")
    op.drop_column("marketing_inquiries", "utm_campaign")
    op.drop_column("marketing_inquiries", "utm_medium")
    op.drop_column("marketing_inquiries", "utm_source")
    op.drop_column("marketing_inquiries", "evaluation_timeline")
    op.drop_column("marketing_inquiries", "primary_objective")
    op.drop_column("marketing_inquiries", "business_phone")
    op.drop_column("marketing_inquiries", "organization_size")
    op.drop_column("marketing_inquiries", "country_name")
    op.drop_column("marketing_inquiries", "country_code")
