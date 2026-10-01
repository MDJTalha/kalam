from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.models import CapabilityGap, CapabilityEvidence, RoleRequirement, User, UserRole


TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
OTHER_TENANT = "isolation-corporation"
OTHER_USER = {"email": "isolated@other.corp", "password": "DemoOnly!1234"}


def login(client, credentials=ADMIN, tenant=TENANT):
    r = client.post("/api/v1/auth/login", json={"tenant_slug": tenant, **credentials})
    assert r.status_code == 200, r.text


def test_phase4_severity_matrix():
    from app.api.routes.capability_gap import _severity
    cases = [
        (Decimal("4"), None, "insufficient_evidence"),
        (Decimal("4"), Decimal("4"), "met"),
        (Decimal("4"), Decimal("3.6"), "minor_gap"),
        (Decimal("4"), Decimal("3"), "moderate_gap"),
        (Decimal("4"), Decimal("2"), "major_gap"),
        (Decimal("4"), Decimal("1"), "critical_gap"),
    ]
    for required, demonstrated, expected in cases:
        assert _severity(required, demonstrated) == expected


def test_phase4_negative_gap_is_met():
    from app.api.routes.capability_gap import _severity
    assert _severity(Decimal("3"), Decimal("4")) == "met"


def test_phase4_end_to_end_requirement_evidence_and_recalculation():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P4-{token}", "name": f"P4 Gap Capability {token}",
            "definition": "End-to-end Phase 4 gap target."
        })
        assert capability.status_code == 201, capability.text
        capability_id = capability.json()["id"]

        roles = client.get("/api/v1/organization/roles")
        assert roles.status_code == 200 and roles.json()
        role_id = roles.json()[0]["id"]

        # Use a seeded user without relying on a non-existent /users listing route.
        import asyncio
        from app.db.session import SessionLocal
        async def first_user():
            async with SessionLocal() as db:
                return str((await db.execute(select(User.id).where(User.tenant_id.is_not(None), User.is_active.is_(True)))).scalars().first())
        user_id = asyncio.run(first_user())
        assert user_id and user_id != "None"

        req = client.post(f"/api/v1/capability-domain/roles/{role_id}/requirements", json={
            "target_type": "capability", "target_id": capability_id,
            "required_level": 4, "criticality": "critical", "weight": 100
        })
        assert req.status_code == 201, req.text
        req_id = req.json()["id"]

        assignment = client.post(f"/api/v1/organization/users/{user_id}/roles/{role_id}")
        assert assignment.status_code in {200, 201, 409}, assignment.text

        recalculated = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalculated.status_code == 200, recalculated.text

        gaps = client.get(f"/api/v1/capability-gaps?user_id={user_id}&role_id={role_id}")
        assert gaps.status_code == 200, gaps.text
        row = next(x for x in gaps.json() if x["role_requirement_id"] == req_id)
        assert row["required_level"] == 4
        assert row["demonstrated_level"] is None
        assert row["severity"] == "insufficient_evidence"

        source = f"phase4-{token}"
        evidence = client.post("/api/v1/evidence", json={
            "user_id": user_id, "target_type": "capability", "target_id": capability_id,
            "evidence_type": "assessment_result", "source_type": "assessment",
            "source_id": source, "demonstrated_level": 3, "confidence": 90,
            "observed_at": datetime.now(timezone.utc).isoformat()
        })
        assert evidence.status_code == 201, evidence.text
        evidence_id = evidence.json()["id"]

        decision = client.post(f"/api/v1/evidence/{evidence_id}/decision", json={
            "decision": "verified"
        })
        assert decision.status_code == 200, decision.text

        recalculated = client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}")
        assert recalculated.status_code == 200, recalculated.text
        row = next(x for x in client.get(f"/api/v1/capability-gaps?user_id={user_id}&role_id={role_id}").json()
                   if x["role_requirement_id"] == req_id)
        assert row["demonstrated_level"] == 3
        assert row["gap"] == 1
        assert row["severity"] == "moderate_gap"
        assert row["evidence_confidence"] == 90

        fresh_summary = client.get(f"/api/v1/capability-gaps/summary?scope=person&scope_id={user_id}")
        assert fresh_summary.status_code == 200
        assert fresh_summary.json()["material_gaps"] >= 1

        snapshots = client.get(f"/api/v1/capability-gaps/snapshots?user_id={user_id}")
        assert snapshots.status_code == 200
        assert any(x["role_requirement_id"] == req_id for x in snapshots.json())


def test_phase4_stale_evidence_becomes_insufficient_evidence():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]
        capability = client.post("/api/v1/capabilities", json={
            "code": f"P4S-{token}", "name": f"P4 Stale Capability {token}",
            "definition": "Stale evidence target."
        })
        assert capability.status_code == 201
        roles = client.get("/api/v1/organization/roles").json()
        role_id = roles[0]["id"]
        import asyncio
        from app.db.session import SessionLocal
        async def first_user():
            async with SessionLocal() as db:
                return str((await db.execute(select(User.id).where(User.is_active.is_(True)))).scalars().first())
        user_id = asyncio.run(first_user())
        assert user_id and user_id != "None"
        req = client.post(f"/api/v1/capability-domain/roles/{role_id}/requirements", json={
            "target_type": "capability", "target_id": capability.json()["id"],
            "required_level": 4, "criticality": "high", "weight": 10
        })
        assert req.status_code == 201
        assert client.post(f"/api/v1/organization/users/{user_id}/roles/{role_id}").status_code in {201, 200}

        # Evidence API rejects observations too far in the past; create a
        # Create a valid record, then backdate it directly to exercise Phase 4 freshness.
        evidence = client.post("/api/v1/evidence", json={
            "user_id": user_id, "target_type": "capability", "target_id": capability.json()["id"],
            "evidence_type": "assessment_result", "source_type": "assessment", "source_id": f"stale-{token}",
            "demonstrated_level": 5, "confidence": 100
        })
        assert evidence.status_code == 201
        evidence_id = evidence.json()["id"]
        assert client.post(f"/api/v1/evidence/{evidence_id}/decision", json={"decision": "verified"}).status_code == 200

        import asyncio
        async def backdate():
            async with SessionLocal() as db:
                item = await db.scalar(select(CapabilityEvidence).where(CapabilityEvidence.id == evidence_id))
                item.observed_at = datetime.now(timezone.utc) - timedelta(days=181)
                await db.commit()
        asyncio.run(backdate())

        assert client.post(f"/api/v1/capability-gaps/recalculate?user_id={user_id}").status_code == 200
        rows = client.get(f"/api/v1/capability-gaps?user_id={user_id}&role_id={role_id}").json()
        row = next(x for x in rows if x["role_requirement_id"] == req.json()["id"])
        assert row["demonstrated_level"] is None
        assert row["severity"] == "insufficient_evidence"


def test_phase4_manager_and_tenant_isolation():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        own = client.get("/api/v1/capability-gaps")
        assert own.status_code == 200

        login(client, tenant=OTHER_TENANT, credentials=OTHER_USER)
        assert client.get("/api/v1/capability-gaps").status_code in {200, 403}
        assert client.get("/api/v1/capability-gaps/snapshots").status_code in {200, 403}
