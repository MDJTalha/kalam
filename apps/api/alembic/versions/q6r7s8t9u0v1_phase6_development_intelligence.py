"""Phase 6 development intelligence."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision="q6r7s8t9u0v1"; down_revision="p5a6b7c8d9e0"; branch_labels=None; depends_on=None
PERMISSIONS=[("development.recommendations.read","View governed development recommendations"),("development.recommendations.manage","Accept and manage development recommendations")]

def upgrade():
    op.create_table("development_recommendations",
        sa.Column("id",UUID(as_uuid=True),primary_key=True),
        sa.Column("tenant_id",UUID(as_uuid=True),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("user_id",UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),
        sa.Column("capability_gap_id",UUID(as_uuid=True),sa.ForeignKey("capability_gaps.id",ondelete="CASCADE"),nullable=False),
        sa.Column("intervention_type",sa.String(40),nullable=False),
        sa.Column("source_type",sa.String(40),nullable=False),
        sa.Column("source_id",sa.String(160),nullable=False),
        sa.Column("title",sa.String(240),nullable=False),
        sa.Column("rationale",sa.Text(),nullable=False),
        sa.Column("score",sa.Numeric(5,2),nullable=False),
        sa.Column("priority",sa.String(20),nullable=False,server_default="medium"),
        sa.Column("timeframe_days",sa.Integer(),nullable=False,server_default="90"),
        sa.Column("status",sa.String(30),nullable=False,server_default="recommended"),
        sa.Column("recommendation_version",sa.String(30),nullable=False,server_default="phase6.v1"),
        sa.Column("metadata_json",sa.JSON(),nullable=False,server_default="{}"),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("tenant_id","user_id","capability_gap_id","intervention_type","source_type","source_id",name="uq_development_recommendation_target"),
        sa.CheckConstraint("score >= 0 AND score <= 100",name="ck_development_recommendation_score"))
    op.create_index("ix_development_recommendations_tenant_user","development_recommendations",["tenant_id","user_id"])
    op.create_index("ix_development_recommendations_gap","development_recommendations",["tenant_id","capability_gap_id"])
    conn=op.get_bind()
    for key,desc in PERMISSIONS:
        conn.execute(sa.text("INSERT INTO permissions (id,key,description) SELECT gen_random_uuid(),CAST(:key AS varchar),CAST(:desc AS text) WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key=CAST(:key AS varchar))"),{"key":key,"desc":desc})
    role_keys={"Tenant Owner":["development.recommendations.read","development.recommendations.manage"],"Tenant Administrator":["development.recommendations.read","development.recommendations.manage"],"L&D Administrator":["development.recommendations.read","development.recommendations.manage"],"HR / People Administrator":["development.recommendations.read"],"Manager":["development.recommendations.read"]}
    for role_name,keys in role_keys.items():
        for key in keys:
            conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT r.id,p.id FROM roles r JOIN permissions p ON p.key=:key WHERE lower(r.name)=lower(:role_name) AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)"),{"role_name":role_name,"key":key})

def downgrade():
    conn=op.get_bind()
    for key,_ in PERMISSIONS:
        conn.execute(sa.text("DELETE FROM role_permissions rp USING permissions p WHERE rp.permission_id=p.id AND p.key=:key"),{"key":key})
        conn.execute(sa.text("DELETE FROM permissions WHERE key=:key"),{"key":key})
    op.drop_index("ix_development_recommendations_gap",table_name="development_recommendations")
    op.drop_index("ix_development_recommendations_tenant_user",table_name="development_recommendations")
    op.drop_table("development_recommendations")
