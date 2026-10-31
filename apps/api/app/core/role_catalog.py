"""Canonical Kalam tenant and SaaS operations role catalogue.

These grants are defaults for newly provisioned roles. API handlers must still
apply tenant/resource scoping; a permission grant is not a substitute for it.
"""

PERMISSION_DESCRIPTIONS: dict[str, str] = {
    "tenant.read": "View the current tenant and its configuration",
    "tenant.manage": "Manage the current tenant configuration",
    "users.read": "View authorized workforce profiles",
    "users.manage": "Manage authorized workforce users and invitations",
    "courses.read": "View learning courses",
    "courses.manage": "Create and manage learning courses",
    "learning.access": "Access assigned learning experiences",
    "assessments.manage": "Manage and grade learning assessments",
    "certificates.manage": "Manage credentials and certificates",
    "compliance.manage": "Manage compliance requirements and assignments",
    "skills.manage": "Manage skills and competency frameworks",
    "capabilities.read": "View capability frameworks",
    "capabilities.manage": "Manage capability frameworks",
    "development.manage": "Manage development plans within authorized scope",
    "reports.read": "View reports within authorized scope",
    "reports.manage": "Create and manage saved reports and schedules",
    "audit.read": "View tenant audit records",
    "files.read": "View governed files and evidence",
    "files.manage": "Manage governed file controls",
    "integrations.manage": "Manage tenant integrations",
    "ai.manage": "Manage governed AI settings",
    "reassessment.manage": "Manage capability reassessment workflows",
    "capability_gaps.read": "View capability gaps within authorized scope",
    "capability_risk.read": "View capability risk within authorized scope",
    "capability_assessments.read": "View capability assessments within authorized scope",
    "capability_assessments.execute": "Complete assigned capability assessments",
    "evidence.read": "View capability evidence within authorized scope",
    "saas.crm.read": "View Kalam SaaS commercial CRM records",
    "saas.crm.manage": "Manage Kalam SaaS commercial CRM records",
    "saas.platform.read": "View SaaS platform administration",
    "saas.platform.manage": "Manage SaaS platform administration",
    "saas.tenants.manage": "Provision and administer customer tenants",
    "saas.roles.manage": "Create and govern customer-tenant roles",
    "saas.team.manage": "Manage internal SaaS operations team members",
    "saas.pricing.manage": "Manage SaaS plans, pricing and offers",
    "saas.billing.manage": "Manage subscriptions, invoices and payments",
    "saas.access.revoke": "Revoke customer and SaaS team account access",
    "saas.audit.read": "View SaaS platform audit activity",
}

TENANT_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Tenant Owner": (
        "tenant.read", "reports.read", "audit.read",
    ),
    "Tenant Administrator": (
        "tenant.read", "tenant.manage", "users.read", "users.manage",
        "reports.read", "audit.read", "integrations.manage",
        "capabilities.read", "capabilities.manage",
    ),
    "HR / People Administrator": (
        "users.read", "users.manage", "reports.read", "compliance.manage",
        "capabilities.read", "development.manage",
    ),
    "L&D Administrator": (
        "courses.read", "courses.manage", "learning.access", "assessments.manage",
        "certificates.manage", "reports.read", "skills.manage", "capabilities.read",
        "capabilities.manage", "development.manage", "users.read",
        "compliance.manage", "reassessment.manage",
    ),
    "Manager": (
        "users.read", "courses.read", "learning.access", "reports.read",
        "development.manage", "capabilities.read", "capability_gaps.read",
        "capability_risk.read", "capability_assessments.read",
        "capability_assessments.execute",
    ),
    "Instructor": (
        "courses.read", "learning.access", "assessments.manage",
    ),
    "Learner / Employee": (
        "courses.read", "learning.access", "development.manage",
        "capability_assessments.read", "capability_assessments.execute",
    ),
    "HR Business Partner": (
        "users.read", "reports.read", "development.manage", "capabilities.read",
        "capability_gaps.read", "capability_risk.read",
    ),
    "Quality & Compliance": (
        "users.read", "courses.read", "learning.access", "compliance.manage",
        "reports.read", "audit.read", "files.read", "evidence.read",
    ),
    "Auditor": (
        "reports.read", "audit.read", "files.read", "evidence.read",
    ),
    # Regional data isolation is not yet represented in the current API model.
    # This role is deliberately limited to reporting until regional row-level
    # authorization is implemented and tested.
    "Regional Executive": (
        "reports.read",
    ),
    "Global Executive": (
        "tenant.read", "users.read", "courses.read", "learning.access",
        "reports.read", "audit.read", "compliance.manage", "skills.manage",
        "capabilities.read", "development.manage", "capability_gaps.read",
        "capability_risk.read",
    ),
}

PLATFORM_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    # Platform Developer is a separate engineering/support role; its elevated
    # behavior is recognized explicitly by app.api.deps.is_platform_developer.
    "Platform Developer": (),
    "SaaS Super Admin": (
        "tenant.read", "tenant.manage", "users.read", "users.manage",
        "saas.crm.read", "saas.crm.manage", "saas.platform.read",
        "saas.platform.manage", "saas.tenants.manage", "saas.roles.manage",
        "saas.team.manage", "saas.pricing.manage", "saas.billing.manage",
        "saas.access.revoke", "saas.audit.read", "audit.read",
    ),
    "SaaS Administrator": (
        "tenant.read", "tenant.manage", "users.read", "users.manage",
        "saas.crm.read", "saas.crm.manage",
    ),
    "SaaS Business Owner": (
        "tenant.read", "saas.crm.read", "saas.audit.read", "reports.read",
    ),
    "Sales Operations": (
        "tenant.read", "saas.crm.read", "saas.crm.manage",
    ),
    "Sales Viewer": (
        "tenant.read", "saas.crm.read",
    ),
    "SaaS Finance Administrator": (
        "tenant.read", "saas.crm.read", "saas.crm.manage",
        "saas.pricing.manage", "saas.billing.manage",
    ),
    "Customer Success Manager": (
        "tenant.read", "saas.crm.read", "saas.crm.manage",
        "saas.tenants.manage",
    ),
}
