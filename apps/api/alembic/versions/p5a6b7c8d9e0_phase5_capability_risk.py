"""Phase 5 capability risk intelligence."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision="p5a6b7c8d9e0"; down_revision="g7h8i9j0k1l2"; branch_labels=None; depends_on=None
PERMISSIONS=[("capability_risk.read","View capability risk intelligence"),("capability_risk.manage","Recalculate capability risk intelligence")]

def upgrade():
    op.create_table("capability_risks",
        sa.Column("id",UUID(as_uuid=True),primary_key=True),
        sa.Column("tenant_id",UUID(as_uuid=True),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("capability_id",UUID(as_uuid=True),sa.ForeignKey("capabilities.id",ondelete="CASCADE"),nullable=False),
        sa.Column("risk_score",sa.Numeric(5,2),nullable=False), sa.Column("risk_level",sa.String(20),nullable=False),
        sa.Column("gap_severity_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("criticality_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("strategic_importance_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("people_exposure_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("critical_role_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("evidence_confidence_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("assessment_age_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("development_inactivity_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("certification_expiry_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("concentration_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("compliance_impact_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("trend_score",sa.Numeric(5,2),nullable=False,server_default="0"),
        sa.Column("affected_people",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("affected_roles",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("critical_roles_affected",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("evidence_count",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("development_active_count",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("assessment_age_days",sa.Integer()),
        sa.Column("certification_expiring_count",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("calculation_version",sa.String(30),nullable=False,server_default="phase5.v1"),
        sa.Column("explanation",sa.JSON(),nullable=False,server_default="{}"),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("computed_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("tenant_id","capability_id",name="uq_capability_risk_tenant_capability"),
        sa.CheckConstraint("risk_score>=0 AND risk_score<=100",name="ck_capability_risk_score"))
    op.create_index("ix_capability_risks_tenant_level","capability_risks",["tenant_id","risk_level"])
    op.create_index("ix_capability_risks_tenant_score","capability_risks",["tenant_id","risk_score"])
    conn=op.get_bind()
    for key,description in PERMISSIONS:
        conn.execute(sa.text("INSERT INTO permissions (id,key,description) SELECT gen_random_uuid(),CAST(:key AS varchar),CAST(:description AS text) WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE key=CAST(:key AS varchar))"),{"key":key,"description":description})
    role_keys={"Tenant Owner":["capability_risk.read","capability_risk.manage"],"Tenant Administrator":["capability_risk.read","capability_risk.manage"],"L&D Administrator":["capability_risk.read","capability_risk.manage"],"HR / People Administrator":["capability_risk.read","capability_risk.manage"],"Manager":["capability_risk.read"]}
    for role_name,keys in role_keys.items():
        for key in keys:
            conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT r.id,p.id FROM roles r JOIN permissions p ON p.key=:key WHERE lower(r.name)=lower(:role_name) AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)"),{"role_name":role_name,"key":key})

def downgrade():
    conn=op.get_bind()
    for key,_ in PERMISSIONS:
        conn.execute(sa.text("DELETE FROM role_permissions rp USING permissions p WHERE rp.permission_id=p.id AND p.key=:key"),{"key":key})
        conn.execute(sa.text("DELETE FROM permissions WHERE key=:key"),{"key":key})
    op.drop_index("ix_capability_risks_tenant_score",table_name="capability_risks"); op.drop_index("ix_capability_risks_tenant_level",table_name="capability_risks"); op.drop_table("capability_risks")
