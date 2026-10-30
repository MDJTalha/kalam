from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k1l2m3n4o5p6"
down_revision = "j6k7l8m9n0o1"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    offline = context.is_offline_mode()
    inspector = None if offline else sa.inspect(bind)
    if offline or not inspector.has_table("developer_support_sessions"):
        op.create_table(
            "developer_support_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("developer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("target_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reason", sa.String(500), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["developer_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["target_tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("token_hash"),
        )
    op.create_index("ix_dev_support_session_token", "developer_support_sessions", ["token_hash"], if_not_exists=True)
    op.create_index("ix_dev_support_session_developer", "developer_support_sessions", ["developer_user_id"], if_not_exists=True)

def downgrade():
    bind = op.get_bind()
    offline = context.is_offline_mode()
    if offline or sa.inspect(bind).has_table("developer_support_sessions"):
        op.drop_index("ix_dev_support_session_developer", table_name="developer_support_sessions", if_exists=True)
        op.drop_index("ix_dev_support_session_token", table_name="developer_support_sessions", if_exists=True)
        op.drop_table("developer_support_sessions")
