"""Separate SaaS business and platform roles; scope manager and L&D permissions.

This migration is additive except for tightening the Manager role's tenant-wide
people/report permissions. Existing users, learning records and tenant IDs are
preserved.
"""
from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "9a7b8c9d0e1f"
down_revision = "82cb7d9e1f4a"
branch_labels = None
depends_on = None

NEW_PERMISSIONS = {
    "platform.tenants.read": "View platform tenant registry and operational metadata",
    "platform.tenants.manage": "Provision, suspend and reactivate customer tenants",
    "platform.health.read": "View platform service and infrastructure health",
    "platform.incidents.manage": "Investigate and manage platform incidents",
    "platform.support.access": "Start and manage audited, time-limited customer support access",
    "platform.audit.read": "View platform-level operational audit events",
    "users.team.read": "View direct reports and their assigned learning status",
    "reports.team.read": "View manager-scoped team learning reports",
    "users.invite.learning_roles": "Invite learners, trainers and managers for learning delivery",
    "roles.manage": "Create and govern tenant custom roles using delegated permissions",
    "courses.assign_team": "Assign published learning to direct reports",
    "development.team.read": "Read direct reports' development plans and progress",
    "development.team.manage": "Manage development milestones and feedback for direct reports",
}

CUSTOMER_ROLE_DEFINITIONS = {
    "Tenant Owner": ["tenant.read", "reports.read", "audit.read"],
    "HR / People Administrator": ["users.read", "users.manage", "reports.read", "compliance.manage"],
    "L&D Administrator": [
        "courses.read", "courses.manage", "learning.access", "assessments.manage",
        "certificates.manage", "reports.read", "skills.manage", "capabilities.read",
        "capabilities.manage", "competencies.read", "competencies.manage",
        "role_requirements.read", "role_requirements.manage", "development.manage",
        "users.read", "users.invite.learning_roles",
    ],
    "Manager": [
        "users.team.read", "courses.read", "courses.assign_team", "learning.access",
        "reports.team.read", "development.manage", "development.team.read",
        "development.team.manage",
    ],
    "Trainer": ["courses.read", "learning.access", "assessments.manage"],
    "Instructor": ["courses.read", "learning.access", "assessments.manage"],
    "L&D Analyst": [
        "courses.read", "reports.read", "capabilities.read", "competencies.read",
        "capability_assessments.read", "role_requirements.read",
    ],
    "Assessor": [
        "capability_assessments.read", "capability_assessments.execute",
        "competencies.read",
    ],
    # HRBP and Regional Executive require organizational-unit row-level
    # filters that are not yet implemented. Keep these templates deliberately
    # non-sensitive until that scope engine is available.
    "HR Business Partner": ["courses.read", "learning.access", "development.manage"],
    "Quality & Compliance": [
        "users.read", "courses.read", "learning.access", "compliance.manage",
        "reports.read", "audit.read", "files.read", "evidence.read", "evidence.verify",
    ],
    "Auditor": ["reports.read", "audit.read", "files.read", "evidence.read"],
    "Regional Executive": ["tenant.read", "courses.read", "learning.access"],
    "Global Executive": [
        "tenant.read", "users.read", "courses.read", "learning.access",
        "reports.read", "audit.read", "compliance.manage", "skills.manage",
        "capabilities.read", "development.manage", "capability_gaps.read",
        "capability_risk.read",
    ],
}

PLATFORM_ROLE_DEFINITIONS = {
    "SaaS Owner": ["saas.crm.read"],
    "Platform Developer": [
        "platform.tenants.read", "platform.tenants.manage", "platform.health.read",
        "platform.incidents.manage", "platform.support.access", "platform.audit.read",
    ],
    "Sales Operations": ["saas.crm.read", "saas.crm.manage"],
    "Sales Viewer": ["saas.crm.read"],
}


def _permission_id(conn, key: str):
    return conn.execute(
        sa.text("SELECT id FROM permissions WHERE key=:key"), {"key": key}
    ).scalar()


