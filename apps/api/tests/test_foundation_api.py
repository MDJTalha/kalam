from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
MANAGER = {"email": "manager@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}
DEMO_COURSE_SLUG = "workplace-ethics-2026"


@pytest.fixture(scope="session", autouse=True)
def webhook_encryption_test_config():
    settings.webhook_encryption_keys = f"test:{Fernet.generate_key().decode('ascii')}"
    settings.webhook_active_key_id = "test"


@pytest.fixture
def client():
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


def login(client: TestClient, credentials: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, **credentials},
    )
    assert response.status_code == 200, response.text


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rejected_origin_keeps_security_headers(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/forgot-password",
        headers={"Origin": "https://untrusted.invalid"},
        json={"tenant_slug": TENANT, "email": ADMIN["email"]},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Origin not allowed"}
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]


def test_login_is_tenant_scoped(client: TestClient) -> None:
    good = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, **ADMIN},
    )
    assert good.status_code == 200
    assert good.cookies.get("corp_lms_session")

    wrong = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "not-a-real-tenant", **ADMIN},
    )
    assert wrong.status_code == 401


def test_auth_discovery_does_not_enumerate_unknown_tenant(client: TestClient) -> None:
    unknown = client.get("/api/v1/auth/discovery/not-a-real-tenant")
    assert unknown.status_code == 200
    payload = unknown.json()
    assert payload["recognized"] is False
    assert payload["tenant_name"] is None
    assert payload["sso_providers"] == []


def test_auth_discovery_recognizes_demo_tenant(client: TestClient) -> None:
    response = client.get(f"/api/v1/auth/discovery/{TENANT}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["recognized"] is True
    assert payload["tenant_slug"] == TENANT
    assert payload["password_available"] is True


def test_global_search_respects_people_permission(client: TestClient) -> None:
    login(client, LEARNER)
    assert client.get("/api/v1/search", params={"q": "   "}).status_code == 422
    private_result = client.get("/api/v1/search", params={"q": ADMIN["email"]})
    assert private_result.status_code == 200
    assert private_result.json()["people"] == []
    login(client, ADMIN)
    admin_result = client.get("/api/v1/search", params={"q": ADMIN["email"]})
    assert admin_result.status_code == 200
    assert any(person["email"] == ADMIN["email"] for person in admin_result.json()["people"])


def test_people_directory_page_is_bounded_and_permissioned(client: TestClient) -> None:
    login(client, LEARNER)
    assert client.get("/api/v1/people/page").status_code == 403
    login(client, ADMIN)
    first = client.get("/api/v1/people/page", params={"page": 1, "page_size": 1})
    second = client.get("/api/v1/people/page", params={"page": 2, "page_size": 1})
    assert first.status_code == second.status_code == 200
    assert len(first.json()["items"]) == len(second.json()["items"]) == 1
    assert first.json()["items"][0]["id"] != second.json()["items"][0]["id"]
    assert first.json()["total"] == second.json()["total"] >= 2
    match = client.get("/api/v1/people/page", params={"q": ADMIN["email"]})
    assert match.status_code == 200
    assert any(person["email"] == ADMIN["email"] for person in match.json()["items"])
    assert client.get("/api/v1/people/page", params={"page_size": 101}).status_code == 422


def test_skills_page_is_bounded_searchable_and_tenant_scoped(client: TestClient) -> None:
    login(client, LEARNER)
    first = client.get("/api/v1/skills/page", params={"page": 1, "page_size": 1, "q": "Ethical"})
    assert first.status_code == 200, first.text
    payload = first.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["total"] >= 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "Ethical Decision Making"
    assert client.get("/api/v1/skills/page", params={"page_size": 101}).status_code == 422


def test_compliance_reference_pages_are_bounded(client: TestClient) -> None:
    login(client, ADMIN)
    requirements = client.get("/api/v1/compliance/page", params={"page": 1, "page_size": 1, "q": "Annual Ethics"})
    assert requirements.status_code == 200, requirements.text
    requirement_payload = requirements.json()
    assert requirement_payload["total"] >= 1
    assert len(requirement_payload["items"]) == 1
    assert requirement_payload["items"][0]["name"] == "Annual Ethics Training"
    assert client.get("/api/v1/compliance/page", params={"page_size": 101}).status_code == 422

    courses = client.get("/api/v1/compliance/courses/page", params={"page": 1, "page_size": 1, "q": "Workplace"})
    assert courses.status_code == 200, courses.text
    course_payload = courses.json()
    assert course_payload["total"] >= 1
    assert len(course_payload["items"]) == 1
    assert course_payload["items"][0]["title"] == "Workplace Ethics & Responsible Conduct"
    assert client.get("/api/v1/compliance/courses/page", params={"page_size": 101}).status_code == 422


def test_organization_reference_pages_are_bounded(client: TestClient) -> None:
    login(client, ADMIN)

    roles = client.get("/api/v1/organization/roles/page", params={"page": 1, "page_size": 1})
    assert roles.status_code == 200, roles.text
    assert len(roles.json()["items"]) <= 1
    assert roles.json()["page_size"] == 1
    assert client.get("/api/v1/organization/roles/page", params={"page_size": 101}).status_code == 422

    units = client.get("/api/v1/organization/units/page", params={"page": 1, "page_size": 1})
    assert units.status_code == 200, units.text
    assert len(units.json()["items"]) <= 1
    assert units.json()["page_size"] == 1
    assert client.get("/api/v1/organization/units/page", params={"page_size": 101}).status_code == 422


def test_capability_framework_reference_pages_are_bounded(client: TestClient) -> None:
    login(client, ADMIN)

    objectives = client.get(
        "/api/v1/capability-domain/objectives/page",
        params={"page": 1, "page_size": 1},
    )
    assert objectives.status_code == 200, objectives.text
    objective_payload = objectives.json()
    assert objective_payload["page"] == 1
    assert objective_payload["page_size"] == 1
    assert len(objective_payload["items"]) <= 1
    assert client.get(
        "/api/v1/capability-domain/objectives/page",
        params={"page_size": 101},
    ).status_code == 422

    capabilities = client.get(
        "/api/v1/capabilities/page",
        params={"page": 1, "page_size": 1},
    )
    assert capabilities.status_code == 200, capabilities.text
    capability_payload = capabilities.json()
    assert capability_payload["page"] == 1
    assert capability_payload["page_size"] == 1
    assert len(capability_payload["items"]) <= 1
    assert client.get(
        "/api/v1/capabilities/page",
        params={"page_size": 101},
    ).status_code == 422


def test_authenticated_profile_is_available(client: TestClient) -> None:
    login(client, LEARNER)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == LEARNER["email"]


def test_learner_can_view_courses_but_cannot_manage_them(client: TestClient) -> None:
    login(client, LEARNER)
    courses = client.get("/api/v1/courses")
    assert courses.status_code == 200
    assert any(item["slug"] == DEMO_COURSE_SLUG for item in courses.json())

    forbidden = client.post(
        "/api/v1/courses",
        json={
            "title": "Unauthorized Course",
            "slug": "unauthorized-course",
            "description": "Should never be created by a learner.",
        },
    )
    assert forbidden.status_code == 403


def test_course_catalog_page_is_bounded_searchable_and_tenant_scoped(client: TestClient) -> None:
    login(client, LEARNER)
    page = client.get("/api/v1/courses/page", params={"page": 1, "page_size": 1, "q": "workplace"})
    assert page.status_code == 200, page.text
    payload = page.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["total"] >= 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["slug"] == DEMO_COURSE_SLUG
    assert "enrollment_status" in payload["items"][0]
    by_id = client.get("/api/v1/courses/page", params={"course_ids": payload["items"][0]["id"]})
    assert by_id.status_code == 200, by_id.text
    assert [item["id"] for item in by_id.json()["items"]] == [payload["items"][0]["id"]]

    invalid = client.get("/api/v1/courses/page", params={"page_size": 101})
    assert invalid.status_code == 422

    invalid_scope = client.get("/api/v1/courses/page", params={"scope": "all-tenants"})
    assert invalid_scope.status_code == 422

    login(client, ADMIN)
    drafts = client.get("/api/v1/courses/page", params={"manage": "true", "status": "draft", "page_size": 10})
    assert drafts.status_code == 200, drafts.text
    assert all(item["status"] == "draft" for item in drafts.json()["items"])
    invalid_status = client.get("/api/v1/courses/page", params={"manage": "true", "status": "hidden"})
    assert invalid_status.status_code == 422


def test_learner_can_enroll_idempotently(client: TestClient) -> None:
    login(client, LEARNER)
    courses = client.get("/api/v1/courses").json()
    course = next(item for item in courses if item["slug"] == DEMO_COURSE_SLUG)

    first = client.post(f"/api/v1/courses/{course['id']}/enroll")
    second = client.post(f"/api/v1/courses/{course['id']}/enroll")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_reports_require_permission(client: TestClient) -> None:
    login(client, LEARNER)
    forbidden = client.get("/api/v1/reports/summary")
    assert forbidden.status_code == 403

    login(client, ADMIN)
    summary = client.get("/api/v1/reports/summary")
    assert summary.status_code == 200
    assert summary.json()["users"] >= 4
    assert summary.json()["courses"] >= 1


def test_learner_can_complete_seeded_course_and_earn_credential(client: TestClient) -> None:
    login(client, LEARNER)
    courses = client.get("/api/v1/courses").json()
    course = next(item for item in courses if item["slug"] == DEMO_COURSE_SLUG)

    enrolled = client.post(f"/api/v1/courses/{course['id']}/enroll")
    assert enrolled.status_code == 200
    enrollment_id = enrolled.json()["id"]

    detail = client.get(f"/api/v1/courses/{course['id']}")
    assert detail.status_code == 200
    lesson = detail.json()["modules"][0]["lessons"][0]

    completed = client.post(
        f"/api/v1/courses/my/enrollments/{enrollment_id}/lessons/{lesson['id']}/complete"
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    assessments = client.get("/api/v1/assessments").json()
    assessment = next(item for item in assessments if item["title"] == "Ethics Knowledge Check")
    assessment_detail = client.get(f"/api/v1/assessments/{assessment['id']}")
    question = assessment_detail.json()["questions"][0]

    submitted = client.post(
        f"/api/v1/assessments/{assessment['id']}/submit",
        json={"answers": {question["id"]: "Transparency"}},
    )
    assert submitted.status_code == 200
    assert submitted.json()["passed"] is True

    certificates = client.get("/api/v1/certificates/my")
    assert certificates.status_code == 200
    certificate = next(item for item in certificates.json() if item["course"] == course["title"])
    verification = client.get(f"/api/v1/certificates/verify/{certificate['verification_code']}")
    assert verification.status_code == 200
    assert verification.json()["valid"] is True


def test_assessment_manual_grade_override_is_audited(client: TestClient) -> None:
    login(client, LEARNER)
    courses = client.get("/api/v1/courses").json()
    course = next(item for item in courses if item["slug"] == DEMO_COURSE_SLUG)
    enrollment = client.post(f"/api/v1/courses/{course['id']}/enroll").json()
    detail = client.get(f"/api/v1/courses/{course['id']}").json()
    lesson = detail["modules"][0]["lessons"][0]
    completed = client.post(
        f"/api/v1/courses/my/enrollments/{enrollment['id']}/lessons/{lesson['id']}/complete"
    )
    assert completed.status_code == 200
    assessment = next(
        item for item in client.get("/api/v1/assessments").json()
        if item["title"] == "Ethics Knowledge Check"
    )
    question = client.get(f"/api/v1/assessments/{assessment['id']}").json()["questions"][0]
    submitted = client.post(
        f"/api/v1/assessments/{assessment['id']}/submit",
        json={"answers": {question["id"]: "Not the stored answer"}},
    )
    assert submitted.status_code == 200
    attempt_id = submitted.json()["attempt_id"]
    login(client, ADMIN)
    overridden = client.patch(
        f"/api/v1/assessments/attempts/{attempt_id}/grade",
        json={
            "score": 90,
            "passed": True,
            "feedback": "Reviewed by an assessor.",
            "reason": "Manual review identified an acceptable response.",
        },
    )
    assert overridden.status_code == 200
    attempts = client.get(f"/api/v1/assessments/{assessment['id']}/attempts")
    assert attempts.status_code == 200
    row = next(item for item in attempts.json() if item["id"] == str(attempt_id))
    assert row["grade_override"] is True
    assert row["score"] == 90
    assert row["passed"] is True


def test_admin_can_unlock_a_locked_account(client: TestClient) -> None:
    login(client, LEARNER)
    profile = client.get("/api/v1/auth/me").json()
    for _ in range(5):
        failed = client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": TENANT, "email": LEARNER["email"], "password": "Wrong!123456"},
        )
        assert failed.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, **LEARNER},
    )
    assert blocked.status_code == 401

    login(client, ADMIN)
    unlocked = client.patch(
        f"/api/v1/admin/users/{profile['id']}",
        json={"unlock_now": True},
    )
    assert unlocked.status_code == 200

    login(client, LEARNER)
    assert client.get("/api/v1/auth/me").status_code == 200

