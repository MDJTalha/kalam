from fastapi.testclient import TestClient

from app.main import app

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}


def test_phase6_metric_contracts_reconcile():
    with TestClient(app, base_url="http://localhost") as client:
        login = client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        assert login.status_code == 200, login.text

        summary = client.get("/api/v1/reports/summary")
        effectiveness = client.get("/api/v1/reports/learning-effectiveness")
        performance = client.get("/api/v1/reports/course-performance", params={"page": 1, "page_size": 25, "sort_by": "enrollments", "sort_dir": "desc"})
        risk = client.get("/api/v1/reports/compliance-risk")

        assert summary.status_code == 200
        assert effectiveness.status_code == 200
        assert performance.status_code == 200
        assert risk.status_code == 200

        summary_data = summary.json()
        effectiveness_data = effectiveness.json()
        performance_data = performance.json()
        risk_data = risk.json()

        assert 0 <= summary_data["completed_enrollments"] <= summary_data["enrollments"]
        assert 0 <= effectiveness_data["completed"] <= summary_data["enrollments"]
        assert 0 <= effectiveness_data["completion_rate"] <= 100
        assert performance_data["total"] >= len(performance_data["courses"])
        assert all(0 <= row["completion_rate"] <= 100 for row in performance_data["courses"])
        assert risk_data["total"] >= risk_data["open"]
        assert risk_data["overdue"] <= risk_data["open"] <= risk_data["total"]
        assert risk_data["risk_band"] in {"low", "medium", "high"}
