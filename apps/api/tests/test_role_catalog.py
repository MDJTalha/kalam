from app.core.role_catalog import (
    PERMISSION_DESCRIPTIONS,
    PLATFORM_ROLE_PERMISSIONS,
    TENANT_ROLE_PERMISSIONS,
)


def test_every_role_permission_has_a_description():
    referenced = {
        permission
        for role_permissions in (
            *TENANT_ROLE_PERMISSIONS.values(),
            *PLATFORM_ROLE_PERMISSIONS.values(),
        )
        for permission in role_permissions
    }
    assert referenced <= set(PERMISSION_DESCRIPTIONS)


def test_customer_roles_never_receive_saas_platform_permissions():
    for role_name, permission_keys in TENANT_ROLE_PERMISSIONS.items():
        assert not any(key.startswith("saas.") for key in permission_keys), role_name


def test_saas_super_admin_has_explicit_platform_governance_rights():
    grants = set(PLATFORM_ROLE_PERMISSIONS["SaaS Super Admin"])
    assert {
        "saas.crm.read",
        "saas.crm.manage",
        "saas.tenants.manage",
        "saas.roles.manage",
        "saas.team.manage",
        "saas.pricing.manage",
        "saas.billing.manage",
        "saas.access.revoke",
        "saas.audit.read",
    } <= grants


def test_saas_super_admin_is_separate_from_platform_developer():
    assert PLATFORM_ROLE_PERMISSIONS["Platform Developer"] == ()
    assert PLATFORM_ROLE_PERMISSIONS["SaaS Super Admin"]


def test_regional_executive_does_not_receive_unscoped_people_access():
    # Until regional row-level filters exist, this role must not receive the
    # tenant-wide users.read grant.
    assert "users.read" not in TENANT_ROLE_PERMISSIONS["Regional Executive"]


def test_core_business_roles_are_present():
    assert {
        "Tenant Owner",
        "Tenant Administrator",
        "HR / People Administrator",
        "L&D Administrator",
        "Manager",
        "Instructor",
        "Learner / Employee",
        "HR Business Partner",
        "Quality & Compliance",
        "Auditor",
        "Regional Executive",
        "Global Executive",
    } <= set(TENANT_ROLE_PERMISSIONS)

    assert {
        "Platform Developer",
        "SaaS Super Admin",
        "SaaS Administrator",
        "SaaS Business Owner",
        "Sales Operations",
        "Sales Viewer",
        "SaaS Finance Administrator",
        "Customer Success Manager",
    } <= set(PLATFORM_ROLE_PERMISSIONS)
