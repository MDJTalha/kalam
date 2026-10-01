from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}
OTHER_TENANT = "isolation-corporation"
OTHER_USER = {"email": "isolated@other.corp", "password": "DemoOnly!1234"}


def login(client: TestClient, tenant: str = TENANT, credentials: dict[str, str] = ADMIN) -> None:
    response = client.post("/api/v1/auth/login", json={"tenant_slug": tenant, **credentials})
    assert response.status_code == 200, response.text


def test_phase1_capability_crud_levels_and_category_governance():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        category = client.post("/api/v1/capabilities/categories", json={
            "name": f"Phase 1 Category {token}",
            "description": "Governed capability domain category.",
        })
        assert category.status_code == 201, category.text
        category_id = category.json()["id"]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1-{token}",
            "name": f"Phase 1 Capability {token}",
            "definition": "A governed organizational capability for Phase 1 validation.",
            "category_id": category_id,
            "criticality": "high",
            "status": "active",
            "governance": {"owner_type": "business", "review_cycle_days": 180},
        })
        assert capability.status_code == 201, capability.text
        capability_id = capability.json()["id"]
        assert capability.json()["code"] == f"P1-{token}".upper()
        assert capability.json()["category_id"] == category_id
        assert capability.json()["level_min"] == 1
        assert capability.json()["level_max"] == 5

        levels = [{
            "level": level,
            "name": ["Foundational", "Developing", "Proficient", "Advanced", "Expert"][level - 1],
            "definition": f"Phase 1 governed level {level}.",
            "indicators": [f"Indicator {level}"],
        } for level in range(1, 6)]
        replaced = client.put(f"/api/v1/capabilities/{capability_id}/levels", json=levels)
        assert replaced.status_code == 200, replaced.text
        assert [x["level"] for x in replaced.json()["levels"]] == [1, 2, 3, 4, 5]

        detail = client.get(f"/api/v1/capabilities/{capability_id}")
        assert detail.status_code == 200
        assert len(detail.json()["levels"]) == 5

        duplicate = client.post("/api/v1/capabilities", json={
            "code": f" P1-{token} ",
            "name": "Duplicate",
            "definition": "This duplicate must be rejected by governed code uniqueness.",
        })
        assert duplicate.status_code == 409

        invalid_levels = client.put(
            f"/api/v1/capabilities/{capability_id}/levels",
            json=levels[:-1],
        )
        assert invalid_levels.status_code == 422


def test_phase1_competency_levels_and_capability_relationship():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1C-{token}",
            "name": f"Phase 1 Relationship Capability {token}",
            "definition": "Capability used to validate competency relationships.",
            "status": "active",
        })
        assert capability.status_code == 201, capability.text
        capability_id = capability.json()["id"]

        competency = client.post("/api/v1/capability-domain/competencies", json={
            "code": f"P1COMP-{token}",
            "name": f"Phase 1 Competency {token}",
            "definition": "A governed competency supporting the capability model.",
            "type": "functional",
            "status": "active",
        })
        assert competency.status_code == 201, competency.text
        competency_id = competency.json()["id"]

        levels = [{
            "level": level,
            "definition": f"Competency level {level} definition.",
            "behavioral_indicators": [f"Competency indicator {level}"],
        } for level in range(1, 6)]
        saved = client.put(
            f"/api/v1/capability-domain/competencies/{competency_id}/levels",
            json=levels,
        )
        assert saved.status_code == 200, saved.text
        assert [x["level"] for x in saved.json()["levels"]] == [1, 2, 3, 4, 5]

        mapped = client.post(
            f"/api/v1/capability-domain/capabilities/{capability_id}/competencies",
            json={"competency_id": competency_id, "weight": 75},
        )
        assert mapped.status_code == 201, mapped.text
        assert mapped.json()["weight"] == 75

        listed = client.get(f"/api/v1/capability-domain/capabilities/{capability_id}/competencies")
        assert listed.status_code == 200
        row = next(x for x in listed.json() if x["competency_id"] == competency_id)
        assert row["weight"] == 75

        updated = client.post(
            f"/api/v1/capability-domain/capabilities/{capability_id}/competencies",
            json={"competency_id": competency_id, "weight": 40},
        )
        assert updated.status_code == 201
        assert updated.json()["weight"] == 40