def test_security_headers_are_present(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_untrusted_host_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"host": "evil.example"})
    assert response.status_code == 400


def test_cross_tenant_data_isolation(client: TestClient) -> None:
    login(client, ADMIN)
    courses = client.get("/api/v1/courses").json()
    demo_course_id = courses[0]["id"]

    other = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "isolation-corporation",
            "email": "isolated@other.corp",
            "password": "DemoOnly!1234",
        },
    )
    assert other.status_code == 200

    other_detail = client.get(f"/api/v1/courses/{demo_course_id}")
    assert other_detail.status_code == 404

    other_people = client.get("/api/v1/people")
    assert other_people.status_code == 403

    login(client, ADMIN)
    assert client.get(f"/api/v1/courses/{demo_course_id}").status_code == 200


def test_search_reports_and_tenant_settings(client: TestClient) -> None:
    login(client, ADMIN)

    search = client.get("/api/v1/search", params={"q": "Ethics"})
    assert search.status_code == 200
    assert any(item["title"] == "Workplace Ethics & Responsible Conduct" for item in search.json()["courses"])

    people_csv = client.get("/api/v1/reports/export/people")
    assert people_csv.status_code == 200
    assert "text/csv" in people_csv.headers["content-type"]
    assert "Employee Number" in people_csv.text

    current = client.get("/api/v1/admin/tenant-settings")
    assert current.status_code == 200

    updated = client.patch(
        "/api/v1/admin/tenant-settings",
        json={"settings": {"timezone": "Asia/Karachi", "default_language": "en"}},
    )
    assert updated.status_code == 200
    assert updated.json()["settings"]["timezone"] == "Asia/Karachi"

    refreshed = client.get("/api/v1/admin/tenant-settings")
    assert refreshed.json()["settings"]["default_language"] == "en"


def test_authenticated_module_surface_smoke(client: TestClient) -> None:
    login(client, ADMIN)
    endpoints = [
        "/api/v1/people",
        "/api/v1/people/me",
        "/api/v1/people/team",
        "/api/v1/admin/roles",
        "/api/v1/admin/org-units",
        "/api/v1/programs",
        "/api/v1/programs/cohorts",
        "/api/v1/skills",
        "/api/v1/development/my",
        "/api/v1/compliance",
        "/api/v1/assessments",
        "/api/v1/certificates/my",
        "/api/v1/notifications",
        "/api/v1/sessions",
        "/api/v1/search?q=Ethics",
        "/api/v1/integrations",
        "/api/v1/files",
        "/api/v1/webhooks",
    ]
    for path in endpoints:
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.text}"


def test_readiness_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "ok"}


def test_session_management_is_user_scoped(client: TestClient) -> None:
    login(client, LEARNER)
    sessions = client.get("/api/v1/auth/sessions")
    assert sessions.status_code == 200
    current = next(item for item in sessions.json() if item["is_current"])
    cannot_revoke_current = client.delete(f"/api/v1/auth/sessions/{current['id']}")
    assert cannot_revoke_current.status_code == 400
    revoked = client.post("/api/v1/auth/sessions/revoke-others")
    assert revoked.status_code == 200


def test_admin_user_lifecycle_rejects_cross_tenant_or_missing_targets(client: TestClient) -> None:
    login(client, ADMIN)
    missing = client.patch(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000000",
        json={"is_active": False},
    )
    assert missing.status_code == 404
    missing_role = client.post(
        "/api/v1/organization/users/00000000-0000-0000-0000-000000000000/roles/00000000-0000-0000-0000-000000000000",
    )
    assert missing_role.status_code == 404

def test_phase1_permission_matrix_core_admin_endpoints(client: TestClient) -> None:
    login(client, LEARNER)
    for path in (
        "/api/v1/admin/roles",
        "/api/v1/admin/tenant-settings",
        "/api/v1/admin/audit",
        "/api/v1/organization/roles",
    ):
        response = client.get(path)
        assert response.status_code == 403, path

    login(client, ADMIN)
    assert client.get("/api/v1/admin/roles").status_code == 200
    assert client.get("/api/v1/admin/tenant-settings").status_code == 200
    assert client.get("/api/v1/admin/audit").status_code == 200
    assert client.get("/api/v1/organization/roles").status_code == 200


def test_phase1_cross_tenant_resource_ids_are_not_resolvable(client: TestClient) -> None:
    login(client, ADMIN)

    course_id = client.get("/api/v1/courses").json()[0]["id"]
    assessment_id = client.get("/api/v1/assessments").json()[0]["id"]
    role_id = client.get("/api/v1/organization/roles").json()[0]["id"]
    _skill_id = client.get("/api/v1/skills").json()[0]["id"]
    programs = client.get("/api/v1/programs").json()
    paths = client.get("/api/v1/programs/paths/all").json()

    isolated = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "isolation-corporation",
            "email": "isolated@other.corp",
            "password": "DemoOnly!1234",
        },
    )
    assert isolated.status_code == 200

    checks = [
        f"/api/v1/courses/{course_id}",
        f"/api/v1/assessments/{assessment_id}",
        f"/api/v1/skills/role/{role_id}",
    ]
    if programs:
        checks.append(f"/api/v1/programs/{programs[0]['id']}")
    if paths:
        checks.append(f"/api/v1/programs/paths/{paths[0]['id']}")
    for path in checks:
        response = client.get(path)
        assert response.status_code in {403, 404}, f"{path}: {response.status_code} {response.text}"

    assert client.get(f"/api/v1/skills/course/{course_id}").status_code == 404


