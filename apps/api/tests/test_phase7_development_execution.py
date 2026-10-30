import os

from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
DEMO_PASSWORD = os.environ.get("KALAM_QA_DEMO_PASSWORD", os.environ["CI_FIXTURE_PASSWORD"])
ADMIN = {"email": "admin@demo.corp", "password": DEMO_PASSWORD}


def login(client):
    response = client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
    assert response.status_code == 200, response.text


def test_phase7_intervention_list_contract():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        response = client.get("/api/v1/development/interventions")
        assert response.status_code == 200, response.text
        assert isinstance(response.json(), list)


def test_phase7_intervention_not_found_is_tenant_safe():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        missing = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/development/interventions/{missing}")
        assert response.status_code == 404

        response = client.patch(
            f"/api/v1/development/interventions/{missing}",
            json={"status": "completed"},
        )
        assert response.status_code == 404


def test_phase7_invalid_status_is_rejected():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        response = client.get("/api/v1/development/interventions?status_filter=invalid")
        assert response.status_code == 422
