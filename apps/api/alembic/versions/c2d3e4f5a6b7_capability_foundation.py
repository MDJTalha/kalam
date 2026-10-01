"""Add governed capability foundation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert as pg_insert

revision = "c2d3e4f5a6b7"
down_revision = "b3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capability_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_capability_category_tenant_name"),
    )
    op.create_index("ix_capability_categories_tenant_id", "capability_categories", ["tenant_id"])
    op.create_table(
        "capabilities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("capability_categories.id", ondelete="SET NULL")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("level_min", sa.Integer(), server_default="1", nullable=False),
        sa.Column("level_max", sa.Integer(), server_default="5", nullable=False),
        sa.Column("criticality", sa.String(20), server_default="medium", nullable=False),
        sa.Column("status", sa.String(30), server_default="draft", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("governance", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_capability_tenant_code"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_capability_tenant_name"),
        sa.CheckConstraint("level_min >= 1 AND level_min <= 5", name="ck_capability_level_min"),
        sa.CheckConstraint("level_max >= 1 AND level_max <= 5", name="ck_capability_level_max"),
        sa.CheckConstraint("level_min <= level_max", name="ck_capability_level_range"),
    )
    op.create_index("ix_capabilities_tenant_id", "capabilities", ["tenant_id"])
    op.create_index("ix_capabilities_category_id", "capabilities", ["category_id"])
    op.create_index("ix_capabilities_owner_id", "capabilities", ["owner_id"])
    op.create_table(
        "capability_levels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("capability_id", UUID(as_uuid=True), sa.ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("indicators", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.UniqueConstraint("capability_id", "level", name="uq_capability_level"),
    )
    op.create_index("ix_capability_levels_capability_id", "capability_levels", ["capability_id"])

    op.create_table(
        "capability_skills",
        sa.Column("capability_id", UUID(as_uuid=True), sa.ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("capability_id", "skill_id", name="uq_capability_skill"),
    )
    op.create_index("ix_capability_skills_skill_id", "capability_skills", ["skill_id"])

    permissions = sa.table("permissions", sa.column("id", UUID(as_uuid=True)), sa.column("key", sa.String), sa.column("description", sa.String))
    for key, description in [("capabilities.read", "View capability framework"), ("capabilities.manage", "Manage capability framework")]:
        op.execute(pg_insert(permissions).values(id=sa.text("gen_random_uuid()"), key=key, description=description).on_conflict_do_nothing(index_elements=["key"]))


def downgrade() -> None:
    op.drop_table("capability_skills")
    op.drop_table("capability_levels")
    op.drop_table("capabilities")
    op.drop_table("capability_categories")