def test_phase1_strategic_objective_maps_to_capability():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1O-{token}",
            "name": f"Phase 1 Objective Capability {token}",
            "definition": "Capability linked to a strategic objective.",
        })
        assert capability.status_code == 201, capability.text

        objective = client.post("/api/v1/capability-domain/objectives", json={
            "objective": f"Phase 1 Strategic Objective {token}",
            "description": "Validates strategy to capability traceability.",
            "priority": 1,
            "strategic_category": "growth",
            "status": "active",
        })
        assert objective.status_code == 201, objective.text
        objective_id = objective.json()["id"]

        mapped = client.post(
            f"/api/v1/capability-domain/objectives/{objective_id}/capabilities",
            json={"capability_id": capability.json()["id"], "required_level": 4, "weight": 80},
        )
        assert mapped.status_code == 201, mapped.text
        assert mapped.json()["required_level"] == 4
        assert mapped.json()["weight"] == 80

        objectives = client.get("/api/v1/capability-domain/objectives")
        assert objectives.status_code == 200
        assert any(x["id"] == objective_id for x in objectives.json())


def test_phase1_role_requirements_support_capability_competency_and_skill():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]

        roles = client.get("/api/v1/organization/roles")
        assert roles.status_code == 200
        assert roles.json(), "Seeded role is required for Phase 1 role-domain acceptance."
        role_id = roles.json()[0]["id"]

        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1R-{token}",
            "name": f"Phase 1 Role Capability {token}",
            "definition": "Capability used in a governed role requirement.",
        })
        assert capability.status_code == 201, capability.text
        capability_id = capability.json()["id"]

        competency = client.post("/api/v1/capability-domain/competencies", json={
            "code": f"P1RC-{token}",
            "name": f"Phase 1 Role Competency {token}",
            "definition": "Competency used in a governed role requirement.",
        })
        assert competency.status_code == 201, competency.text
        competency_id = competency.json()["id"]

        skill = client.post("/api/v1/skills", json={
            "name": f"Phase 1 Role Skill {token}",
            "description": "Skill created specifically for the role-domain acceptance test.",
            "category": "Acceptance",
        })
        assert skill.status_code == 201, skill.text
        skill_id = skill.json()["id"]

        for target_type, target_id, level in (
            ("capability", capability_id, 4),
            ("competency", competency_id, 3),
            ("skill", skill_id, 2),
        ):
            created = client.post(f"/api/v1/capability-domain/roles/{role_id}/requirements", json={
                "target_type": target_type,
                "target_id": target_id,
                "required_level": level,
                "criticality": "high",
                "weight": 50,
            })
            assert created.status_code == 201, created.text
            assert created.json()["target_type"] == target_type
            assert created.json()["required_level"] == level

        requirements = client.get(f"/api/v1/capability-domain/roles/{role_id}/requirements")
        assert requirements.status_code == 200
        rows = {x["target_type"]: x for x in requirements.json()}
        assert rows["capability"]["target_id"] == capability_id
        assert rows["competency"]["target_id"] == competency_id
        assert rows["skill"]["target_id"] == skill_id


