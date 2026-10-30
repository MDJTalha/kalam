import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}
LEARNER = {"email": "learner@demo.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}


def login(client: TestClient, credentials: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **credentials})
    assert response.status_code == 200, response.text


def make_competency(client: TestClient) -> str:
    token = uuid4().hex[:10]
    response = client.post("/api/v1/capability-domain/competencies", json={
        "code": f"PH2-{token}", "name": f"Phase 2 Evidence Competency {token}",
        "definition": "Demonstrates a capability through validated evidence.",
        "type": "functional", "status": "active",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]
def test_evidence_lifecycle_and_provenance_are_governed():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, ADMIN)
        people = client.get("/api/v1/people").json()
        learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
        competency_id = make_competency(client)
        payload = {
            "user_id": learner_id, "target_type": "competency", "target_id": competency_id,
            "evidence_type": "observation", "source_type": "manual_observation",
            "source_id": f"obs-{uuid4()}", "demonstrated_level": 4, "confidence": 85,
            "notes": "Observed during a governed review.",
        }
        created = client.post("/api/v1/evidence", json=payload)
        assert created.status_code == 201, created.text
        evidence_id = created.json()["id"]
        assert client.post("/api/v1/evidence", json=payload).status_code == 409
        verified = client.post(f"/api/v1/evidence/{evidence_id}/decision", json={"decision": "verified"})
        assert verified.status_code == 200
        assert verified.json()["status"] == "verified"
        immutable = client.post(f"/api/v1/evidence/{evidence_id}/decision", json={"decision": "rejected", "reason": "Changed"})
        assert immutable.status_code == 409
        summary = client.get(f"/api/v1/evidence/users/{learner_id}/summary")
        assert summary.status_code == 200
        row = next(item for item in summary.json()["verified_current_evidence"] if item["target_id"] == competency_id)
        assert row["level"] == 4
        assert row["confidence"] == 85
def test_expired_verified_evidence_is_excluded_from_current_state():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, ADMIN)
        people = client.get("/api/v1/people").json()
        learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
        competency_id = make_competency(client)
        observed = datetime.now(UTC) - timedelta(days=2)
        expires = datetime.now(UTC) - timedelta(days=1)
        created = client.post("/api/v1/evidence", json={
            "user_id": learner_id, "target_type": "competency", "target_id": competency_id,
            "evidence_type": "observation", "source_type": "manual_observation",
            "source_id": f"expired-{uuid4()}", "demonstrated_level": 5, "confidence": 100,
            "observed_at": observed.isoformat(), "expires_at": expires.isoformat(),
        })
        assert created.status_code == 201, created.text
        evidence_id = created.json()["id"]
        assert client.post(f"/api/v1/evidence/{evidence_id}/decision", json={"decision": "verified"}).status_code == 200
        summary = client.get(f"/api/v1/evidence/users/{learner_id}/summary")
        assert summary.status_code == 200
        assert all(item["target_id"] != competency_id for item in summary.json()["verified_current_evidence"])
def test_assessment_evidence_is_idempotent_and_tenant_scoped():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, ADMIN)
        people = client.get("/api/v1/people").json()
        learner_id = next(item["id"] for item in people if item["email"] == LEARNER["email"])
        competency_id = make_competency(client)
        assessment = client.post("/api/v1/assessments", json={
            "title": f"Phase 2 Evidence Assessment {uuid4().hex[:8]}", "passing_score": 70,
        })
        assert assessment.status_code == 201, assessment.text
        assessment_id = assessment.json()["id"]
        question = client.post(f"/api/v1/assessments/{assessment_id}/questions", json={
            "question_type": "single_choice",
            "prompt": "Which option demonstrates the governed capability?",
            "options": ["Validated evidence", "Guessing", "Skipping review"],
            "answer_key": {"correct": "Validated evidence"}, "points": 1, "position": 1,
        })
        assert question.status_code == 201, question.text
        mapping = client.post(f"/api/v1/evidence/assessments/{assessment_id}/competencies", json={
            "competency_id": competency_id, "target_level": 4, "weight": 1,
        })
        assert mapping.status_code == 201, mapping.text
        login(client, LEARNER)
        started = client.post(f"/api/v1/assessments/{assessment_id}/start")
        assert started.status_code == 201, started.text
        attempt_id = started.json()["attempt_id"]
        submitted = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={
            "attempt_id": attempt_id,
            "answers": {question.json()["id"]: "Validated evidence"},
        })
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["score"] == 100
        login(client, ADMIN)
        generated = client.post(f"/api/v1/evidence/from-assessment/{attempt_id}")
        assert generated.status_code == 201, generated.text
        assert len(generated.json()) == 1
        assert generated.json()[0]["user_id"] == learner_id
        assert generated.json()[0]["demonstrated_level"] == 5
        repeated = client.post(f"/api/v1/evidence/from-assessment/{attempt_id}")
        assert repeated.status_code == 201, repeated.text
        assert repeated.json()[0]["id"] == generated.json()[0]["id"]
        summary = client.get(f"/api/v1/evidence/users/{learner_id}/summary")
        assert summary.status_code == 200
        assert any(item["target_id"] == competency_id for item in summary.json()["verified_current_evidence"])
        other = client.post("/api/v1/auth/login", json={
            "tenant_slug": "isolation-corporation", "email": "isolated@other.corp", "password": os.environ["CI_FIXTURE_PASSWORD"],
        })
        assert other.status_code == 200
        assert client.post(f"/api/v1/evidence/from-assessment/{attempt_id}").status_code in {403, 404}
        assert client.get(f"/api/v1/evidence/users/{learner_id}/summary").status_code in {403, 404}
