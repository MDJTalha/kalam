import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import ComplianceAssignment, ComplianceEvidence, ComplianceException
from app.db.session import SessionLocal
from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}


def login(client: TestClient, credentials: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, **credentials},
    )
    assert response.status_code == 200, response.text


def test_phase8_compliance_operations_recurrence_and_exception_expiry() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client, ADMIN)
        token = uuid4().hex[:8]
        requirement = client.post(
            "/api/v1/compliance",
            json={
                "name": "Phase 8 Recurring Compliance " + token,
                "description": "Operational recurrence proof",
                "due_days": 30,
                "recurrence_days": 1,
                "active": True,
                "rules": {"escalation_days": 1},
            },
        )
        assert requirement.status_code == 201, requirement.text
        requirement_id = requirement.json()["id"]

        people = client.get("/api/v1/people").json()
        learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
        assignment = client.post(
            f"/api/v1/compliance/{requirement_id}/assign",
            json={"user_id": learner_id},
        )
        assert assignment.status_code == 201, assignment.text
        assignment_id = assignment.json()["id"]

        login(client, LEARNER)
        mine = client.get("/api/v1/compliance/my").json()
        learner_assignment_id = next(item["id"] for item in mine if item["id"] == assignment_id)
        evidence = client.post(
            f"/api/v1/compliance/my/{learner_assignment_id}/evidence",
            json={
                "evidence_type": "attestation",
                "reference": "phase8-attestation-" + token,
                "notes": "Verified operational proof",
            },
        )
        assert evidence.status_code == 201, evidence.text
        evidence_id = evidence.json()["id"]

        login(client, ADMIN)
        verified = client.post(f"/api/v1/compliance/evidence/{evidence_id}/verify")
        assert verified.status_code == 200, verified.text
        review_page = client.get("/api/v1/compliance/evidence?verified=true&limit=1&offset=0")
        assert review_page.status_code == 200, review_page.text
        assert review_page.json()["total"] >= 1
        assert len(review_page.json()["items"]) == 1
        oversized_review_page = client.get("/api/v1/compliance/evidence?limit=101")
        assert oversized_review_page.status_code == 422

        async def age_verified_evidence() -> None:
            async with SessionLocal() as db:
                item = await db.get(ComplianceEvidence, evidence_id)
                assert item is not None
                item.verified_at = datetime.now(timezone.utc) - timedelta(days=2)
                await db.commit()

        asyncio.run(age_verified_evidence())

        run = client.post("/api/v1/compliance/operations/run")
        assert run.status_code == 200, run.text
        assert run.json()["recurring_created"] == 1

        second_run = client.post("/api/v1/compliance/operations/run")
        assert second_run.status_code == 200, second_run.text
        assert second_run.json()["recurring_created"] == 0

        exception_assignment = client.post(
            f"/api/v1/compliance/{requirement_id}/assign",
            json={"user_id": client.get("/api/v1/people").json()[1]["id"]},
        )
        assert exception_assignment.status_code in {201, 409}
        if exception_assignment.status_code == 409:
            refreshed = client.get("/api/v1/compliance/assignments?limit=50").json()
            exception_assignment_id = next(
                item["id"] for item in refreshed["items"]
                if item["requirement"] == requirement.json()["name"] and item["status"] in {"assigned", "overdue"}
            )
        else:
            exception_assignment_id = exception_assignment.json()["id"]

        exception = client.post(
            f"/api/v1/compliance/{exception_assignment_id}/exceptions",
            json={
                "reason": "Phase 8 expiry lifecycle proof",
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            },
        )
        assert exception.status_code == 201, exception.text
        exception_id = exception.json()["id"]
        approved = client.post(f"/api/v1/compliance/exceptions/{exception_id}/approve")
        assert approved.status_code == 200, approved.text

        async def expire_exception() -> None:
            async with SessionLocal() as db:
                item = await db.get(ComplianceException, exception_id)
                assignment_item = await db.get(ComplianceAssignment, exception_assignment_id)
                assert item is not None and assignment_item is not None
                item.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
                assignment_item.status = "excepted"
                await db.commit()

        asyncio.run(expire_exception())

        expired_run = client.post("/api/v1/compliance/operations/run")
        assert expired_run.status_code == 200, expired_run.text
        assert expired_run.json()["expired_exceptions"] == 1

        async def check_exception_state() -> tuple[str, str]:
            async with SessionLocal() as db:
                item = await db.get(ComplianceException, exception_id)
                assignment_item = await db.get(ComplianceAssignment, exception_assignment_id)
                return item.status, assignment_item.status

        exception_status, assignment_status = asyncio.run(check_exception_state())
        assert exception_status == "expired"
        assert assignment_status in {"assigned", "overdue"}


def test_phase8_compliance_escalation_is_idempotent() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client, ADMIN)
        token = uuid4().hex[:8]
        requirement = client.post(
            "/api/v1/compliance",
            json={
                "name": "Phase 8 Escalation " + token,
                "due_days": 30,
                "active": True,
                "rules": {"escalation_days": 1},
            },
        )
        assert requirement.status_code == 201, requirement.text
        requirement_id = requirement.json()["id"]
        people = client.get("/api/v1/people").json()
        learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])

        assignment = client.post(
            f"/api/v1/compliance/{requirement_id}/assign",
            json={"user_id": learner_id},
        )
        assert assignment.status_code == 201, assignment.text
        assignment_id = assignment.json()["id"]

        async def age_assignment() -> None:
            async with SessionLocal() as db:
                item = await db.get(ComplianceAssignment, assignment_id)
                assert item is not None
                item.due_at = datetime.now(timezone.utc) - timedelta(days=3)
                item.status = "assigned"
                await db.commit()

        asyncio.run(age_assignment())

        run = client.post("/api/v1/compliance/operations/run")
        assert run.status_code == 200, run.text
        assert run.json()["overdue"] == 1
        assert run.json()["escalated"] == 1

        second_run = client.post("/api/v1/compliance/operations/run")
        assert second_run.status_code == 200, second_run.text
        assert second_run.json()["escalated"] == 0

        summary = client.get("/api/v1/compliance/operations/summary")
        assert summary.status_code == 200, summary.text
        assert summary.json()["overdue"] >= 1
