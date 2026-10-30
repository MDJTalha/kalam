"""Add tenant-scoped knowledge articles."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "k1b2c3d4e5f6"
down_revision = "r7s8t9u0v1w2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), server_default="general", nullable=False),
        sa.Column("tags", JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_knowledge_articles_status"),
    )
    op.create_index("ix_knowledge_articles_tenant_id", "knowledge_articles", ["tenant_id"])
    op.create_index("ix_knowledge_articles_tenant_status_updated", "knowledge_articles", ["tenant_id", "status", "updated_at"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_articles_tenant_status_updated", table_name="knowledge_articles")
    op.drop_index("ix_knowledge_articles_tenant_id", table_name="knowledge_articles")
    op.drop_table("knowledge_articles")
