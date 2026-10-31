from app.core.role_catalog import (
    PERMISSION_DESCRIPTIONS,
    PLATFORM_ROLE_PERMISSIONS,
    TENANT_ROLE_PERMISSIONS,
)


def test_role_catalog_references_only_declared_permissions() -> None:
    declared = set(PERMISSION_DESCRIPTIONS)
    for grants in (*TENANT_ROLE_PERMISSIONS.values(), *PLATFORM_ROLE_PERMISSIONS.values()):
        assert set(grants) <= declared


def test_role_catalog_has_unique_role_names_across_security_domains() -> None:
    assert len(TENANT_ROLE_PERMISSIONS) == len(set(TENANT_ROLE_PERMISSIONS))
    assert len(PLATFORM_ROLE_PERMISSIONS) == len(set(PLATFORM_ROLE_PERMISSIONS))
    assert set(TENANT_ROLE_PERMISSIONS).isdisjoint(PLATFORM_ROLE_PERMISSIONS)


def test_sensitive_role_boundaries_are_explicit() -> None:
    assert "users.read" not in TENANT_ROLE_PERMISSIONS["Manager"]
    assert "reports.read" not in TENANT_ROLE_PERMISSIONS["Manager"]
    assert "reports.export.people" not in TENANT_ROLE_PERMISSIONS["L&D Administrator"]
    assert "reports.read" not in TENANT_ROLE_PERMISSIONS["Auditor"]
    assert TENANT_ROLE_PERMISSIONS["Regional Executive"] == ()
    assert "saas.finance.manage" not in PLATFORM_ROLE_PERMISSIONS["Sales Operations"]
    assert "saas.sales.manage" not in PLATFORM_ROLE_PERMISSIONS["SaaS Finance Administrator"]


def test_instructor_grading_is_separate_from_assessment_authoring() -> None:
    assert "assessments.grade_assigned" in TENANT_ROLE_PERMISSIONS["Instructor"]
    assert "assessments.manage" not in TENANT_ROLE_PERMISSIONS["Instructor"]