def test_phase1_effective_dating_and_overlap_rules():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        token = uuid4().hex[:10]
        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1D-{token}",
            "name": f"Phase 1 Effective Dating {token}",
            "definition": "Capability used to validate effective-dated governance.",
        })
        assert capability.status_code == 201
        capability_id = capability.json()["id"]

        now = datetime.now(timezone.utc)
        future = now + timedelta(days=30)
        future2 = now + timedelta(days=60)
        invalid = client.post("/api/v1/capabilities", json={
            "code": f"P1INV-{token}",
            "name": f"Invalid Window {token}",
            "definition": "This window is intentionally invalid for validation.",
            "effective_from": future.isoformat(),
            "effective_to": now.isoformat(),
        })
        assert invalid.status_code == 422

        role = client.get("/api/v1/organization/roles").json()[0]["id"]
        first = client.post(f"/api/v1/capability-domain/roles/{role}/requirements", json={
            "target_type": "capability",
            "target_id": capability_id,
            "required_level": 3,
            "effective_from": now.isoformat(),
            "effective_to": future2.isoformat(),
        })
        assert first.status_code == 201, first.text

        overlap = client.post(f"/api/v1/capability-domain/roles/{role}/requirements", json={
            "target_type": "capability",
            "target_id": capability_id,
            "required_level": 4,
            "effective_from": future.isoformat(),
            "effective_to": (future2 + timedelta(days=30)).isoformat(),
        })
        assert overlap.status_code == 409

        non_overlap = client.post(f"/api/v1/capability-domain/roles/{role}/requirements", json={
            "target_type": "capability",
            "target_id": capability_id,
            "required_level": 4,
            "effective_from": (future2 + timedelta(days=1)).isoformat(),
            "effective_to": None,
        })
        assert non_overlap.status_code == 201


def test_phase1_permission_and_tenant_isolation_for_capability_domain():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        capability = client.post("/api/v1/capabilities", json={
            "code": f"P1SEC-{uuid4().hex[:10]}",
            "name": f"Phase 1 Security Capability {uuid4().hex[:6]}",
            "definition": "Capability for tenant and permission boundary testing.",
        })
        assert capability.status_code == 201
        capability_id = capability.json()["id"]

        manager = {"email": "manager@demo.corp", "password": "DemoOnly!1234"}
        login(client, TENANT, manager)
        assert client.get("/api/v1/capabilities").status_code == 200
        assert client.get("/api/v1/capability-domain/competencies").status_code == 403
        assert client.get("/api/v1/capability-domain/objectives").status_code == 403
        assert client.get("/api/v1/capability-domain/proficiency-levels").status_code == 403

        login(client, TENANT, LEARNER)
        assert client.get("/api/v1/capabilities").status_code == 403
        assert client.get("/api/v1/capability-domain/competencies").status_code == 403

        forbidden = client.post("/api/v1/capabilities", json={
            "code": f"P1DENY-{uuid4().hex[:8]}",
            "name": "Denied capability",
            "definition": "Learner must not manage governed capability definitions.",
        })
        assert forbidden.status_code == 403

        login(client, OTHER_TENANT, OTHER_USER)
        assert client.get(f"/api/v1/capabilities/{capability_id}").status_code in {403, 404}
        assert client.get("/api/v1/capabilities").status_code == 403

        assert client.get(f"/api/v1/capability-domain/capabilities/{capability_id}/competencies").status_code in {403, 404}


def test_phase1_validation_rejects_invalid_governed_values():
    with TestClient(app, base_url="http://localhost") as client:
        login(client)

        bad_capability = client.post("/api/v1/capabilities", json={
            "code": "X",
            "name": "X",
            "definition": "short",
            "criticality": "invalid",
        })
        assert bad_capability.status_code == 422

        bad_competency = client.post("/api/v1/capability-domain/competencies", json={
            "code": "X",
            "name": "X",
            "definition": "short",
            "type": "invalid",
        })
        assert bad_competency.status_code == 422

        roles = client.get("/api/v1/organization/roles").json()
        assert roles
        bad_requirement = client.post(
            f"/api/v1/capability-domain/roles/{roles[0]['id']}/requirements",
            json={
                "target_type": "capability",
                "target_id": str(uuid4()),
                "required_level": 9,
                "criticality": "invalid",
            },
        )
        assert bad_requirement.status_code == 422
