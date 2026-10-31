"""Provision the canonical tenant and SaaS operations role catalogue.

The permission and role maps are intentionally snapshotted in this migration so
future catalogue edits do not change the behavior of an already-created
migration.
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "s1t2u3v4w5x6"
down_revision = "r7s8t9u0v1w2"
branch_labels = None
depends_on = None

PERMISSION_DESCRIPTIONS: dict[str, str] = {
    "tenant.read": "View the current tenant and its configuration",
    "tenant.manage": "Manage the current tenant configuration",
    "organization.read": "View tenant role and organization-unit metadata without employee records",
    "users.read": "View authorized workforce profiles",
    "team.read": "View the current user's direct reports and team learning signals",
    "users.manage": "Manage authorized workforce users and invitations",
    "courses.read": "View learning courses",
    "courses.manage": "Create and manage learning courses",
    "learning.access": "Access assigned learning experiences",
    "assessments.manage": "Author and administer tenant assessments",
    "assessments.grade_assigned": "Review and grade assessments for assigned instructor sessions",
    "certificates.manage": "Manage credentials and certificates",
    "compliance.manage": "Manage compliance requirements and assignments",
    "skills.manage": "Manage skills and competency frameworks",
    "capabilities.read": "View capability frameworks",
    "capabilities.manage": "Manage capability frameworks",
    "development.manage": "Manage development plans within authorized scope",
    "reports.read": "View reports within authorized scope",
    "reports.manage": "Create and manage saved reports and schedules",
    "reports.export.people": "Export employee-identifiable workforce registers",
    "reports.export.learning": "Export employee-linked learning and enrollment registers",
    "reports.export.compliance": "Export employee-linked compliance assignment records",
    "audit.read": "View tenant audit records",
    "files.read": "View governed files and evidence",
    "files.manage": "Manage governed file controls",
    "integrations.manage": "Manage tenant integrations",
    "ai.manage": "Manage governed AI settings",
    "reassessment.manage": "Manage capability reassessment workflows",
    "capability_gaps.read": "View capability gaps within authorized scope",
    "capability_gaps.manage": "Recalculate and administer tenant capability-gap intelligence",
    "capability_risk.read": "View capability risk within authorized scope",
    "capability_risk.manage": "Recalculate and administer tenant capability-risk intelligence",
    "capability_assessments.read": "View capability assessments within authorized scope",
    "capability_assessments.execute": "Complete assigned capability assessments",
    "evidence.read": "View capability evidence within authorized scope",
    "evidence.manage": "Capture and administer capability evidence",
    "evidence.verify": "Independently verify or reject submitted capability evidence",
    "competencies.read": "View governed competency definitions and proficiency levels",
    "saas.crm.read": "View consolidated Kalam SaaS business overview and full client 360",
    "saas.crm.manage": "Manage consolidated Kalam SaaS commercial records",
    "saas.sales.read": "View sales accounts, contacts, opportunities, tasks and pipeline",
    "saas.sales.manage": "Manage sales accounts, contacts, opportunities, tasks and pipeline",
    "saas.sales.export": "Export approved CRM account registers",
    "saas.pricing.read": "View SaaS plans, public pricing and commercial offers",
    "saas.pricing.manage": "Create and manage SaaS plans, pricing and offers",
    "saas.finance.read": "View subscriptions, contracts, invoices, payments and renewals",
    "saas.finance.manage": "Manage subscriptions, contracts, invoices, payments and renewals",
    "saas.customer_success.read": "View customer onboarding, trials and tenant lifecycle status",
    "saas.customer_users.read": "View customer-tenant employee accounts and access status",
    "saas.customer_success.manage": "Manage customer onboarding, trials, tenant status and customer access",
    "saas.platform.read": "View SaaS platform administration",
    "saas.platform.manage": "Manage SaaS platform administration",
    "saas.tenants.manage": "Provision and administer customer tenants",
    "saas.roles.manage": "Create and govern customer-tenant roles",
    "saas.team.read": "View internal SaaS operations team members",
    "saas.team.manage": "Manage internal SaaS operations team members and assignments",
    "saas.access.revoke": "Revoke customer and SaaS team account access",
    "saas.audit.read": "View SaaS platform audit activity",
}

TENANT_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Tenant Owner": ("tenant.read", "reports.read", "audit.read"),
    "Tenant Administrator": (
        "tenant.read", "tenant.manage", "users.read", "users.manage", "team.read",
        "reports.read", "reports.export.people", "reports.export.learning",
        "reports.export.compliance", "audit.read", "integrations.manage",
        "capabilities.read", "capabilities.manage", "capability_gaps.read",
        "capability_gaps.manage", "capability_risk.read", "capability_risk.manage",
    ),
    "HR / People Administrator": (
        "users.read", "users.manage", "team.read", "reports.read",
        "reports.export.people", "reports.export.learning", "reports.export.compliance",
        "compliance.manage", "capabilities.read", "development.manage",
        "capability_gaps.read", "capability_gaps.manage",
        "capability_risk.read", "capability_risk.manage",
    ),
    "L&D Administrator": (
        "courses.read", "courses.manage", "learning.access", "assessments.manage",
        "certificates.manage", "reports.read", "reports.export.learning",
        "skills.manage", "capabilities.read", "capabilities.manage", "development.manage",
        "users.read", "compliance.manage", "reassessment.manage", "evidence.read",
        "evidence.manage", "evidence.verify", "competencies.read",
        "capability_gaps.read", "capability_gaps.manage",
        "capability_risk.read", "capability_risk.manage",
    ),
    "Manager": (
        "team.read", "courses.read", "learning.access", "development.manage",
        "capabilities.read", "capability_gaps.read", "capability_risk.read",
        "capability_assessments.read", "capability_assessments.execute",
    ),
    "Instructor": ("courses.read", "learning.access", "assessments.grade_assigned"),
    "Learner / Employee": (
        "courses.read", "learning.access", "development.manage",
        "capability_assessments.read", "capability_assessments.execute",
    ),
    "HR Business Partner": ("team.read", "development.manage"),
    "Quality & Compliance": (
        "tenant.read", "organization.read", "compliance.manage", "audit.read",
        "files.read", "reports.export.compliance",
    ),
    "Auditor": ("audit.read", "files.read", "evidence.read", "competencies.read"),
    "Regional Executive": (),
    "Global Executive": (
        "tenant.read", "courses.read", "learning.access", "reports.read",
        "audit.read", "capabilities.read",
    ),
}

PLATFORM_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Platform Developer": (),
    "SaaS Super Admin": (
        "tenant.read", "tenant.manage", "users.read", "users.manage", "team.read",
        "saas.crm.read", "saas.crm.manage", "saas.sales.read", "saas.sales.manage",
        "saas.sales.export", "saas.pricing.read", "saas.pricing.manage",
        "saas.finance.read", "saas.finance.manage", "saas.customer_success.read",
        "saas.customer_success.manage", "saas.customer_users.read",
        "saas.platform.read", "saas.platform.manage", "saas.tenants.manage",
        "saas.roles.manage", "saas.team.read", "saas.team.manage",
        "saas.access.revoke", "saas.audit.read", "audit.read", "reports.read",
        "integrations.manage",
    ),
    "SaaS Administrator": (
        "tenant.read", "tenant.manage", "users.read", "users.manage",
        "saas.platform.read", "saas.platform.manage", "saas.customer_success.read",
        "saas.team.read", "saas.team.manage", "saas.audit.read", "audit.read",
        "integrations.manage",
    ),
    "SaaS Business Owner": (
        "tenant.read", "saas.crm.read", "saas.sales.read", "saas.pricing.read",
        "saas.finance.read", "saas.customer_success.read", "saas.platform.read",
        "saas.audit.read", "reports.read",
    ),
    "Sales Operations": (
        "saas.sales.read", "saas.sales.manage", "saas.sales.export",
        "saas.pricing.read", "saas.team.read",
    ),
    "Sales Viewer": ("saas.sales.read", "saas.pricing.read"),
    "SaaS Finance Administrator": (
        "saas.finance.read", "saas.finance.manage", "saas.pricing.read",
    ),
    "Customer Success Manager": (
        "saas.sales.read", "saas.pricing.read", "saas.customer_success.read",
        "saas.customer_success.manage", "saas.customer_users.read",
    ),
}


def _ensure_role(conn, tenant_id, name, role_kind: str):
    role_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE tenant_id=:tenant_id AND name=:name"),
        {"tenant_id": tenant_id, "name": name},
    ).scalar()
    if role_id is None:
        role_id = uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO roles (id, tenant_id, name, description, role_kind)
                VALUES (:id, :tenant_id, :name, :description, :role_kind)
                """
            ),
            {
                "id": role_id,
                "tenant_id": tenant_id,
                "name": name,
                "description": f"Kalam {role_kind} role: {name}",
                "role_kind": role_kind,
            },
        )
    return role_id


