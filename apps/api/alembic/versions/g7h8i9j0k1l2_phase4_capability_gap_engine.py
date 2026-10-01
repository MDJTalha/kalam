"""Phase 4 capability gap engine."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision="g7h8i9j0k1l2"; down_revision="f7b8c9d0e1f2"; branch_labels=None; depends_on=None
PERMISSIONS=[("capability_gaps.read","View capability gaps and organizational exposure"),("capability_gaps.manage","Recalculate and manage capability gap snapshots")]
def upgrade():
    op.create_table("capability_gaps",
        sa.Column("id",UUID(as_uuid=True),primary_key=True), sa.Column("tenant_id",UUID(as_uuid=True),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("user_id",UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False), sa.Column("role_requirement_id",UUID(as_uuid=True),sa.ForeignKey("role_requirements.id",ondelete="CASCADE"),nullable=False),
        sa.Column("target_type",sa.String(20),nullable=False), sa.Column("target_id",UUID(as_uuid=True),nullable=False), sa.Column("required_level",sa.Numeric(4,2),nullable=False),
        sa.Column("demonstrated_level",sa.Numeric(4,2)), sa.Column("gap_value",sa.Numeric(5,2)), sa.Column("severity",sa.String(30),nullable=False),
        sa.Column("criticality",sa.String(20),nullable=False), sa.Column("weight",sa.Integer(),server_default="1",nullable=False), sa.Column("evidence_confidence",sa.Integer(),server_default="0",nullable=False),
        sa.Column("evidence_count",sa.Integer(),server_default="0",nullable=False), sa.Column("evidence_observed_at",sa.DateTime(timezone=True)), sa.Column("calculation_version",sa.String(30),server_default="phase4.v1",nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False), sa.Column("computed_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("tenant_id","user_id","role_requirement_id",name="uq_capability_gap_assignment"),
        sa.CheckConstraint("target_type IN ('capability','competency','skill')",name="ck_capability_gap_target_type"),
        sa.CheckConstraint("required_level>=1 AND required_level<=5",name="ck_capability_gap_required_level"),
        sa.CheckConstraint("demonstrated_level IS NULL OR (demonstrated_level>=1 AND demonstrated_level<=5)",name="ck_capability_gap_demonstrated_level"),
        sa.CheckConstraint("gap_value IS NULL OR gap_value>=0",name="ck_capability_gap_value"), sa.CheckConstraint("evidence_confidence>=0 AND evidence_confidence<=100",name="ck_capability_gap_confidence"))
    op.create_index("ix_capability_gaps_tenant_user","capability_gaps",["tenant_id","user_id"]); op.create_index("ix_capability_gaps_tenant_severity","capability_gaps",["tenant_id","severity"])
    op.create_index("ix_capability_gaps_tenant_target","capability_gaps",["tenant_id","target_type","target_id"]); op.create_index("ix_capability_gaps_requirement","capability_gaps",["role_requirement_id"])
    conn=op.get_bind()
    for key,description in PERMISSIONS:
        conn.execute(sa.text("INSERT INTO permissions (id,key,description) SELECT gen_random_uuid(),CAST(:key AS varchar),CAST(:description AS text) WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key=CAST(:key AS varchar))"),{"key":key,"description":description})
    role_keys={"Tenant Owner":["capability_gaps.read","capability_gaps.manage"],"Tenant Administrator":["capability_gaps.read","capability_gaps.manage"],"L&D Administrator":["capability_gaps.read","capability_gaps.manage"],"HR / People Administrator":["capability_gaps.read","capability_gaps.manage"],"Manager":["capability_gaps.read"],"Learner / Employee":["capability_gaps.read"],"Employee":["capability_gaps.read"],"Learner":["capability_gaps.read"]}
    for role_name,keys in role_keys.items():
        for key in keys:
            conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT r.id,p.id FROM roles r JOIN permissions p ON p.key=:key WHERE lower(r.name)=lower(:role_name) AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)"),{"role_name":role_name,"key":key})
def downgrade():
    conn=op.get_bind()
    for key,_ in PERMISSIONS:
        conn.execute(sa.text("DELETE FROM role_permissions rp USING permissions p WHERE rp.permission_id=p.id AND p.key=:key"),{"key":key})
        conn.execute(sa.text("DELETE FROM permissions WHERE key=:key"),{"key":key})
    op.drop_index("ix_capability_gaps_requirement",table_name="capability_gaps"); op.drop_index("ix_capability_gaps_tenant_target",table_name="capability_gaps")
    op.drop_index("ix_capability_gaps_tenant_severity",table_name="capability_gaps"); op.drop_index("ix_capability_gaps_tenant_user",table_name="capability_gaps"); op.drop_table("capability_gaps")