def test_phase1_user_target_is_tenant_scoped(client: TestClient) -> None:
    login(client, ADMIN)
    missing = "00000000-0000-0000-0000-000000000000"
    response = client.patch(f"/api/v1/admin/users/{missing}", json={"job_title": "Should not update"})
    assert response.status_code == 404

def test_phase1_privileged_endpoint_matrix_denies_learner(client: TestClient) -> None:
    login(client, LEARNER)
    privileged = [
        ("GET", "/api/v1/admin/roles"),
        ("GET", "/api/v1/admin/permissions"),
        ("GET", "/api/v1/admin/audit"),
        ("GET", "/api/v1/admin/tenant-settings"),
        ("POST", "/api/v1/admin/invitations"),
        ("POST", "/api/v1/admin/org-units"),
        ("GET", "/api/v1/organization/roles"),
        ("POST", "/api/v1/organization/units"),
        ("POST", "/api/v1/courses"),
        ("POST", "/api/v1/assessments"),
        ("POST", "/api/v1/compliance"),
        ("POST", "/api/v1/skills"),
        ("POST", "/api/v1/files"),
        ("POST", "/api/v1/sessions"),
        ("PUT", "/api/v1/integrations/example"),
        ("POST", "/api/v1/webhooks"),
    ]
    for method, path in privileged:
        response = client.request(method, path, json={})
        assert response.status_code == 403, f"{method} {path}: {response.status_code} {response.text}"


def test_phase1_permission_catalog_covers_all_route_guards(client: TestClient) -> None:
    login(client, ADMIN)
    response = client.get("/api/v1/admin/permissions")
    assert response.status_code == 200
    catalog = {item["key"] for item in response.json()}
    expected = {
        "tenant.read", "tenant.manage", "users.read", "users.manage",
        "courses.read", "courses.manage", "learning.access",
        "assessments.manage", "certificates.manage", "compliance.manage",
        "skills.manage", "development.manage", "reports.read", "audit.read",
        "files.read", "files.manage", "integrations.manage", "ai.manage",
    }
    assert expected.issubset(catalog)


def test_phase1_protected_file_and_org_surfaces_require_permissions(client: TestClient) -> None:
    login(client, LEARNER)
    assert client.get("/api/v1/admin/org-units").status_code == 403
    assert client.get("/api/v1/files").status_code == 403

    login(client, ADMIN)
    assert client.get("/api/v1/admin/org-units").status_code == 200
    assert client.get("/api/v1/files").status_code == 200


def test_phase1_role_permission_matrix_is_tenant_scoped_and_protected(client: TestClient) -> None:
    login(client, LEARNER)
    forbidden = client.get("/api/v1/admin/permissions")
    assert forbidden.status_code == 403

    login(client, ADMIN)
    permissions = client.get("/api/v1/admin/permissions")
    assert permissions.status_code == 200
    assert any(item["key"] == "users.manage" for item in permissions.json())

    roles = client.get("/api/v1/admin/roles")
    assert roles.status_code == 200
    admin_role = next(item for item in roles.json() if item["name"] == "Tenant Administrator")

    current = client.get(f"/api/v1/admin/roles/{admin_role['id']}/permissions")
    assert current.status_code == 200
    assert "tenant.manage" in current.json()["permission_keys"]

    invalid = client.put(
        f"/api/v1/admin/roles/{admin_role['id']}/permissions",
        json={"permission_keys": ["does.not.exist"]},
    )
    assert invalid.status_code == 403

    unsafe = client.put(
        f"/api/v1/admin/roles/{admin_role['id']}/permissions",
        json={"permission_keys": ["users.read"]},
    )
    assert unsafe.status_code == 403


def test_phase1_self_service_resource_ids_remain_tenant_and_user_scoped(client: TestClient) -> None:
    login(client, LEARNER)
    course = next(item for item in client.get("/api/v1/courses").json() if item["slug"] == DEMO_COURSE_SLUG)
    enrollment = client.post(f"/api/v1/courses/{course['id']}/enroll").json()
    lesson = client.get(f"/api/v1/courses/{course['id']}").json()["modules"][0]["lessons"][0]
    compliance = client.get("/api/v1/compliance/my").json()
    assert compliance
    assignment_id = compliance[0]["id"]
    plan = client.post(
        "/api/v1/development/my",
        json={"title": "Phase 1 tenant boundary proof", "goals": [{"title": "Isolation"}]},
    )
    assert plan.status_code == 201
    plan_id = plan.json()["id"]

    isolated = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": LEARNER["password"]},
    )
    assert isolated.status_code == 200

    complete = client.post(
        f"/api/v1/courses/my/enrollments/{enrollment['id']}/lessons/{lesson['id']}/complete",
    )
    assert complete.status_code == 404

    update_plan = client.patch(
        f"/api/v1/development/my/{plan_id}",
        json={"status": "completed"},
    )
    assert update_plan.status_code == 404

    evidence = client.post(
        f"/api/v1/compliance/my/{assignment_id}/evidence",
        json={"evidence_type": "document", "reference": "tenant-boundary-proof"},
    )
    assert evidence.status_code == 404



def test_phase1_parameterized_resource_family_matrix(client: TestClient) -> None:
    login(client, ADMIN)
    _me = client.get("/api/v1/auth/me").json()
    people = client.get("/api/v1/people").json()
    roles = client.get("/api/v1/organization/roles").json()
    course = next(item for item in client.get("/api/v1/courses").json() if item["slug"] == DEMO_COURSE_SLUG)
    assessment = next(item for item in client.get("/api/v1/assessments").json() if item["title"] == "Ethics Knowledge Check")

    programs = client.get("/api/v1/programs").json()
    if programs:
        program_id = programs[0]["id"]
    else:
        created = client.post(
            "/api/v1/programs",
            json={"title": "Phase 1 Isolation Program", "slug": "phase-1-isolation-program"},
        )
        assert created.status_code == 201
        program_id = created.json()["id"]
        assert client.post(
            f"/api/v1/programs/{program_id}/courses",
            json={"course_id": course["id"], "position": 1, "is_required": True},
        ).status_code == 201

    paths = client.get("/api/v1/programs/paths/all").json()
    if paths:
        path_id = paths[0]["id"]
    else:
        created = client.post(
            "/api/v1/programs/paths",
            json={"title": "Phase 1 Isolation Path", "slug": "phase-1-isolation-path"},
        )
        assert created.status_code == 201
        path_id = created.json()["id"]
        assert client.post(
            f"/api/v1/programs/paths/{path_id}/courses",
            json={"course_id": course["id"], "position": 1},
        ).status_code == 201

    cohorts = client.get("/api/v1/programs/cohorts").json()
    if cohorts:
        cohort_id = cohorts[0]["id"]
    else:
        created = client.post(
            f"/api/v1/programs/{program_id}/cohorts",
            json={"name": "Phase 1 Isolation Cohort", "code": "P1-ISO-01"},
        )
        assert created.status_code == 201
        cohort_id = created.json()["id"]

    sessions = client.get("/api/v1/sessions").json()
    if sessions:
        session_id = sessions[0]["id"]
    else:
        created = client.post(
            "/api/v1/sessions",
            json={
                "course_id": course["id"],
                "title": "Phase 1 Isolation Session",
                "starts_at": "2030-01-01T10:00:00Z",
                "ends_at": "2030-01-01T11:00:00Z",
            },
        )
        assert created.status_code == 201
        session_id = created.json()["id"]

    webhook = client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/corporate-lms-phase1", "event_types": ["test.phase1"]},
    )
    assert webhook.status_code == 201
    webhook_id = webhook.json()["id"]

    integration = client.put(
        "/api/v1/integrations/hris",
        json={"provider": "hris", "status": "configured", "config": {"matrix": "phase1"}},
    )
    assert integration.status_code == 200

    upload = client.post(
        "/api/v1/files",
        files={"upload": ("phase1-boundary.txt", b"phase1 boundary evidence", "text/plain")},
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]

    login(client, LEARNER)
    learner_certificates = client.get("/api/v1/certificates/my").json()
    learner_assessment = client.get(f"/api/v1/assessments/{assessment['id']}").json()
    question = learner_assessment["questions"][0]
    submitted = client.post(
        f"/api/v1/assessments/{assessment['id']}/submit",
        json={"answers": {question["id"]: "Transparency"}},
    )
    assert submitted.status_code == 200
    attempt_id = submitted.json()["attempt_id"]
    certificate_id = submitted.json().get("certificate_id")
    if certificate_id is None:
        learner_certificates = client.get("/api/v1/certificates/my").json()
        certificate_id = learner_certificates[0]["id"] if learner_certificates else None

    login(client, ADMIN)
    compliance = client.get("/api/v1/compliance/my").json()
    assignment_id = compliance[0]["id"] if compliance else None

    isolated = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "isolation-corporation",
            "email": "isolated@other.corp",
            "password": LEARNER["password"],
        },
    )
    assert isolated.status_code == 200

    readable_resource_checks = [
        f"/api/v1/programs/{program_id}",
        f"/api/v1/programs/paths/{path_id}",
        f"/api/v1/programs/cohorts/{cohort_id}",
    ]
    for path in readable_resource_checks:
        response = client.get(path)
        assert response.status_code == 404, f"{path}: {response.status_code} {response.text}"

    privileged_checks = [
        ("PATCH", f"/api/v1/webhooks/{webhook_id}", {"active": False}),
        ("PATCH", f"/api/v1/files/{file_id}/scan-result?clean=true", {}),
        ("PATCH", f"/api/v1/assessments/attempts/{attempt_id}/grade", {"score": 90, "passed": True, "reason": "cross-tenant"}),
        ("PUT", "/api/v1/integrations/hris", {"provider": "hris", "status": "disabled", "config": {}}),
        ("POST", "/api/v1/integrations/hris/disable", {}),
        ("POST", f"/api/v1/sessions/{session_id}/attendance", {"user_id": people[0]["id"], "status": "present"}),
        ("POST", f"/api/v1/organization/users/{people[0]['id']}/roles/{roles[0]['id']}", {}),
        ("DELETE", f"/api/v1/organization/users/{people[0]['id']}/roles/{roles[0]['id']}", {}),
    ]
    if certificate_id:
        privileged_checks.append(("POST", f"/api/v1/certificates/{certificate_id}/revoke", {}))
    if assignment_id:
        privileged_checks.extend([
            ("POST", f"/api/v1/compliance/{assignment_id}/complete", {}),
            ("POST", f"/api/v1/compliance/{assignment_id}/exceptions", {"reason": "cross-tenant"}),
        ])

    for method, path, payload in privileged_checks:
        response = client.request(method, path, json=payload)
        assert response.status_code in {403, 404}, f"{method} {path}: {response.status_code} {response.text}"

