import asyncio
import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes.development_intelligence import _priority
from app.db.models import Tenant, User
from app.db.session import SessionLocal
from app.main import app

TENANT = "demo-corporation"
DEMO_PASSWORD = os.environ.get("KALAM_QA_DEMO_PASSWORD", os.environ["CI_FIXTURE_PASSWORD"])
ADMIN = {"email": "admin@demo.corp", "password": DEMO_PASSWORD}


def login(client, credentials=ADMIN, tenant=TENANT):
    response = client.post("/api/v1/auth/login", json={"tenant_slug": tenant, **credentials})
    assert response.status_code == 200, response.text


def test_phase6_priority_governance():
    class Gap:
        criticality = "critical"
        gap_value = Decimal(1)

    assert _priority(Gap(), None) == "critical"

    Gap.criticality = "medium"
    Gap.gap_value = Decimal(2)
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
            assert row.get("tenant_id", True)
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


def test_phase6_evidence_to_recommendation_reassessment_lifecycle():
    """Verified evidence must change gaps, produce recommendations, and retire resolved ones."""
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P6-E2E-{token}",
            "name": f"Phase 6 evidence lifecycle {token}",
            "definition": "Evidence-to-recommendation regression target.",
        })
        assert capability.status_code == 201, capability.text
        capability_id = capability.json()["id"]

        roles = client.get("/api/v1/organization/roles")
        assert roles.status_code == 200 and roles.json(), roles.text
        role_id = roles.json()[0]["id"]

        async def first_tenant_user():
            async with SessionLocal() as db:
                return str((await db.execute(
                    select(User.id)
                    .join(Tenant, Tenant.id == User.tenant_id)
                    .where(Tenant.slug == TENANT, User.is_active.is_(True))
                )).scalars().first())

        user_id = asyncio.run(first_tenant_user())
        assert user_id and user_id != "None"

        requirement = client.post(
            f"/api/v1/capability-domain/roles/{role_id}/requirements",
            json={
                "target_type": "capability",
                "target_id": capability_id,
                "required_level": 4,
                "criticality": "critical",
                "weight": 100,
            },
        )
        assert requirement.status_code == 201, requirement.text
        requirement_id = requirement.json()["id"]

        assignment = client.post(f"/api/v1/organization/users/{user_id}/roles/{role_id}")
        assert assignment.status_code in {200, 201, 409}, assignment.text
        recalculated = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalculated.status_code == 200, recalculated.text

        def gap_row():
            response = client.get(
                f"/api/v1/capability-gaps?user_id={user_id}&role_id={role_id}"
            )
            assert response.status_code == 200, response.text
            return next(
                row for row in response.json()
                if row["role_requirement_id"] == requirement_id
            )

        def gap_snapshot_id():
            response = client.get(f"/api/v1/capability-gaps/snapshots?user_id={user_id}")
            assert response.status_code == 200, response.text
            return next(
                row["id"] for row in response.json()
                if row["role_requirement_id"] == requirement_id
            )

        initial_gap = gap_row()
        assert initial_gap["severity"] == "insufficient_evidence"

        evidence = client.post("/api/v1/evidence", json={
            "user_id": user_id,
            "target_type": "capability",
            "target_id": capability_id,
            "evidence_type": "assessment_result",
            "source_type": "assessment",
            "source_id": f"p6-e2e-low-{token}",
            "demonstrated_level": 2,
            "confidence": 90,
            "observed_at": datetime.now(UTC).isoformat(),
        })
        assert evidence.status_code == 201, evidence.text
        decision = client.post(
            f"/api/v1/evidence/{evidence.json()['id']}/decision",
            json={"decision": "verified"},
        )
        assert decision.status_code == 200, decision.text
        recalculated = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalculated.status_code == 200, recalculated.text

        measured_gap = gap_row()
        assert measured_gap["demonstrated_level"] == 2
        assert measured_gap["severity"] in {"major_gap", "critical_gap"}

        recommendations = client.get(
            f"/api/v1/development/recommendations?user_id={user_id}&limit=200"
        )
        assert recommendations.status_code == 200, recommendations.text
        measured_gap_id = gap_snapshot_id()
        active_for_gap = [
            item for item in recommendations.json()
            if item["capability_gap_id"] == measured_gap_id
        ]
        assert active_for_gap, "A verified material capability gap should produce recommendations."
        assert all(item["rationale"] and item["metadata"] for item in active_for_gap)

        # Accept a recommendation before reassessment, linking the intervention
        # action to the subsequent evidence-driven capability-gap reconciliation.
        accepted_recommendation = client.post(
            f"/api/v1/development/recommendations/{active_for_gap[0]['id']}/accept"
        )
        assert accepted_recommendation.status_code == 200, accepted_recommendation.text
        assert accepted_recommendation.json()["status"] == "accepted"

        stronger_evidence = client.post("/api/v1/evidence", json={
            "user_id": user_id,
            "target_type": "capability",
            "target_id": capability_id,
            "evidence_type": "assessment_result",
            "source_type": "assessment",
            "source_id": f"p6-e2e-met-{token}",
            "demonstrated_level": 4,
            "confidence": 95,
            "observed_at": datetime.now(UTC).isoformat(),
        })
        assert stronger_evidence.status_code == 201, stronger_evidence.text
        stronger_decision = client.post(
            f"/api/v1/evidence/{stronger_evidence.json()['id']}/decision",
            json={"decision": "verified"},
        )
        assert stronger_decision.status_code == 200, stronger_decision.text
        recalculated = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalculated.status_code == 200, recalculated.text

        resolved_gap = gap_row()
        assert resolved_gap["demonstrated_level"] == 4
        assert resolved_gap["severity"] == "met"

        reconciled = client.get(
            f"/api/v1/development/recommendations?user_id={user_id}&limit=200"
        )
        assert reconciled.status_code == 200, reconciled.text
        resolved_gap_id = gap_snapshot_id()
        assert not any(
            item["capability_gap_id"] == resolved_gap_id
            and item["status"] == "recommended"
            for item in reconciled.json()
        ), "Recommendations for a resolved gap must no longer remain active."