def _ensure_grants(conn, role_id, keys, permission_ids):
    for key in keys:
        permission_id = permission_ids.get(key)
        if permission_id is None:
            raise RuntimeError(f"Role catalogue references missing permission: {key}")
        conn.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT :role_id, :permission_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM role_permissions
                    WHERE role_id=:role_id AND permission_id=:permission_id
                )
                """
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )


def upgrade() -> None:
    conn = op.get_bind()

    for key, description in PERMISSION_DESCRIPTIONS.items():
        conn.execute(
            sa.text(
                """
                INSERT INTO permissions (id, key, description)
                VALUES (:id, :key, :description)
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {"id": uuid4(), "key": key, "description": description},
        )

    permission_ids = {
        row.key: row.id
        for row in conn.execute(sa.text("SELECT id, key FROM permissions")).fetchall()
    }

    customer_tenants = conn.execute(
        sa.text(
            """
            SELECT id
            FROM tenants
            WHERE slug <> 'kalam'
              AND COALESCE(settings->>'workspace_type', '') <> 'saas_operations'
            """
        )
    ).fetchall()
    for (tenant_id,) in customer_tenants:
        for name, keys in TENANT_ROLE_PERMISSIONS.items():
            role_id = _ensure_role(conn, tenant_id, name, "predefined")
            _ensure_grants(conn, role_id, keys, permission_ids)

    ops_tenant_id = conn.execute(
        sa.text(
            """
            SELECT id
            FROM tenants
            WHERE COALESCE(settings->>'workspace_type', '') = 'saas_operations'
               OR slug = 'kalam'
            ORDER BY CASE
                WHEN COALESCE(settings->>'workspace_type', '') = 'saas_operations' THEN 0
                ELSE 1
            END
            LIMIT 1
            """
        )
    ).scalar()
    if ops_tenant_id is not None:
        for name, keys in PLATFORM_ROLE_PERMISSIONS.items():
            role_id = _ensure_role(conn, ops_tenant_id, name, "platform")
            _ensure_grants(conn, role_id, keys, permission_ids)


def downgrade() -> None:
    # Deliberately non-destructive: these roles may have been assigned after
    # deployment. Removing grants could lock out active administrators.
    pass