def test_phase1_user_and_session_lifecycle_security_evidence(client: TestClient) -> None:
    login(client, ADMIN)
    admin_profile = client.get("/api/v1/auth/me").json()
    learner_profile = client.get("/api/v1/people").json()
    learner_id = next(item["id"] for item in learner_profile if item["email"] == LEARNER["email"])
    roles = client.get("/api/v1/organization/roles").json()
    manager_role = next(item for item in roles if item["name"] == "Manager")
    learner_role = next(item for item in roles if item["name"] == "Learner")

    updated = client.patch(
        f"/api/v1/admin/users/{learner_id}",
        json={"job_title": "Lifecycle Test Learner"},
    )
    assert updated.status_code == 200
    restored = client.patch(
        f"/api/v1/admin/users/{learner_id}",
        json={"job_title": "Learner"},
    )
    assert restored.status_code == 200

    self_deactivate = client.patch(
        f"/api/v1/admin/users/{admin_profile['id']}",
        json={"is_active": False},
    )
    assert self_deactivate.status_code == 422

    assigned = client.post(
        f"/api/v1/organization/users/{learner_id}/roles/{manager_role['id']}",
    )
    assert assigned.status_code in {201, 200}

    removed = client.delete(
        f"/api/v1/organization/users/{learner_id}/roles/{manager_role['id']}",
    )
    assert removed.status_code == 200

    learner_role_check = client.post(
        f"/api/v1/organization/users/{learner_id}/roles/{learner_role['id']}",
    )
    assert learner_role_check.status_code in {201, 200}

    login(client, LEARNER)
    first_session = client.get("/api/v1/auth/sessions")
    assert first_session.status_code == 200
    _first_active = [item for item in first_session.json() if item["status"] == "active"]

    login(client, LEARNER)
    session_list = client.get("/api/v1/auth/sessions")
    assert session_list.status_code == 200
    current = next(item for item in session_list.json() if item["is_current"])
    non_current = next((item for item in session_list.json() if not item["is_current"] and item["status"] == "active"), None)

    if non_current:
        revoked = client.delete(f"/api/v1/auth/sessions/{non_current['id']}")
        assert revoked.status_code == 200
        assert client.delete(f"/api/v1/auth/sessions/{current['id']}").status_code == 400

    revoked_others = client.post("/api/v1/auth/sessions/revoke-others")
    assert revoked_others.status_code == 200

def test_phase1_invitation_lifecycle_is_tenant_scoped(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from", None)
    monkeypatch.setattr(settings, "dev_email_sink", True)

    login(client, ADMIN)
    roles = client.get("/api/v1/organization/roles").json()
    learner_role = next(item for item in roles if item["name"] == "Learner")
    invite = client.post(
        "/api/v1/admin/invitations",
        json={
            "email": "phase1-invited@example.com",
            "role_id": learner_role["id"],
            "expiry_days": 7,
        },
    )
    assert invite.status_code == 201
    assert invite.json()["status"] == "sent"

    login(client, LEARNER)
    forbidden = client.post(
        "/api/v1/admin/invitations",
        json={
            "email": "phase1-learner-forbidden@example.com",
            "role_id": learner_role["id"],
            "expiry_days": 7,
        },
    )
    assert forbidden.status_code == 403
def test_phase2_course_governance_and_access_controls(client: TestClient) -> None:
    from uuid import uuid4

    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    admin_id = next(item["id"] for item in people if item["email"] == ADMIN["email"])
    learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])

    category_name = f"Phase 2 Governance {uuid4().hex[:8]}"
    category = client.post(
        "/api/v1/courses/categories",
        json={"name": category_name, "description": "Phase 2 governance validation"},
    )
    assert category.status_code == 201
    category_id = category.json()["id"]

    prerequisite = client.post(
        "/api/v1/courses",
        json={
            "title": "Phase 2 Prerequisite Course",
            "slug": f"phase-2-prereq-{uuid4().hex[:8]}",
            "description": "Prerequisite for governance validation.",
            "estimated_minutes": 30,
            "category_id": category_id,
            "owner_id": admin_id,
            "tags": ["Compliance", " compliance ", ""],
        },
    )
    assert prerequisite.status_code == 201, prerequisite.text
    prerequisite_id = prerequisite.json()["id"]
    assert prerequisite.json()["owner_id"] == admin_id
    assert prerequisite.json()["tags"] == ["Compliance"]

    module = client.post(
        f"/api/v1/courses/{prerequisite_id}/modules",
        json={"title": "Foundations", "position": 1},
    )
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{prerequisite_id}/modules/{module.json()['id']}/lessons",
        json={"title": "Complete this lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Phase 2"}},
    )
    assert lesson.status_code == 200
    published = client.post(f"/api/v1/courses/{prerequisite_id}/publish")
    assert published.status_code == 200

    private_course = client.post(
        "/api/v1/courses",
        json={
            "title": "Phase 2 Private Course",
            "slug": f"phase-2-private-{uuid4().hex[:8]}",
            "visibility": "private",
            "owner_id": admin_id,
            "category_id": category_id,
        },
    )
    assert private_course.status_code == 201
    private_id = private_course.json()["id"]
    private_module = client.post(
        f"/api/v1/courses/{private_id}/modules",
        json={"title": "Private module", "position": 1},
    )
    assert private_module.status_code == 200
    private_lesson = client.post(
        f"/api/v1/courses/{private_id}/modules/{private_module.json()['id']}/lessons",
        json={"title": "Private lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Private"}},
    )
    assert private_lesson.status_code == 200
    assert client.post(f"/api/v1/courses/{private_id}/publish").status_code == 200
    dependent = client.post(
        "/api/v1/courses",
        json={
            "title": "Phase 2 Dependent Course",
            "slug": f"phase-2-dependent-{uuid4().hex[:8]}",
            "visibility": "tenant",
            "owner_id": admin_id,
            "category_id": category_id,
            "prerequisites": [prerequisite_id],
        },
    )
    assert dependent.status_code == 201, dependent.text
    dependent_id = dependent.json()["id"]

    dependent_module = client.post(
        f"/api/v1/courses/{dependent_id}/modules",
        json={"title": "Dependent module", "position": 1},
    )
    assert dependent_module.status_code == 200
    assert client.post(
        f"/api/v1/courses/{dependent_id}/modules/{dependent_module.json()['id']}/lessons",
        json={"title": "Dependent lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Dependent"}},
    ).status_code == 200
    assert client.post(f"/api/v1/courses/{dependent_id}/publish").status_code == 200

    manage_courses = client.get("/api/v1/courses?manage=true")
    assert manage_courses.status_code == 200
    assert any(item["id"] == private_id and item["visibility"] == "private" for item in manage_courses.json())

    login(client, LEARNER)
    learner_catalog = client.get("/api/v1/courses")
    assert learner_catalog.status_code == 200
    assert private_id not in {item["id"] for item in learner_catalog.json()}

    private_detail = client.get(f"/api/v1/courses/{private_id}")
    assert private_detail.status_code == 404
    private_enroll = client.post(f"/api/v1/courses/{private_id}/enroll")
    assert private_enroll.status_code == 404

    blocked = client.post(f"/api/v1/courses/{dependent_id}/enroll")
    assert blocked.status_code == 422

    prerequisite_enrollment = client.post(f"/api/v1/courses/{prerequisite_id}/enroll")
    assert prerequisite_enrollment.status_code == 200
    prerequisite_detail = client.get(f"/api/v1/courses/{prerequisite_id}")
    assert prerequisite_detail.status_code == 200
    prerequisite_lesson_id = prerequisite_detail.json()["modules"][0]["lessons"][0]["id"]
    completed = client.post(
        f"/api/v1/courses/my/enrollments/{prerequisite_enrollment.json()['id']}/lessons/{prerequisite_lesson_id}/complete"
    )
    assert completed.status_code == 200
    allowed = client.post(f"/api/v1/courses/{dependent_id}/enroll")
    assert allowed.status_code == 200

    login(client, ADMIN)
    assigned = client.post(
        f"/api/v1/courses/{private_id}/enrollments/bulk",
        json={"user_ids": [learner_id]},
    )
    assert assigned.status_code == 200
    login(client, LEARNER)
    enrolled_private_detail = client.get(f"/api/v1/courses/{private_id}")
    assert enrolled_private_detail.status_code == 200

    login(client, ADMIN)
    update = client.patch(
        f"/api/v1/courses/{dependent_id}",
        json={"tags": ["Leadership", " leadership ", "L&D"]},
    )
    assert update.status_code == 200
    assert update.json()["tags"] == ["Leadership", "L&D"]

    isolation_login = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": LEARNER["password"]},
    )
    assert isolation_login.status_code == 200
    category_list = client.get("/api/v1/courses/categories")
    assert category_list.status_code == 200
    assert category_name not in {item["name"] for item in category_list.json()}