def _ensure_permission(conn, key: str, description: str):
    existing = _permission_id(conn, key)
    if existing is not None:
        return existing
    permission_id = uuid4()
    conn.execute(
        sa.text(
            "INSERT INTO permissions (id, key, description) "
            "VALUES (:id, :key, :description)"
        ),
        {"id": permission_id, "key": key, "description": description},
    )
    return permission_id


def _ensure_role(conn, tenant_id, name: str, role_kind: str):
    row = conn.execute(
        sa.text(
            "SELECT id, role_kind FROM roles "
            "WHERE tenant_id=:tenant_id AND lower(name)=lower(:name)"
        ),
        {"tenant_id": tenant_id, "name": name},
    ).first()

    if row is not None:
        role_id, existing_kind = row
        if existing_kind == "custom" and role_kind in {"predefined", "platform"}:
            # Never repurpose a customer-created custom role because it happens
            # to use a built-in role name. Retain all its memberships and
            # permission links under a collision-safe legacy name instead.
            short_id = str(role_id).replace("-", "")[:8]
            custom_name = f"{name[:78]} (Custom {short_id})"
            conn.execute(
                sa.text("UPDATE roles SET name=:name WHERE id=:id"),
                {"id": role_id, "name": custom_name},
            )
            row = None
        elif existing_kind in {"predefined", "legacy", "platform"}:
            conn.execute(
                sa.text("UPDATE roles SET role_kind=:role_kind WHERE id=:id"),
                {"id": role_id, "role_kind": role_kind},
            )
            return role_id
        else:
            raise RuntimeError(
                f"Refusing to change role '{name}' with role_kind='{existing_kind}'"
            )

    role_id = uuid4()
    conn.execute(
        sa.text(
            "INSERT INTO roles (id, tenant_id, name, description, role_kind) "
            "VALUES (:id, :tenant_id, :name, :description, :role_kind)"
        ),
        {
            "id": role_id,
            "tenant_id": tenant_id,
            "name": name,
            "description": f"Kalam predefined role: {name}",
            "role_kind": role_kind,
        },
    )
    return role_id


def _replace_role_permissions(conn, role_id, keys: list[str]):
    conn.execute(
        sa.text("DELETE FROM role_permissions WHERE role_id=:role_id"),
        {"role_id": role_id},
    )
    for key in keys:
        permission_id = _permission_id(conn, key)
        if permission_id is None:
            raise RuntimeError(f"Required permission was not created: {key}")
        conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "VALUES (:role_id, :permission_id)"
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )


