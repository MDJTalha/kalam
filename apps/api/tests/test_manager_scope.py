from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
PASSWORD = __import__("os").environ["CI_FIXTURE_PASSWORD"]


def login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": TENANT, "email": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


def test_manager_is_limited_to_direct_reports_and_team_reports() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client, "manager@demo.corp")

        profile = client.get("/api/v1/auth/me")
        assert profile.status_code == 200
        assert "users.team.read" in profile.json()["permissions"]
        assert "reports.team.read" in profile.json()["permissions"]
        assert "users.read" not in profile.json()["permissions"]
        assert "reports.read" not in profile.json()["permissions"]

        # The manager cannot enumerate the full tenant people directory.
        assert client.get("/api/v1/people/page").status_code == 403

        team = client.get("/api/v1/people/team")
        assert team.status_code == 200, team.text
        assert len(team.json()) == 1
        direct_report_id = team.json()[0]["id"]

        # Direct report details remain available.
        direct_report = client.get(f"/api/v1/people/{direct_report_id}")
        assert direct_report.status_code == 200, direct_report.text

        # A different employee is deliberately undiscoverable to this manager.
        everyone_else = client.get("/api/v1/people")
        assert everyone_else.status_code == 403

        team_report = client.get("/api/v1/reports/my-team")
        assert team_report.status_code == 200, team_report.text
        report = team_report.json()
        assert report["scope"] == "direct_reports"
        assert report["team_members"] == 1
        assert report["enrollments"] >= 0

        # Tenant-wide manager benchmarking is not part of the Manager role.
        assert client.get("/api/v1/reports/manager-performance").status_code == 403


def test_learner_cannot_read_manager_team_report() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        login(client, "learner@demo.corp")
        assert client.get("/api/v1/people/team").status_code == 403
        assert client.get("/api/v1/reports/my-team").status_code == 403


def test_manager_can_manage_only_direct_report_development_interventions() -> None:
    from datetime import UTC, datetime

    with TestClient(app, base_url="http://localhost") as client:
        login(client, "manager@demo.corp")
        profile = client.get("/api/v1/auth/me").json()
        permissions = set(profile["permissions"])
        assert "development.team.read" in permissions
        assert "development.team.manage" in permissions
        assert "development.recommendations.manage" not in permissions

        team = client.get("/api/v1/people/team")
        assert team.status_code == 200 and len(team.json()) == 1
        direct_report_id = team.json()[0]["id"]

        created = client.post(
            "/api/v1/development/interventions",
            json={
                "user_id": direct_report_id,
                "intervention_type": "coaching",
                "title": "Direct report coaching",
                "objective": "Build confidence through structured practice.",
            },
        )
        assert created.status_code == 201, created.text
        intervention_id = created.json()["id"]

        details = client.get(f"/api/v1/development/interventions/{intervention_id}")
        assert details.status_code == 200, details.text

        interaction = client.post(
            f"/api/v1/development/interventions/{intervention_id}/interactions",
            json={
                "interaction_type": "coaching_session",
                "occurred_at": datetime.now(UTC).isoformat(),
                "duration_minutes": 30,
                "summary": "Reviewed progress and agreed next actions.",
            },
        )
        assert interaction.status_code == 201, interaction.text

        evidence = client.post(
            f"/api/v1/development/interventions/{intervention_id}/evidence",
            json={
                "evidence_type": "manager_observation",
                "description": "Observed the employee demonstrate the agreed practice.",
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        assert evidence.status_code == 201, evidence.text

        # A Manager cannot create team interventions for their own account;
        # that is outside the delegated direct-report workflow.
        own_intervention = client.post(
            "/api/v1/development/interventions",
            json={
                "user_id": profile["id"],
                "intervention_type": "coaching",
                "title": "Out-of-scope self intervention",
                "objective": "Must not be created through team-management permission.",
            },
        )
        assert own_intervention.status_code == 403


def test_manager_can_manage_direct_report_intervention_but_not_self_service_as_team_admin() -> None:
    from datetime import UTC, datetime

    with TestClient(app, base_url="http://localhost") as client:
        login(client, "manager@demo.corp")
        profile = client.get("/api/v1/auth/me").json()
        permissions = set(profile["permissions"])
        assert "development.team.read" in permissions
        assert "development.team.manage" in permissions
        assert "development.recommendations.manage" not in permissions

        team = client.get("/api/v1/people/team")
        assert team.status_code == 200 and len(team.json()) == 1
        direct_report_id = team.json()[0]["id"]

        created = client.post(
            "/api/v1/development/interventions",
            json={
                "user_id": direct_report_id,
                "intervention_type": "coaching",
                "title": "Direct report coaching",
                "objective": "Build confidence through structured practice.",
            },
        )
        assert created.status_code == 201, created.text
        intervention_id = created.json()["id"]

        listed = client.get(
            "/api/v1/development/interventions",
            params={"user_id": direct_report_id, "include_progress": "true"},
        )
        assert listed.status_code == 200, listed.text
        assert any(item["id"] == intervention_id for item in listed.json())

        interaction = client.post(
            f"/api/v1/development/interventions/{intervention_id}/interactions",
            json={
                "interaction_type": "coaching_session",
                "occurred_at": datetime.now(UTC).isoformat(),
                "duration_minutes": 30,
                "summary": "Reviewed progress and agreed next actions.",
            },
        )
        assert interaction.status_code == 201, interaction.text

        evidence = client.post(
            f"/api/v1/development/interventions/{intervention_id}/evidence",
            json={
                "evidence_type": "manager_observation",
                "description": "Observed the employee demonstrate the agreed practice.",
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        assert evidence.status_code == 201, evidence.text

        # Team-management permission is not a general self-service override.
        own_intervention = client.post(
            "/api/v1/development/interventions",
            json={
                "user_id": profile["id"],
                "intervention_type": "coaching",
                "title": "Out-of-scope self intervention",
                "objective": "Must not be created through team-management permission.",
            },
        )
        assert own_intervention.status_code == 403