def test_phase2_due_date_reminders_are_idempotent_and_tenant_scoped(client: TestClient) -> None:
    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
    token = uuid4().hex[:8]
    slug = f"phase-2-reminders-{token}"
    course_title = f"Phase 2 Reminder Course {token}"
    course = client.post("/api/v1/courses", json={"title": course_title, "slug": slug})
    assert course.status_code == 201
    course_id = course.json()["id"]
    module = client.post(f"/api/v1/courses/{course_id}/modules", json={"title": "Reminder module", "position": 1})
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
        json={"title": "Reminder lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Due date"}},
    )
    assert lesson.status_code == 200
    assert client.post(f"/api/v1/courses/{course_id}/publish").status_code == 200
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    assigned = client.post(
        f"/api/v1/courses/{course_id}/enrollments/bulk",
        json={"user_ids": [learner_id], "due_at": due_at},
    )
    assert assigned.status_code == 200
    first_run = client.post("/api/v1/admin/learning/reminders/run")
    assert first_run.status_code == 200
    assert first_run.json()["created"] >= 1
    second_run = client.post("/api/v1/admin/learning/reminders/run")
    assert second_run.status_code == 200
    assert second_run.json()["created"] == 0

    login(client, LEARNER)
    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    reminders = [
        item for item in notifications.json()
        if item["type"] == "learning.due_reminder" and course.json()["title"] in item["body"]
    ]
    assert len(reminders) == 1

    isolated = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "isolation-corporation",
            "email": "isolated@other.corp",
            "password": LEARNER["password"],
        },
    )
    assert isolated.status_code == 200
    assert client.post("/api/v1/admin/learning/reminders/run").status_code == 403


def test_phase2_category_lifecycle_is_tenant_scoped_and_soft_delete(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    created = client.post(
        "/api/v1/courses/categories",
        json={"name": f"  Phase 2 Category {token}  ", "description": "Lifecycle"},
    )
    assert created.status_code == 201, created.text
    category = created.json()
    assert category["name"] == f"Phase 2 Category {token}"
    category_id = category["id"]

    duplicate = client.post(
        "/api/v1/courses/categories",
        json={"name": f"phase 2 category {token}"},
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/courses/categories/{category_id}",
        json={"name": f"Phase 2 Category Renamed {token}", "description": "Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"].endswith(token)

    deactivated = client.patch(f"/api/v1/courses/categories/{category_id}", json={"active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False

    login(client, LEARNER)
    visible = {item["id"] for item in client.get("/api/v1/courses/categories").json()}
    assert category_id not in visible

    restored = client.patch(f"/api/v1/courses/categories/{category_id}", json={"active": True})
    assert restored.status_code == 403


def test_phase2_learner_journey_enrollment_progress_completion(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 2 Learner Journey {token}", "slug": f"phase-2-journey-{token}"},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]
    module = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "Journey module", "position": 1},
    )
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
        json={
            "title": "Journey lesson",
            "position": 1,
            "content_type": "rich_text",
            "content": {"body": "Complete the learner journey."},
        },
    )
    assert lesson.status_code == 200
    lesson_id = lesson.json()["id"]
    assert client.post(f"/api/v1/courses/{course_id}/publish").status_code == 200

    login(client, LEARNER)
    enrollment = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert enrollment.status_code == 200
    enrollment_id = enrollment.json()["id"]
    before = client.get(f"/api/v1/courses/{course_id}")
    assert before.status_code == 200
    assert before.json()["progress_percent"] == 0
    assert before.json()["enrollment"]["status"] in {"enrolled", "in_progress"}

    completed = client.post(
        f"/api/v1/courses/my/enrollments/{enrollment_id}/lessons/{lesson_id}/complete"
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] is not None

    after = client.get(f"/api/v1/courses/{course_id}")
    assert after.status_code == 200
    payload = after.json()
    assert payload["progress_percent"] == 100
    assert lesson_id in payload["completed_lesson_ids"]
    assert payload["enrollment"]["status"] == "completed"
    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    assert any(
        item["type"] == "learning.course_completed" and course.json()["title"] in item["body"]
        for item in notifications.json()
    )


def test_phase2_content_version_history_and_restore(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 2 Versioned Course {token}", "slug": f"phase-2-versioned-{token}"},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]
    module = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "Versioned module", "position": 1},
    )
    assert module.status_code == 200
    module_id = module.json()["id"]
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module_id}/lessons",
        json={
            "title": "Original lesson",
            "position": 1,
            "content_type": "rich_text",
            "content": {"body": "Version one"},
            "change_note": "Initial evidence version",
        },
    )
    assert lesson.status_code == 200
    lesson_id = lesson.json()["id"]
    updated = client.patch(
        f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}",
        json={
            "title": "Updated lesson",
            "content": {"body": "Version two"},
            "change_note": "Second evidence version",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated lesson"

    versions = client.get(
        f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/versions"
    )
    assert versions.status_code == 200
    assert [item["version_number"] for item in versions.json()[:2]] == [2, 1]
    assert versions.json()[0]["content"]["body"] == "Version two"
    assert versions.json()[1]["content"]["body"] == "Version one"

    restored = client.post(
        f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/versions/1/restore"
    )
    assert restored.status_code == 200
    assert restored.json()["title"] == "Original lesson"
    assert restored.json()["content"]["body"] == "Version one"

    final_versions = client.get(
        f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/versions"
    )
    assert final_versions.status_code == 200
    assert final_versions.json()[0]["version_number"] == 3
    assert final_versions.json()[0]["change_note"] == "Restored from version 1"


def test_phase2_approval_and_audience_enrollment(client: TestClient) -> None:
    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
    unit = client.post(
        "/api/v1/admin/org-units",
        json={"name": f"Phase 2 Audience {uuid4().hex[:8]}", "unit_type": "department"},
    )
    assert unit.status_code == 201
    unit_id = unit.json()["id"]
    course = client.post(
        "/api/v1/courses",
        json={
            "title": "Phase 2 Approval Course",
            "slug": f"phase-2-approval-{uuid4().hex[:8]}",
            "enrollment_policy": "approval",
            "audience_org_units": [unit_id],
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]
    module = client.post(f"/api/v1/courses/{course_id}/modules", json={"title": "Approval module", "position": 1})
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
        json={"title": "Approval lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Approval"}},
    )
    assert lesson.status_code == 200
    assert client.post(f"/api/v1/courses/{course_id}/publish").status_code == 200
    login(client, LEARNER)
    preview = client.get(f"/api/v1/courses/{course_id}")
    assert preview.status_code == 200
    assert preview.json()["modules"][0]["lessons"][0]["content"] == {}
    outside = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert outside.status_code == 403
    login(client, ADMIN)
    assigned = client.patch(f"/api/v1/admin/users/{learner_id}", json={"org_unit_id": unit_id})
    assert assigned.status_code == 200
    login(client, LEARNER)
    requested = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert requested.status_code == 200
    assert requested.json()["status"] == "pending_approval"
    assert client.get(f"/api/v1/courses/{course_id}").json()["modules"][0]["lessons"][0]["content"] == {}
    enrollment_id = requested.json()["id"]
    login(client, ADMIN)
    queue = client.get(f"/api/v1/courses/{course_id}/enrollments/queue")
    assert queue.status_code == 200
    assert any(item["id"] == enrollment_id for item in queue.json())
    approved = client.post(f"/api/v1/courses/{course_id}/enrollments/{enrollment_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "enrolled"
    login(client, LEARNER)
    detail = client.get(f"/api/v1/courses/{course_id}")
    assert detail.status_code == 200
    lesson_id = detail.json()["modules"][0]["lessons"][0]["id"]
    assert detail.json()["modules"][0]["lessons"][0]["content"]["body"] == "Approval"
    completed = client.post(
        f"/api/v1/courses/my/enrollments/{enrollment_id}/lessons/{lesson_id}/complete"
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    login(client, ADMIN)
    restored = client.patch(f"/api/v1/admin/users/{learner_id}", json={"org_unit_id": None})
    assert restored.status_code == 200


def test_phase2_capacity_waitlist_promotes_on_completion(client: TestClient) -> None:
    login(client, ADMIN)
    course = client.post(
        "/api/v1/courses",
        json={
            "title": "Phase 2 Capacity Course",
            "slug": f"phase-2-capacity-{uuid4().hex[:8]}",
            "enrollment_policy": "open",
            "capacity": 1,
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]
    module = client.post(f"/api/v1/courses/{course_id}/modules", json={"title": "Capacity module", "position": 1})
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
        json={"title": "Capacity lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Capacity"}},
    )
    assert lesson.status_code == 200
    assert client.post(f"/api/v1/courses/{course_id}/publish").status_code == 200

    login(client, MANAGER)
    first = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert first.status_code == 200
    assert first.json()["status"] == "enrolled"
    first_enrollment_id = first.json()["id"]

    login(client, LEARNER)
    second = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert second.status_code == 200
    assert second.json()["status"] == "waitlisted"
    second_enrollment_id = second.json()["id"]

    blocked = client.post(
        f"/api/v1/courses/my/enrollments/{second_enrollment_id}/lessons/{lesson.json()['id']}/complete"
    )
    assert blocked.status_code == 409

    login(client, MANAGER)
    finished = client.post(
        f"/api/v1/courses/my/enrollments/{first_enrollment_id}/lessons/{lesson.json()['id']}/complete"
    )
    assert finished.status_code == 200
    assert finished.json()["status"] == "completed"

    login(client, LEARNER)
    enrollments = client.get("/api/v1/courses/my/enrollments")
    assert enrollments.status_code == 200
    promoted = next(item for item in enrollments.json() if item["id"] == second_enrollment_id)
    assert promoted["status"] == "enrolled"

def test_phase3_assessment_analytics_and_question_management(client: TestClient) -> None:
    login(client, ADMIN)
    assessment = next(item for item in client.get('/api/v1/assessments').json() if item['title'] == 'Ethics Knowledge Check')
    original = client.get(f"/api/v1/assessments/{assessment['id']}")
    assert original.status_code == 200
    original_question = original.json()['questions'][0]
    assert client.patch(f"/api/v1/assessments/questions/{original_question['id']}", json={'points': 2}).status_code == 409
    copied = client.post(f"/api/v1/assessments/{assessment['id']}/clone")
    assert copied.status_code == 201
    assessment = copied.json()
    detail = client.get(f"/api/v1/assessments/{assessment['id']}")
    assert detail.status_code == 200
    question = detail.json()['questions'][0]
    updated = client.patch(
        f"/api/v1/assessments/questions/{question['id']}",
        json={'prompt': question['prompt'], 'points': question['points'] + 1},
    )
    assert updated.status_code == 200
    analytics = client.get(f"/api/v1/assessments/{assessment['id']}/analytics")
    assert analytics.status_code == 200
    body = analytics.json()
    assert body['attempts'] >= 0
    assert 0 <= body['pass_rate'] <= 100
    assert body['average_score'] >= 0
    reordered = client.post(
        f"/api/v1/assessments/{assessment['id']}/questions/reorder",
        json={'question_ids': [q['id'] for q in reversed(detail.json()['questions'])]},
    )
    assert reordered.status_code == 200
    question_analytics = client.get(f"/api/v1/assessments/{assessment['id']}/question-analytics")
    assert question_analytics.status_code == 200
    assert len(question_analytics.json()['questions']) == len(detail.json()['questions'])
    assert all('correct_rate' in item for item in question_analytics.json()['questions'])
    created = client.post(
        f"/api/v1/assessments/{assessment['id']}/questions",
        json={'question_type':'single_choice','prompt':'Temporary Phase 3 question','options':['A','B'],'answer_key':{'correct':'A'},'points':1,'position':99},
    )
    assert created.status_code == 201
    deleted = client.delete(f"/api/v1/assessments/questions/{created.json()['id']}")
    assert deleted.status_code == 204


def test_phase3_security_permission_and_tenant_boundaries(client: TestClient) -> None:
    login(client, LEARNER)
    assessment = client.get("/api/v1/assessments").json()[0]
    checks = [
        client.get(f"/api/v1/assessments/{assessment['id']}/analytics"),
        client.get(f"/api/v1/assessments/{assessment['id']}/question-analytics"),
        client.post(f"/api/v1/assessments/{assessment['id']}/questions/reorder", json={"question_ids": []}),
        client.get("/api/v1/certificates/admin"),
        client.get("/api/v1/certificates/templates/default"),
        client.patch("/api/v1/certificates/templates/default", json={"title": "No"}),
    ]
    assert all(response.status_code == 403 for response in checks)

    login(client, ADMIN)
    detail = client.get(f"/api/v1/assessments/{assessment['id']}").json()
    question_ids = [item["id"] for item in detail["questions"]]
    isolated = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": LEARNER["password"]},
    )
    assert isolated.status_code == 200
    assert client.get(f"/api/v1/assessments/{assessment['id']}/analytics").status_code in {403, 404}
    assert client.get(f"/api/v1/assessments/{assessment['id']}/question-analytics").status_code in {403, 404}
    assert client.post(f"/api/v1/assessments/{assessment['id']}/questions/reorder", json={"question_ids": question_ids}).status_code in {403, 404}
    assert client.get("/api/v1/certificates/admin").status_code == 403
    assert client.get("/api/v1/certificates/templates/default").status_code == 403


