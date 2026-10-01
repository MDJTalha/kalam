from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}
OTHER_TENANT = "isolation-corporation"
OTHER_USER = {"email": "isolated@other.corp", "password": "DemoOnly!1234"}


def login(client: TestClient, tenant: str, credentials: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/login", json={"tenant_slug": tenant, **credentials})
    assert response.status_code == 200, response.text


def competency_id(client: TestClient) -> str:
    token = uuid4().hex[:8]
    response = client.post("/api/v1/capability-domain/competencies", json={
        "code": "P3-" + token,
        "name": "Phase 3 Demonstrated Capability " + token,
        "definition": "A governed competency used to validate capability measurement.",
        "type": "functional", "status": "active",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_engine(client: TestClient, kind: str = "self") -> tuple[str, str]:
    cid = competency_id(client)
    response = client.post("/api/v1/assessments", json={
        "title": "Phase 3 " + kind + " assessment " + uuid4().hex[:8],
        "passing_score": 70, "assessment_type": kind,
        "measurement_method": "level_based" if kind == "self" else "360_aggregate",
        "validity_days": 30,
    })
    assert response.status_code == 201, response.text
    assessment_id = response.json()["id"]
    mapped = client.post("/api/v1/capability-assessments/assessments/" + assessment_id + "/targets", json={
        "target_type": "competency", "target_id": cid, "target_level": 4.0, "weight": 1,
    })
    assert mapped.status_code == 201, mapped.text
    return assessment_id, cid


def person_id(client: TestClient) -> str:
    people = client.get("/api/v1/people").json()
    return next(item["id"] for item in people if item["email"] == LEARNER["email"])
def test_baseline_reassessment_and_improvement_are_governed():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, TENANT, ADMIN)
        assessment_id, target_id = create_engine(client)
        learner_id = person_id(client)

        cycle = client.post("/api/v1/capability-assessments/assessments/" + assessment_id + "/cycles", json={
            "user_id": learner_id, "target_type": "competency",
            "target_id": target_id, "required_level": 4.0,
        })
        assert cycle.status_code == 201, cycle.text
        cycle_id = cycle.json()["id"]

        login(client, TENANT, LEARNER)
        started = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/attempts?stage=baseline")
        assert started.status_code == 201, started.text
        attempt_id = started.json()["id"]

        outcome = client.post("/api/v1/capability-assessments/attempts/" + attempt_id + "/outcomes", json={
            "target_type": "competency", "target_id": target_id, "demonstrated_level": 2.6, "confidence": 82,
        })
        assert outcome.status_code == 200, outcome.text
        assert outcome.json()["demonstrated_level"] == 2.6

        completed = client.post("/api/v1/capability-assessments/attempts/" + attempt_id + "/complete")
        assert completed.status_code == 200, completed.text
        assert completed.json()["demonstrated_level"] == 2.6

        login(client, TENANT, ADMIN)
        summary = client.get("/api/v1/capability-assessments/cycles/" + cycle_id)
        assert summary.status_code == 200, summary.text
        assert summary.json()["baseline_level"] == 2.6
        due = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/mark-reassessment-due")
        assert due.status_code == 200, due.text
        assert due.json()["status"] == "reassessment_due"

        login(client, TENANT, LEARNER)
        reassess = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/reassessment")
        assert reassess.status_code == 201, reassess.text
        reassess_id = reassess.json()["id"]

        saved = client.post("/api/v1/capability-assessments/attempts/" + reassess_id + "/outcomes", json={
            "target_type": "competency", "target_id": target_id, "demonstrated_level": 3.7, "confidence": 91,
        })
        assert saved.status_code == 200, saved.text

        done = client.post("/api/v1/capability-assessments/attempts/" + reassess_id + "/complete")
        assert done.status_code == 200, done.text
        assert done.json()["demonstrated_level"] == 3.7
        assert done.json()["cycle"]["improvement"] == 1.1

        evidence = client.get("/api/v1/evidence/users/" + learner_id + "/summary")
        assert evidence.status_code == 200, evidence.text
        row = next(x for x in evidence.json()["verified_current_evidence"] if x["target_id"] == target_id)
        assert row["level"] == 3.7


def test_360_cycle_aggregates_completed_reviewer_outcomes():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, TENANT, ADMIN)
        assessment_id, target_id = create_engine(client, "360")
        learner_id = person_id(client)

        cycle = client.post("/api/v1/capability-assessments/assessments/" + assessment_id + "/cycles", json={
            "user_id": learner_id, "target_type": "competency",
            "target_id": target_id, "required_level": 4.0,
        })
        assert cycle.status_code == 201, cycle.text
        cycle_id = cycle.json()["id"]
        admin_id = client.get("/api/v1/people/me").json()["id"]
        reviewer = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/reviewers", json={
            "reviewer_id": admin_id, "reviewer_type": "assessor",
        })
        assert reviewer.status_code == 201, reviewer.text
        reviewer2 = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/reviewers", json={
            "reviewer_id": learner_id, "reviewer_type": "self",
        })
        assert reviewer2.status_code == 201, reviewer2.text

        admin_attempt = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/attempts?stage=baseline")
        assert admin_attempt.status_code == 201, admin_attempt.text
        admin_attempt_id = admin_attempt.json()["id"]
        saved_admin = client.post("/api/v1/capability-assessments/attempts/" + admin_attempt_id + "/outcomes", json={
            "target_type": "competency", "target_id": target_id, "demonstrated_level": 3.0, "confidence": 90,
        })
        assert saved_admin.status_code == 200, saved_admin.text
        completed_admin = client.post("/api/v1/capability-assessments/attempts/" + admin_attempt_id + "/complete")
        assert completed_admin.status_code == 200, completed_admin.text

        login(client, TENANT, LEARNER)
        learner_attempt = client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/attempts?stage=baseline")
        assert learner_attempt.status_code == 201, learner_attempt.text
        learner_attempt_id = learner_attempt.json()["id"]
        saved_learner = client.post("/api/v1/capability-assessments/attempts/" + learner_attempt_id + "/outcomes", json={
            "target_type": "competency", "target_id": target_id, "demonstrated_level": 4.0, "confidence": 88,
        })
        assert saved_learner.status_code == 200, saved_learner.text
        completed_learner = client.post("/api/v1/capability-assessments/attempts/" + learner_attempt_id + "/complete")
        assert completed_learner.status_code == 200, completed_learner.text
        assert completed_learner.json()["cycle"]["baseline_level"] == 3.5


def test_capability_assessment_cycles_are_tenant_scoped():
    with TestClient(app, base_url="http://localhost") as client:
        login(client, TENANT, ADMIN)
        assessment_id, target_id = create_engine(client)
        learner_id = person_id(client)
        cycle = client.post("/api/v1/capability-assessments/assessments/" + assessment_id + "/cycles", json={
            "user_id": learner_id, "target_type": "competency",
            "target_id": target_id, "required_level": 4.0,
        })
        assert cycle.status_code == 201, cycle.text
        cycle_id = cycle.json()["id"]

        login(client, OTHER_TENANT, OTHER_USER)
        assert client.get("/api/v1/capability-assessments/cycles/" + cycle_id).status_code in {403, 404}
        assert client.post("/api/v1/capability-assessments/cycles/" + cycle_id + "/attempts?stage=baseline").status_code in {403, 404}
