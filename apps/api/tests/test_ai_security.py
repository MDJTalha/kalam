from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_ai_admin_surfaces_are_denied_to_learner():
    with TestClient(app, base_url="http://localhost") as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": "demo-corporation", "email": "learner@demo.corp", "password": "DemoOnly!1234"},
        )
        assert login.status_code == 200
        assert client.get("/api/v1/ai/admin/interactions").status_code == 403
        assert client.get("/api/v1/ai/admin/telemetry").status_code == 403
        assert client.put(
            f"/api/v1/ai/admin/interactions/{uuid4()}/review",
            json={"decision": "approved"},
        ).status_code == 403
        assert client.post(
            "/api/v1/ai/content-assist",
            json={
                "instruction": "Rewrite this draft.",
                "draft_text": "This is a sufficiently long draft for authorization validation.",
                "mode": "rewrite",
            },
        ).status_code == 403


def test_ai_status_does_not_cross_tenant_boundaries():
    with TestClient(app, base_url="http://localhost") as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": "DemoOnly!1234"},
        )
        assert login.status_code == 200
        status = client.get("/api/v1/ai/status")
        assert status.status_code == 200
        payload = status.json()
        assert payload["configured"] is False
        assert payload["fallback_provider_count"] == 0
        assert client.get("/api/v1/ai/admin/providers").status_code == 403


def test_admin_auth_profile_exposes_ai_manage_permission():
    with TestClient(app, base_url="http://localhost") as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"},
        )
        assert login.status_code == 200
        profile = client.get("/api/v1/auth/me")
        assert profile.status_code == 200
        assert "ai.manage" in profile.json()["permissions"]