def test_phase3_attempt_detail_security(client: TestClient) -> None:
    login(client, ADMIN)
    assessment = client.get("/api/v1/assessments").json()[0]
    attempts = client.get(f"/api/v1/assessments/{assessment['id']}/attempts").json()
    if not attempts:
        pytest.skip("No seeded assessment attempt available")
    attempt_id = attempts[0]["id"]
    login(client, LEARNER)
    assert client.get(f"/api/v1/assessments/attempts/{attempt_id}/detail").status_code == 403
    isolated = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": LEARNER["password"]},
    )
    assert isolated.status_code == 200
    assert client.get(f"/api/v1/assessments/attempts/{attempt_id}/detail").status_code in {403, 404}


def test_phase3_certificate_admin_lifecycle(client: TestClient) -> None:
    login(client, ADMIN)
    certificates = client.get('/api/v1/certificates/admin')
    assert certificates.status_code == 200
    if not certificates.json():
        pytest.skip('No certificate available in seeded database')
    certificate = certificates.json()[0]
    expiry = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    renewed = client.patch(
        f"/api/v1/certificates/{certificate['id']}/lifecycle",
        json={'action': 'renew', 'expires_at': expiry, 'reason': 'Phase 3 lifecycle regression verification.'},
    )
    assert renewed.status_code == 200
    assert renewed.json()['expires_at'] is not None


def test_phase3_attempt_detail_does_not_disclose_answer_keys(client: TestClient) -> None:
    login(client, ADMIN)
    assessment = client.get("/api/v1/assessments").json()[0]
    attempts = client.get(f"/api/v1/assessments/{assessment['id']}/attempts").json()
    if not attempts:
        pytest.skip("No seeded assessment attempt available")
    detail = client.get(f"/api/v1/assessments/attempts/{attempts[0]['id']}/detail")
    assert detail.status_code == 200
    assert detail.json()["questions"]
    assert all("answer_key" not in item for item in detail.json()["questions"])


def test_phase3_certificate_template_validation_and_tenant_persistence(client: TestClient) -> None:
    login(client, ADMIN)
    original = client.get("/api/v1/certificates/templates/default")
    assert original.status_code == 200
    original_body = original.json()
    invalid = client.patch(
        "/api/v1/certificates/templates/default",
        json={**original_body, "logo_url": "javascript:alert(1)"},
    )
    assert invalid.status_code == 422
    updated = client.patch(
        "/api/v1/certificates/templates/default",
        json={**original_body, "issuer_name": "CorpLMS Evidence Test", "logo_url": "https://example.com/logo.png"},
    )
    assert updated.status_code == 200
    refreshed = client.get("/api/v1/certificates/templates/default")
    assert refreshed.status_code == 200
    assert refreshed.json()["issuer_name"] == "CorpLMS Evidence Test"
    assert refreshed.json()["logo_url"] == "https://example.com/logo.png"
    restored = client.patch("/api/v1/certificates/templates/default", json=original_body)
    assert restored.status_code == 200


def test_phase3_certificate_renewal_server_default_and_reason_validation(client: TestClient) -> None:
    login(client, ADMIN)
    certificates = client.get("/api/v1/certificates/admin")
    assert certificates.status_code == 200
    if not certificates.json():
        pytest.skip("No certificate available in seeded database")
    certificate_id = certificates.json()[0]["id"]
    invalid = client.patch(
        f"/api/v1/certificates/{certificate_id}/lifecycle",
        json={"action": "renew", "reason": "x"},
    )
    assert invalid.status_code == 422
    renewed = client.patch(
        f"/api/v1/certificates/{certificate_id}/lifecycle",
        json={"action": "renew", "reason": "Default renewal evidence test."},
    )
    assert renewed.status_code == 200
    assert renewed.json()["expires_at"] is not None