def upgrade() -> None:
    conn = op.get_bind()

    for key, description in NEW_PERMISSIONS.items():
        _ensure_permission(conn, key, description)

    # Manager is a team-scoped role. Remove tenant-wide directory and report
    # permissions; separate HR/L&D roles can still grant broader access.
    manager_rows = conn.execute(
        sa.text(
            "SELECT id FROM roles WHERE lower(name)='manager' "
            "AND role_kind IN ('predefined', 'legacy')"
        )
    ).fetchall()
    users_read_id = _permission_id(conn, "users.read")
    reports_read_id = _permission_id(conn, "reports.read")
    for (role_id,) in manager_rows:
        if users_read_id is not None:
            conn.execute(
                sa.text(
                    "DELETE FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id"
                ),
                {"role_id": role_id, "permission_id": users_read_id},
            )
        if reports_read_id is not None:
            conn.execute(
                sa.text(
                    "DELETE FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id"
                ),
                {"role_id": role_id, "permission_id": reports_read_id},
            )
        for key in (
            "users.team.read", "reports.team.read",
            "courses.assign_team", "development.team.read", "development.team.manage",
        ):
            permission_id = _permission_id(conn, key)
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT :role_id, :permission_id "
                    "WHERE NOT EXISTS (SELECT 1 FROM role_permissions "
                    "WHERE role_id=:role_id AND permission_id=:permission_id)"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            )

    # Ensure every permission referenced by a role template exists. Existing
    # permission identifiers and assignments are kept; only missing catalogue
    # entries are added.
    for keys in CUSTOMER_ROLE_DEFINITIONS.values():
        for key in keys:
            if _permission_id(conn, key) is None:
                _ensure_permission(conn, key, key.replace(".", " ").replace("_", " ").capitalize())
    for key in (
        "tenant.read", "tenant.manage", "users.read", "users.manage", "reports.read",
        "audit.read", "integrations.manage", "capabilities.read", "capabilities.manage",
        "roles.manage",
    ):
        if _permission_id(conn, key) is None:
            _ensure_permission(conn, key, key.replace(".", " ").replace("_", " ").capitalize())

    # Customer role templates. Tenant Administrator owns account and role
    # governance; L&D can invite only operational learning roles.
    customer_tenants = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug <> 'kalam'")
    ).fetchall()
    for (tenant_id,) in customer_tenants:
        tenant_admin_id = _ensure_role(conn, tenant_id, "Tenant Administrator", "predefined")
        existing_admin_keys = conn.execute(
            sa.text(
                "SELECT p.key FROM role_permissions rp "
                "JOIN permissions p ON p.id=rp.permission_id WHERE rp.role_id=:role_id"
            ),
            {"role_id": tenant_admin_id},
        ).scalars().all()
        tenant_admin_keys = sorted((set(existing_admin_keys) - {
            "saas.crm.read", "saas.crm.manage", "platform.tenants.read",
            "platform.tenants.manage", "platform.health.read",
            "platform.incidents.manage", "platform.support.access", "platform.audit.read",
        }) | {
            "tenant.read", "tenant.manage", "users.read", "users.manage", "reports.read",
            "audit.read", "integrations.manage", "capabilities.read", "capabilities.manage",
            "roles.manage",
        })
        _replace_role_permissions(conn, tenant_admin_id, tenant_admin_keys)

        for role_name, keys in CUSTOMER_ROLE_DEFINITIONS.items():
            role_id = _ensure_role(conn, tenant_id, role_name, "predefined")
            _replace_role_permissions(conn, role_id, keys)

        for role_name in ("L&D Administrator", "HR/L&D Admin"):
            role_id = conn.execute(
                sa.text(
                    "SELECT id FROM roles WHERE tenant_id=:tenant_id "
                    "AND lower(name)=lower(:name) AND role_kind IN ('predefined','legacy')"
                ),
                {"tenant_id": tenant_id, "name": role_name},
            ).scalar()
            if role_id is not None:
                current = conn.execute(
                    sa.text(
                        "SELECT p.key FROM role_permissions rp "
                        "JOIN permissions p ON p.id=rp.permission_id WHERE rp.role_id=:role_id"
                    ),
                    {"role_id": role_id},
                ).scalars().all()
                expanded = sorted((set(current) - {"users.manage"}) | {
                    "users.read", "users.invite.learning_roles", "competencies.read",
                    "competencies.manage", "role_requirements.read", "role_requirements.manage",
                })
                _replace_role_permissions(conn, role_id, expanded)

    # Kalam is the internal SaaS operations tenant, not a customer workspace.
    ops_tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug='kalam'")
    ).scalar()
    if ops_tenant_id is not None:
        old_owner_row = conn.execute(
            sa.text(
                "SELECT id, role_kind FROM roles "
                "WHERE tenant_id=:tenant_id AND lower(name)='saas administrator'"
            ),
            {"tenant_id": ops_tenant_id},
        ).first()
        old_owner_id = old_owner_row[0] if old_owner_row is not None else None
        old_owner_kind = old_owner_row[1] if old_owner_row is not None else None
        owner_id = conn.execute(
            sa.text(
                "SELECT id FROM roles WHERE tenant_id=:tenant_id AND lower(name)='saas owner'"
            ),
            {"tenant_id": ops_tenant_id},
        ).scalar()

        if owner_id is None and old_owner_id is not None and old_owner_kind == "custom":
            # Preserve any customer-defined role using the legacy SaaS
            # Administrator label rather than converting it into an owner.
            short_id = str(old_owner_id).replace("-", "")[:8]
            conn.execute(
                sa.text("UPDATE roles SET name=:name WHERE id=:id"),
                {"id": old_owner_id, "name": f"SaaS Administrator (Custom {short_id})"},
            )
            owner_id = _ensure_role(conn, ops_tenant_id, "SaaS Owner", "platform")
        elif owner_id is None and old_owner_id is not None:
            owner_id = old_owner_id
            conn.execute(
                sa.text("UPDATE roles SET name='SaaS Owner', description='Kalam business owner: commercial read access only', role_kind='platform' WHERE id=:id"),
                {"id": owner_id},
            )
        elif owner_id is None:
            owner_id = _ensure_role(conn, ops_tenant_id, "SaaS Owner", "platform")
        elif old_owner_id is not None and old_owner_id != owner_id and old_owner_kind == "custom":
            short_id = str(old_owner_id).replace("-", "")[:8]
            conn.execute(
                sa.text("UPDATE roles SET name=:name WHERE id=:id"),
                {"id": old_owner_id, "name": f"SaaS Administrator (Custom {short_id})"},
            )
        elif old_owner_id is not None and old_owner_id != owner_id:
            conn.execute(
                sa.text(
                    "INSERT INTO user_roles (user_id, role_id) "
                    "SELECT user_id, :owner_id FROM user_roles WHERE role_id=:old_id "
                    "ON CONFLICT DO NOTHING"
                ),
                {"owner_id": owner_id, "old_id": old_owner_id},
            )
            conn.execute(sa.text("DELETE FROM role_permissions WHERE role_id=:id"), {"id": old_owner_id})
            conn.execute(sa.text("DELETE FROM user_roles WHERE role_id=:id"), {"id": old_owner_id})
            conn.execute(sa.text("DELETE FROM roles WHERE id=:id"), {"id": old_owner_id})

        _replace_role_permissions(conn, owner_id, PLATFORM_ROLE_DEFINITIONS["SaaS Owner"])

        for role_name in ("Platform Developer", "Sales Operations", "Sales Viewer"):
            role_id = _ensure_role(conn, ops_tenant_id, role_name, "platform")
            _replace_role_permissions(conn, role_id, PLATFORM_ROLE_DEFINITIONS[role_name])


