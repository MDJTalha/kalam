from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}


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


def test_phase7_recommendation_to_intervention_to_verified_evidence_lifecycle():
    import asyncio
    from sqlalchemy import select
    from app.db.models import Tenant, User
    from app.db.session import SessionLocal

    async def first_active_user():
        async with SessionLocal() as db:
            return str((await db.execute(
                select(User.id)
                .join(Tenant, Tenant.id == User.tenant_id)
                .where(Tenant.slug == TENANT, User.is_active.is_(True))
            )).scalars().first())

    user_id = asyncio.run(first_active_user())
    assert user_id and user_id != "None"

    with TestClient(app, base_url="http://localhost") as client:
        login(client)

        recalc = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalc.status_code == 200, recalc.text

        recommendations = client.get(
            f"/api/v1/development/recommendations?user_id={user_id}&limit=50"
        )
        assert recommendations.status_code == 200, recommendations.text
        rows = recommendations.json()
        assert rows, "seeded capability lifecycle should produce a development recommendation"
        recommendation = rows[0]

        intervention = client.post(
            "/api/v1/development/interventions",
            json={
                "user_id": user_id,
                "recommendation_id": recommendation["id"],
                "intervention_type": recommendation["intervention_type"],
                "title": "Phase 7 lifecycle intervention",
                "objective": "Create verified development evidence and feed it back into capability state.",
            },
        )
        assert intervention.status_code == 201, intervention.text
        intervention_id = intervention.json()["id"]

        evidence = client.post(
            f"/api/v1/development/interventions/{intervention_id}/evidence",
            json={
                "evidence_type": "assessment",
                "description": "Lifecycle regression evidence.",
                "observed_at": "2026-10-31T12:00:00Z",
                "demonstrated_level": 4,
            },
        )
        assert evidence.status_code == 201, evidence.text
        evidence_id = evidence.json()["id"]

        verified = client.post(
            f"/api/v1/development/interventions/{intervention_id}/evidence/{evidence_id}/verify"
        )
        assert verified.status_code == 200, verified.text
        assert verified.json()["verification_status"] == "verified"
        assert verified.json()["metadata_json"]["capability_evidence_created"] is True
        assert verified.json()["metadata_json"]["capability_gap_recalculated"] is True

        progress = client.get(
            f"/api/v1/development/interventions/{intervention_id}/progress"
        )
        assert progress.status_code == 200, progress.text
        assert progress.json()["verified_evidence_count"] == 1
        assert progress.json()["progress_signal"] == "evidence_verified"

        completed = client.patch(
            f"/api/v1/development/interventions/{intervention_id}",
            json={"status": "completed"},
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "completed"
