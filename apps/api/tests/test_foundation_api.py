import pytest
from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}
DEMO_COURSE_SLUG = "workplace-ethics-2026"


@pytest.fixture(scope="session")
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
