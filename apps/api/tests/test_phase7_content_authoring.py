from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}


def login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, **ADMIN},
    )
    assert response.status_code == 200, response.text


def test_phase7_structured_lesson_lifecycle_and_publish_validation() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:8]
        course = client.post(
            "/api/v1/courses",
            json={"title": "Phase 7 Content Course " + token, "slug": "phase-7-content-" + token},
        )
        assert course.status_code == 201, course.text
        course_id = course.json()["id"]

        module = client.post(
            f"/api/v1/courses/{course_id}/modules",
            json={"title": "Structured module", "position": 1},
        )
        assert module.status_code == 200, module.text
        module_id = module.json()["id"]

        blocks = {
            "version": 2,
            "blocks": [
                {"id": "b1", "type": "heading", "level": 2, "text": "Operational readiness"},
                {"id": "b2", "type": "paragraph", "text": "Build capability through evidence-led practice."},
                {"id": "b3", "type": "bullets", "text": "Know the standard\nApply the standard\nProve the standard"},
                {"id": "b4", "type": "callout", "variant": "important", "text": "Evidence must be current and attributable."},
                {"id": "b5", "type": "divider"},
                {"id": "b6", "type": "link", "text": "Capability reference", "url": "https://example.com/reference"},
            ],
        }
        lesson = client.post(
            f"/api/v1/courses/{course_id}/modules/{module_id}/lessons",
            json={
                "title": "Readiness foundations",
                "position": 1,
                "content_type": "rich_text",
                "content": blocks,
                "change_note": "Initial structured content",
            },
        )
        assert lesson.status_code == 200, lesson.text
        lesson_id = lesson.json()["id"]

        detail = client.get(f"/api/v1/courses/{course_id}")
        assert detail.status_code == 200
        stored = detail.json()["modules"][0]["lessons"][0]
        assert stored["content"]["version"] == 2
        assert len(stored["content"]["blocks"]) == 6
        assert stored["content"]["blocks"][0]["type"] == "heading"

        invalid = client.patch(
            f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}",
            json={"content_type": "rich_text", "content": {"version": 2, "blocks": []}},
        )
        assert invalid.status_code == 422

        bad_file = client.patch(
            f"/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}",
            json={
                "content_type": "rich_text",
                "content": {
                    "version": 2,
                    "blocks": [{"id": "b7", "type": "file", "file_id": str(uuid4())}],
                },
            },
        )
        assert bad_file.status_code == 422

        published = client.post(f"/api/v1/courses/{course_id}/publish")
        assert published.status_code == 200, published.text
        assert published.json()["status"] == "published"
def test_phase7_legacy_lesson_remains_publishable() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:8]
        course = client.post(
            "/api/v1/courses",
            json={"title": "Phase 7 Legacy Compatibility " + token, "slug": "phase-7-legacy-" + token},
        )
        assert course.status_code == 201, course.text
        course_id = course.json()["id"]
        module = client.post(
            f"/api/v1/courses/{course_id}/modules",
            json={"title": "Legacy module", "position": 1},
        )
        assert module.status_code == 200
        lesson = client.post(
            f"/api/v1/courses/{course_id}/modules/{module.json()['id']}/lessons",
            json={
                "title": "Legacy text lesson",
                "position": 1,
                "content_type": "rich_text",
                "content": {"body": "Existing learner content remains supported."},
            },
        )
        assert lesson.status_code == 200, lesson.text
        published = client.post(f"/api/v1/courses/{course_id}/publish")
        assert published.status_code == 200, published.text
