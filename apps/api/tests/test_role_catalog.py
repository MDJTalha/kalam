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


def test_manager_has_direct_report_scope_not_tenant_wide_directory_or_reports():
    grants = set(TENANT_ROLE_PERMISSIONS["Manager"])
    assert "team.read" in grants
    assert "users.read" not in grants
    assert "reports.read" not in grants


def test_regional_executive_has_no_unscoped_data_grants():
    # No regional-to-org-unit assignment or cross-screen row filter exists yet.
    assert TENANT_ROLE_PERMISSIONS["Regional Executive"] == ()


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


def test_saas_sales_and_finance_are_segregated():
    sales_ops = set(PLATFORM_ROLE_PERMISSIONS["Sales Operations"])
    sales_viewer = set(PLATFORM_ROLE_PERMISSIONS["Sales Viewer"])
    finance = set(PLATFORM_ROLE_PERMISSIONS["SaaS Finance Administrator"])
    assert {"saas.sales.read", "saas.sales.manage"} <= sales_ops
    assert "saas.finance.read" not in sales_ops
    assert "saas.finance.manage" not in sales_ops
    assert "saas.finance.read" not in sales_viewer
    assert "saas.finance.manage" not in sales_viewer
    assert {"saas.finance.read", "saas.finance.manage"} <= finance
    assert "saas.sales.manage" not in finance


def test_saas_administrator_is_not_a_commercial_superuser():
    grants = set(PLATFORM_ROLE_PERMISSIONS["SaaS Administrator"])
    assert {"saas.platform.read", "saas.platform.manage", "saas.team.manage"} <= grants
    assert "saas.crm.manage" not in grants
    assert "saas.finance.manage" not in grants


def test_customer_success_cannot_read_finance():
    grants = set(PLATFORM_ROLE_PERMISSIONS["Customer Success Manager"])
    assert {"saas.customer_success.read", "saas.customer_success.manage"} <= grants
    assert "saas.finance.read" not in grants
    assert "saas.finance.manage" not in grants


def test_employee_identifiable_exports_are_granted_only_to_workforce_admin_roles():
    assert "reports.export.people" in TENANT_ROLE_PERMISSIONS["Tenant Administrator"]
    assert "reports.export.people" in TENANT_ROLE_PERMISSIONS["HR / People Administrator"]
    assert "reports.export.people" not in TENANT_ROLE_PERMISSIONS["Tenant Owner"]
    assert "reports.export.people" not in TENANT_ROLE_PERMISSIONS["Global Executive"]
    assert "reports.export.learning" in TENANT_ROLE_PERMISSIONS["L&D Administrator"]
    assert "reports.export.learning" not in TENANT_ROLE_PERMISSIONS["Auditor"]


def test_hrbp_and_quality_roles_are_limited_to_their_job_scope():
    hrbp = set(TENANT_ROLE_PERMISSIONS["HR Business Partner"])
    assert {"team.read", "development.manage"} <= hrbp
    assert "users.read" not in hrbp
    assert "reports.read" not in hrbp

    quality = set(TENANT_ROLE_PERMISSIONS["Quality & Compliance"])
    assert {"compliance.manage", "audit.read", "files.read", "evidence.read"} <= quality
    assert "users.read" not in quality
    assert "reports.read" not in quality


def test_sales_export_is_a_separate_grant():
    assert "saas.sales.export" in PLATFORM_ROLE_PERMISSIONS["Sales Operations"]
    assert "saas.sales.export" in PLATFORM_ROLE_PERMISSIONS["SaaS Super Admin"]
    assert "saas.sales.export" not in PLATFORM_ROLE_PERMISSIONS["Sales Viewer"]
