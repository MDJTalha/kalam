import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN = {"email": "admin@demo.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}
LEARNER = {"email": "learner@demo.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}
ISOLATED_LEARNER = {"email": "isolated@other.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}


def _login(client: TestClient, tenant_slug: str, credentials: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/login", json={"tenant_slug": tenant_slug, **credentials})
    assert response.status_code == 200, response.text


@pytest.fixture
def client():
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


def test_knowledge_articles_enforce_publication_permissions_and_tenant_scope(client: TestClient) -> None:
    assert client.get("/api/v1/support/knowledge").status_code == 401

    _login(client, "demo-corporation", ADMIN)
    draft = client.post(
        "/api/v1/support/admin/knowledge",
        json={
            "title": "Getting started with Kalam",
            "summary": "A short guide",
            "body": "Sign in and open your assigned learning.",
            "category": "getting-started",
            "tags": ["onboarding", "learning", "onboarding"],
        },
    )
    assert draft.status_code == 201, draft.text
    draft_id = draft.json()["id"]
    assert draft.json()["status"] == "draft"
    assert draft.json()["tags"] == ["onboarding", "learning"]

    _login(client, "demo-corporation", LEARNER)
    assert client.get("/api/v1/support/knowledge").json() == []
    assert client.get(f"/api/v1/support/knowledge/{draft_id}").status_code == 404
    assert client.post(
        "/api/v1/support/admin/knowledge",
        json={"title": "Unauthorized article", "body": "Should be denied."},
    ).status_code == 403

    _login(client, "demo-corporation", ADMIN)
    published = client.patch(
        f"/api/v1/support/admin/knowledge/{draft_id}",
        json={"status": "published"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["published_at"] is not None
    cleared_summary = client.patch(
        f"/api/v1/support/admin/knowledge/{draft_id}",
        json={"summary": None},
    )
    assert cleared_summary.status_code == 200, cleared_summary.text
    assert cleared_summary.json()["summary"] is None
    invalid_tags = client.patch(
        f"/api/v1/support/admin/knowledge/{draft_id}",
        json={"tags": None},
    )
    assert invalid_tags.status_code == 422, invalid_tags.text

    _login(client, "demo-corporation", LEARNER)
    listing = client.get("/api/v1/support/knowledge", params={"q": "getting started"})
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [draft_id]
    assert client.get(f"/api/v1/support/knowledge/{draft_id}").json()["body"] == "Sign in and open your assigned learning."

    _login(client, "demo-corporation", ADMIN)
    archived = client.patch(
        f"/api/v1/support/admin/knowledge/{draft_id}",
        json={"status": "archived"},
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "archived"
    _login(client, "demo-corporation", LEARNER)
    assert client.get("/api/v1/support/knowledge").json() == []
    assert client.get(f"/api/v1/support/knowledge/{draft_id}").status_code == 404

    _login(client, "isolation-corporation", ISOLATED_LEARNER)
    assert client.get(f"/api/v1/support/knowledge/{draft_id}").status_code == 404