def test_phase4_course_equivalency_crud_and_governance(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    first = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 4 Equivalency A {token}", "slug": f"phase4-equiv-a-{token}"},
    )
    second = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 4 Equivalency B {token}", "slug": f"phase4-equiv-b-{token}"},
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    first_id, second_id = first.json()["id"], second.json()["id"]

    created = client.post(
        "/api/v1/courses/equivalencies",
        json={
            "course_id": first_id,
            "equivalent_course_id": second_id,
            "equivalency_type": "partial",
            "notes": "Phase 4 governance test relationship.",
        },
    )
    assert created.status_code == 201, created.text
    relationship_id = created.json()["id"]
    assert created.json()["equivalency_type"] == "partial"

    listed = client.get("/api/v1/courses/equivalencies")
    assert listed.status_code == 200
    assert any(item["id"] == relationship_id for item in listed.json())

    updated = client.patch(
        f"/api/v1/courses/equivalencies/{relationship_id}",
        json={"equivalency_type": "credit_transfer", "active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["equivalency_type"] == "credit_transfer"
    assert updated.json()["active"] is False
    assert all(item["id"] != relationship_id for item in client.get("/api/v1/courses/equivalencies?active_only=true").json())

    deleted = client.delete(f"/api/v1/courses/equivalencies/{relationship_id}")
    assert deleted.status_code == 204
    remaining = client.get("/api/v1/courses/equivalencies").json()
    assert all(item["id"] != relationship_id for item in remaining)


def test_phase4_course_equivalency_rejects_self_and_duplicate_reverse_links(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    first = client.post("/api/v1/courses", json={"title": f"Phase 4 Duplicate A {token}", "slug": f"phase4-dup-a-{token}"})
    second = client.post("/api/v1/courses", json={"title": f"Phase 4 Duplicate B {token}", "slug": f"phase4-dup-b-{token}"})
    assert first.status_code == 201 and second.status_code == 201
    first_id, second_id = first.json()["id"], second.json()["id"]

    self_link = client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": first_id, "equivalent_course_id": first_id},
    )
    assert self_link.status_code == 422

    created = client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": first_id, "equivalent_course_id": second_id},
    )
    assert created.status_code == 201

    duplicate = client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": first_id, "equivalent_course_id": second_id},
    )
    assert duplicate.status_code == 409

    reverse = client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": second_id, "equivalent_course_id": first_id},
    )
    assert reverse.status_code == 409


def test_phase4_course_equivalency_permission_and_tenant_isolation(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    first = client.post("/api/v1/courses", json={"title": f"Phase 4 Boundary A {token}", "slug": f"phase4-boundary-a-{token}"})
    second = client.post("/api/v1/courses", json={"title": f"Phase 4 Boundary B {token}", "slug": f"phase4-boundary-b-{token}"})
    assert first.status_code == 201 and second.status_code == 201
    first_id, second_id = first.json()["id"], second.json()["id"]
    created = client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": first_id, "equivalent_course_id": second_id, "notes": "Tenant boundary test"},
    )
    assert created.status_code == 201
    relationship_id = created.json()["id"]

    login(client, LEARNER)
    assert client.get("/api/v1/courses/equivalencies").status_code == 403
    assert client.post(
        "/api/v1/courses/equivalencies",
        json={"course_id": first_id, "equivalent_course_id": second_id},
    ).status_code == 403

    isolated = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": LEARNER["password"]},
    )
    assert isolated.status_code == 200
    assert client.get("/api/v1/courses/equivalencies").status_code == 403
    assert client.get(f"/api/v1/courses/equivalencies/{relationship_id}").status_code == 405
    assert client.patch(f"/api/v1/courses/equivalencies/{relationship_id}", json={"active": False}).status_code == 403
    assert client.delete(f"/api/v1/courses/equivalencies/{relationship_id}").status_code == 403



def test_phase4_manager_can_assign_direct_report_and_cannot_cross_scope(client: TestClient) -> None:
    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    manager_id = next(item["id"] for item in people if item["email"] == MANAGER["email"])
    learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 4 Manager Assignment {uuid4().hex[:8]}", "slug": f"phase4-manager-{uuid4().hex[:8]}"},
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]
    module = client.post(f"/api/v1/courses/{course_id}/modules", json={"title": "Manager module", "position": 1})
    assert module.status_code == 200
    lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
        json={"title": "Manager lesson", "position": 1, "content_type": "rich_text", "content": {"body": "Manager assignment"}},
    )
    assert lesson.status_code == 200
    assert client.post(f"/api/v1/courses/{course_id}/publish").status_code == 200

    assigned = client.patch(f"/api/v1/admin/users/{learner_id}", json={"manager_id": manager_id})
    assert assigned.status_code == 200, assigned.text

    login(client, MANAGER)
    team = client.get("/api/v1/people/team")
    assert team.status_code == 200
    assert any(item["id"] == learner_id for item in team.json())

    enrollment = client.post(
        f"/api/v1/courses/{course_id}/manager-assignment",
        json={"user_id": learner_id, "due_at": "2030-06-01T00:00:00Z"},
    )
    assert enrollment.status_code == 200, enrollment.text
    assert enrollment.json()["status"] == "enrolled"

    out_of_scope = client.post(
        f"/api/v1/courses/{course_id}/manager-assignment",
        json={"user_id": manager_id},
    )
    assert out_of_scope.status_code == 403

    login(client, ADMIN)
    restored = client.patch(f"/api/v1/admin/users/{learner_id}", json={"manager_id": None})
    assert restored.status_code == 200


def test_phase4_facilitator_session_analytics_is_scoped_and_accurate(client: TestClient) -> None:
    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    admin_id = next(item["id"] for item in people if item["email"] == ADMIN["email"])
    learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 4 Facilitator {uuid4().hex[:8]}", "slug": f"phase4-facilitator-{uuid4().hex[:8]}"},
    )
    assert course.status_code == 201
    session = client.post(
        "/api/v1/sessions",
        json={
            "course_id": course.json()["id"],
            "instructor_id": admin_id,
            "title": "Facilitator analytics session",
            "starts_at": "2030-07-01T10:00:00Z",
            "ends_at": "2030-07-01T11:00:00Z",
        },
    )
    assert session.status_code == 201
    session_id = session.json()["id"]
    marked = client.post(
        f"/api/v1/sessions/{session_id}/attendance",
        json={"user_id": learner_id, "status": "present"},
    )
    assert marked.status_code == 201
    analytics = client.get(f"/api/v1/sessions/{session_id}/analytics")
    assert analytics.status_code == 200, analytics.text
    data = analytics.json()
    assert data["attendance"]["total_marked"] == 1
    assert data["attendance"]["present"] == 1
    assert data["attendance"]["attendance_rate"] == 100.0
    assert data["roster"][0]["user_id"] == learner_id

    login(client, LEARNER)
    forbidden = client.get(f"/api/v1/sessions/{session_id}/analytics")
    assert forbidden.status_code == 403

    login(client, ADMIN)
    missing = client.get(f"/api/v1/sessions/{uuid4()}/analytics")
    assert missing.status_code == 404


