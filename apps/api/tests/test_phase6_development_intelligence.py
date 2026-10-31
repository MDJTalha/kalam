from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.development_intelligence import _priority


TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}


def login(client, credentials=ADMIN, tenant=TENANT):
    response = client.post("/api/v1/auth/login", json={"tenant_slug": tenant, **credentials})
    assert response.status_code == 200, response.text


def test_phase6_priority_governance():
    class Gap:
        criticality = "critical"
        gap_value = Decimal("1")

    assert _priority(Gap(), None) == "critical"

    Gap.criticality = "medium"
    Gap.gap_value = Decimal("2")
    assert _priority(Gap(), None) == "high"

    Gap.gap_value = Decimal("0.5")
    assert _priority(Gap(), None) == "medium"


def test_phase6_recommendations_contract_and_filter():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)

        response = client.get("/api/v1/development/recommendations?limit=10")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert isinstance(rows, list)

        for row in rows:
            assert row["tenant_id"] if "tenant_id" in row else True
            assert 0 <= row["score"] <= 100
            assert row["intervention_type"] in {
                "learning", "coaching", "mentoring", "experiential", "evidence_building"
            }
            assert row["status"] in {"recommended", "accepted"}
            assert row["recommendation_version"].startswith("phase6.")
            assert row["rationale"]

        learning = client.get(
            "/api/v1/development/recommendations?intervention_type=learning&limit=50"
        )
        assert learning.status_code == 200, learning.text
        assert all(item["intervention_type"] == "learning" for item in learning.json())

        bounded = client.get("/api/v1/development/recommendations?limit=1")
        assert bounded.status_code == 200, bounded.text
        assert len(bounded.json()) <= 1


def test_phase6_no_cross_tenant_recommendation_access():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        own = client.get("/api/v1/development/recommendations")
        assert own.status_code == 200

        # A nonexistent UUID must never resolve through another tenant's scope.
        denied = client.get(
            "/api/v1/development/recommendations?user_id=00000000-0000-0000-0000-000000000000"
        )
        assert denied.status_code in {403, 404}


def test_phase6_accept_endpoint_requires_existing_recommendation():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        response = client.post(
            "/api/v1/development/recommendations/00000000-0000-0000-0000-000000000000/accept"
        )
        assert response.status_code == 404
