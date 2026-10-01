from alembic import op
import sqlalchemy as sa

revision = "f7b8c9d0e1f2"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None

READ_EXECUTE_ROLES = {
    "learner": ["capability_assessments.read", "capability_assessments.execute"],
    "employee": ["capability_assessments.read", "capability_assessments.execute"],
    "learner / employee": ["capability_assessments.read", "capability_assessments.execute"],
    "employee / learner": ["capability_assessments.read", "capability_assessments.execute"],
    "manager": ["capability_assessments.read", "capability_assessments.execute"],
}
REASSESSMENT_ROLES = {"tenant owner", "tenant administrator", "l&d administrator", "hr / people administrator"}

def upgrade() -> None:
    conn = op.get_bind()
    for role_name, keys in READ_EXECUTE_ROLES.items():
        for key in keys:
            conn.execute(sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r JOIN permissions p ON p.key = CAST(:key AS varchar)
                WHERE lower(r.name) = CAST(:role_name AS varchar)
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions rp
                    WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  )
            """), {"role_name": role_name, "key": key})
    for role_name in REASSESSMENT_ROLES:
        conn.execute(sa.text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r JOIN permissions p ON p.key = 'reassessment.manage'
            WHERE lower(r.name) = CAST(:role_name AS varchar)
              AND NOT EXISTS (
                SELECT 1 FROM role_permissions rp
                WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
        """), {"role_name": role_name})

def downgrade() -> None:
    conn = op.get_bind()
    for role_name, keys in READ_EXECUTE_ROLES.items():
        for key in keys:
            conn.execute(sa.text("""
                DELETE FROM role_permissions rp
                USING roles r, permissions p
                WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  AND lower(r.name) = CAST(:role_name AS varchar)
                  AND p.key = CAST(:key AS varchar)
            """), {"role_name": role_name, "key": key})
    for role_name in REASSESSMENT_ROLES:
        conn.execute(sa.text("""
            DELETE FROM role_permissions rp
            USING roles r, permissions p
            WHERE rp.role_id = r.id AND rp.permission_id = p.id
              AND lower(r.name) = CAST(:role_name AS varchar)
              AND p.key = 'reassessment.manage'
        """), {"role_name": role_name})