def test_phase5_manager_development_workflow_authorization(client: TestClient) -> None:
    login(client, ADMIN)
    people = client.get("/api/v1/people").json()
    learner = next(item for item in people if item["email"] == LEARNER["email"])
    manager = next(item for item in people if item["email"] == MANAGER["email"])
    assigned = client.patch(
        f"/api/v1/admin/users/{learner['id']}",
        json={"manager_id": manager["id"]},
    )
    assert assigned.status_code == 200

    login(client, LEARNER)
    learner_plan = client.post(
        "/api/v1/development/my",
        json={"title": "Phase 5 manager workflow proof", "goals": [{"title": "Milestone delivery"}]},
    )
    assert learner_plan.status_code == 201
    learner_plan_id = learner_plan.json()["id"]

    progress = client.get(f"/api/v1/development/{learner_plan_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["plan"]["id"] == learner_plan_id

    login(client, MANAGER)
    manager_progress = client.get(f"/api/v1/development/{learner_plan_id}/progress")
    assert manager_progress.status_code == 200
    assert manager_progress.json()["plan"]["id"] == learner_plan_id
    created = client.post(
        f"/api/v1/development/{learner_plan_id}/milestones",
        json={"title": "Complete manager review", "description": "Review progress."},
    )
    assert created.status_code == 201
    milestone_id = created.json()["id"]

    completed = client.patch(
        f"/api/v1/development/{learner_plan_id}/milestones/{milestone_id}",
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    feedback = client.post(
        f"/api/v1/development/{learner_plan_id}/feedback",
        json={"rating": 5, "feedback": "Strong progress and ownership.", "next_steps": "Continue delivery."},
    )
    assert feedback.status_code == 201

    invalid = client.post(
        f"/api/v1/development/{learner_plan_id}/feedback",
        json={"rating": 6, "feedback": "Invalid rating."},
    )
    assert invalid.status_code == 422

    login(client, ADMIN)
    unrelated = client.post(
        "/api/v1/development/my",
        json={"title": "Admin private plan", "goals": []},
    )
    assert unrelated.status_code == 201
    unrelated_id = unrelated.json()["id"]

    login(client, MANAGER)
    assert client.get(f"/api/v1/development/{unrelated_id}/progress").status_code == 403
    forbidden = client.post(
        f"/api/v1/development/{unrelated_id}/milestones",
        json={"title": "Should be forbidden"},
    )
    assert forbidden.status_code == 403

    login(client, LEARNER)
    assert client.get(f"/api/v1/development/{unrelated_id}/progress").status_code == 404



def test_phase6_reporting_analytics_endpoints_are_tenant_scoped(client: TestClient) -> None:
    login(client, ADMIN)

    trends = client.get("/api/v1/reports/learning-trends?days=14")
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["days"] == 14
    assert len(payload["points"]) == 14
    assert {"date", "enrollments", "completions"} <= set(payload["points"][0])

    performance = client.get("/api/v1/reports/course-performance")
    assert performance.status_code == 200
    assert isinstance(performance.json()["courses"], list)

    risk = client.get("/api/v1/reports/compliance-risk")
    assert risk.status_code == 200
    assert set(risk.json()) == {"total", "open", "overdue", "risk_band"}
    assert risk.json()["risk_band"] in {"low", "medium", "high"}


def test_phase6_reporting_endpoints_require_reports_permission(client: TestClient) -> None:
    login(client, LEARNER)
    for path in (
        "/api/v1/reports/learning-trends",
        "/api/v1/reports/course-performance",
        "/api/v1/reports/compliance-risk",
    ):
        assert client.get(path).status_code == 403


def test_phase6_saved_report_and_schedule_governance(client: TestClient) -> None:
    login(client, ADMIN)
    created = client.post(
        "/api/v1/reports/saved",
        json={"name": "Phase 6 Test Report", "report_type": "course-performance", "definition": {"limit": 25}, "visibility": "private"},
    )
    assert created.status_code == 200
    report_id = created.json()["id"]
    duplicate = client.post(
        "/api/v1/reports/saved",
        json={"name": "Phase 6 Test Report", "report_type": "course-performance"},
    )
    assert duplicate.status_code == 409
    scheduled = client.post(
        f"/api/v1/reports/saved/{report_id}/schedule",
        json={"frequency": "weekly", "next_run_at": "2099-01-01T09:00:00Z", "recipients": ["admin@example.com"]},
    )
    assert scheduled.status_code == 200
    listed = client.get("/api/v1/reports/schedules")
    assert listed.status_code == 200
    assert any(item["saved_report_id"] == report_id for item in listed.json())
    runs = client.get(f"/api/v1/reports/schedules/{scheduled.json()['id']}/runs")
    assert runs.status_code == 200
    assert runs.json() == []
    deleted = client.delete(f"/api/v1/reports/saved/{report_id}")
    assert deleted.status_code == 200

def test_assessment_timed_attempt_resume_and_revision_lock(client: TestClient) -> None:
    login(client, ADMIN)
    created = client.post("/api/v1/assessments", json={"title": "Timed revision proof", "time_limit_minutes": 30, "max_attempts": 1})
    assert created.status_code == 201
    assessment_id = created.json()["id"]
    question = client.post(f"/api/v1/assessments/{assessment_id}/questions", json={
        "question_type": "single_choice", "prompt": "Choose the approved answer",
        "options": ["Yes", "No"], "answer_key": {"correct": "Yes"}, "points": 1, "position": 1,
    })
    assert question.status_code == 201
    login(client, LEARNER)
    assert client.get(f"/api/v1/assessments/{assessment_id}/editor").status_code == 403
    started = client.post(f"/api/v1/assessments/{assessment_id}/start")
    assert started.status_code == 201
    attempt_id = started.json()["attempt_id"]
    assert client.post(f"/api/v1/assessments/{assessment_id}/start").json()["attempt_id"] == attempt_id
    assert client.post(f"/api/v1/assessments/{assessment_id}/submit", json={"answers": {question.json()["id"]: "Yes"}}).status_code == 422
    assert client.get(f"/api/v1/assessments/{assessment_id}/my-attempts").json()[0]["id"] == attempt_id
    submitted = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={"attempt_id": attempt_id, "answers": {question.json()["id"]: "Yes"}})
    assert submitted.status_code == 200 and submitted.json()["passed"] is True
    assert client.post(f"/api/v1/assessments/{assessment_id}/start").status_code == 422
    login(client, ADMIN)
    assert client.patch(f"/api/v1/assessments/questions/{question.json()['id']}", json={"prompt": "Changed answer"}).status_code == 409
    copied = client.post(f"/api/v1/assessments/{assessment_id}/clone")
    assert copied.status_code == 201
    editor = client.get(f"/api/v1/assessments/{copied.json()['id']}/editor")
    assert editor.status_code == 200 and editor.json()["locked"] is False


def test_phase9_course_studio_structure_lifecycle(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 9 Studio {token}", "slug": f"phase-9-studio-{token}"},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]

    first = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "First module", "position": 1},
    )
    second = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "Second module", "position": 2},
    )
    assert first.status_code == 200 and second.status_code == 200
    first_id = first.json()["id"]
    second_id = second.json()["id"]

    first_lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{first_id}/lessons",
        json={"title": "First lesson", "position": 1, "content_type": "rich_text", "content": {"body": "one"}},
    )
    second_lesson = client.post(
        f"/api/v1/courses/{course_id}/modules/{first_id}/lessons",
        json={"title": "Second lesson", "position": 2, "content_type": "rich_text", "content": {"body": "two"}},
    )
    assert first_lesson.status_code == 200 and second_lesson.status_code == 200

    detail = client.get(f"/api/v1/courses/{course_id}").json()
    assert [item["position"] for item in detail["modules"]] == [1, 2]
    assert [item["position"] for item in detail["modules"][0]["lessons"]] == [1, 2]

    deleted_lesson = client.delete(
        f"/api/v1/courses/{course_id}/modules/{first_id}/lessons/{second_lesson.json()['id']}"
    )
    assert deleted_lesson.status_code == 200
    after_lesson_delete = client.get(f"/api/v1/courses/{course_id}").json()
    assert len(after_lesson_delete["modules"][0]["lessons"]) == 1
    assert after_lesson_delete["modules"][0]["lessons"][0]["position"] == 1

    deleted_module = client.delete(f"/api/v1/courses/{course_id}/modules/{first_id}")
    assert deleted_module.status_code == 200
    final_detail = client.get(f"/api/v1/courses/{course_id}").json()
    assert len(final_detail["modules"]) == 1
    assert final_detail["modules"][0]["id"] == second_id
    assert final_detail["modules"][0]["position"] == 1


def test_phase9_learning_path_reorder_preserves_prerequisites(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    courses = []
    for index in (1, 2, 3):
        course = client.post(
            "/api/v1/courses",
            json={"title": f"Phase 9 Path {index} {token}", "slug": f"phase-9-path-{index}-{token}"},
        )
        assert course.status_code == 201
        courses.append(course.json()["id"])

    path = client.post(
        "/api/v1/programs/paths",
        json={"title": f"Phase 9 Path {token}", "slug": f"phase-9-learning-path-{token}"},
    )
    assert path.status_code == 201
    path_id = path.json()["id"]

    for position, course_id in enumerate(courses, start=1):
        response = client.post(
            f"/api/v1/programs/paths/{path_id}/courses",
            json={"course_id": course_id, "position": position, "prerequisite_item_id": courses[position - 2] if position > 1 else None},
        )
        assert response.status_code == 201

    moved = client.patch(
        f"/api/v1/programs/paths/{path_id}/courses/{courses[2]}/position",
        json={"position": 2},
    )
    assert moved.status_code == 422

    safe_move = client.patch(
        f"/api/v1/programs/paths/{path_id}/courses/{courses[1]}/position",
        json={"position": 3},
    )
    assert safe_move.status_code == 422


def test_phase9_course_reorder_is_atomic_and_normalized(client: TestClient) -> None:
    login(client, ADMIN)
    token = uuid4().hex[:8]
    course = client.post(
        "/api/v1/courses",
        json={"title": f"Phase 9 Reorder {token}", "slug": f"phase-9-reorder-{token}"},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]
    modules = [
        client.post(f"/api/v1/courses/{course_id}/modules", json={"title": f"Module {index}", "position": index}).json()
        for index in (1, 2, 3)
    ]
    move = client.patch(
        f"/api/v1/courses/{course_id}/modules/{modules[2]['id']}/position",
        json={"position": 1},
    )
    assert move.status_code == 200
    detail = client.get(f"/api/v1/courses/{course_id}").json()
    assert [item["id"] for item in detail["modules"]] == [modules[2]["id"], modules[0]["id"], modules[1]["id"]]
    assert [item["position"] for item in detail["modules"]] == [1, 2, 3]
    invalid = client.patch(
        f"/api/v1/courses/{course_id}/modules/{modules[0]['id']}/position",
        json={"position": 99},
    )
    assert invalid.status_code == 422
    unchanged = client.get(f"/api/v1/courses/{course_id}").json()
    assert [item["position"] for item in unchanged["modules"]] == [1, 2, 3]




def test_webhook_list_is_bounded(client: TestClient) -> None:
    login(client, ADMIN)
    first = client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/hooks/one", "event_types": ["course.completed"]},
    )
    second = client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/hooks/two", "event_types": ["course.completed"]},
    )
    assert first.status_code == second.status_code == 201
    listed = client.get("/api/v1/webhooks", params={"limit": 1})
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1
    assert client.get("/api/v1/webhooks", params={"limit": 101}).status_code == 422


def test_live_session_and_program_catalog_reads_are_bounded(client: TestClient) -> None:
    login(client, ADMIN)
    assert client.get("/api/v1/sessions", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/programs", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/programs/cohorts", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/programs/paths/all", params={"limit": 101}).status_code == 422