def downgrade() -> None:
    conn = op.get_bind()
    # Restore Manager's previous broad role links for rollback.
    for role_id, key in conn.execute(
        sa.text(
            "SELECT r.id, p.key FROM roles r CROSS JOIN permissions p "
            "WHERE lower(r.name)='manager' AND p.key IN ('users.read','reports.read')"
        )
    ).all():
        permission_id = _permission_id(conn, key)
        conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "SELECT :role_id, :permission_id WHERE NOT EXISTS "
                "(SELECT 1 FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id)"
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )
    # Restore legacy Owner role naming and permissions.
    ops_tenant_id = conn.execute(sa.text("SELECT id FROM tenants WHERE slug='kalam'")).scalar()
    if ops_tenant_id is not None:
        owner_id = conn.execute(
            sa.text("SELECT id FROM roles WHERE tenant_id=:tenant_id AND name='SaaS Owner'"),
            {"tenant_id": ops_tenant_id},
        ).scalar()
        if owner_id is not None:
            conn.execute(
                sa.text("UPDATE roles SET name='SaaS Administrator', description='Kalam SaaS administrator', role_kind='platform' WHERE id=:id"),
                {"id": owner_id},
            )
            admin_keys = ["tenant.read", "tenant.manage", "saas.crm.read", "saas.crm.manage"]
            _replace_role_permissions(conn, owner_id, admin_keys)
    # Retain newly added platform roles and permission definitions on downgrade:
    # dropping permissions referenced by an assigned role would be destructive.
