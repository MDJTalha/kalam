import asyncio

from app.api.routes.ai import _generate, _lesson_text
from app.db.models import Lesson


def test_ai_provider_fails_closed_when_disabled():
    async def run():
        try:
            await _generate("test", "disabled", "http://127.0.0.1:11434", "")
        except Exception as exc:
            return getattr(exc, "status_code", None)
        return None

    assert asyncio.run(run()) == 503


def test_lesson_context_extraction_is_bounded_to_supported_fields():
    lesson = Lesson(title="Governance", content={"text": "Primary text", "body": "Body text"})
    rendered = _lesson_text(lesson)
    assert "Governance" in rendered
    assert "Primary text" in rendered
    assert "Body text" in rendered



def test_ai_registry_is_admin_only_and_persists_governance_contract(client=None):
    from fastapi.testclient import TestClient
    from app.main import app
    from uuid import uuid4

    with TestClient(app, base_url="http://localhost") as client:
        login_payload = {"tenant_slug": "demo-corporation", "email": "learner@demo.corp", "password": "DemoOnly!1234"}
        assert client.post("/api/v1/auth/login", json=login_payload).status_code == 200
        assert client.get("/api/v1/ai/admin/providers").status_code == 403
        assert client.get("/api/v1/ai/admin/policy").status_code == 403

        admin = {"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}
        assert client.post("/api/v1/auth/login", json=admin).status_code == 200
        token = uuid4().hex[:8]
        provider = client.post("/api/v1/ai/admin/providers", json={
            "name": f"Ollama Local {token}",
            "provider_type": "ollama",
            "endpoint_url": "http://127.0.0.1:11434",
            "secret_ref": "AI_TEST_TOKEN",
            "capabilities": {"chat": True, "grounding": True},
            "enabled": True,
        })
        assert provider.status_code == 200, provider.text
        provider_id = provider.json()["id"]
        provider_check = client.post(f"/api/v1/ai/admin/providers/{provider_id}/test")
        assert provider_check.status_code == 200, provider_check.text
        assert provider_check.json()["status"] == "passed"
        assert provider_check.json()["provider_status"] == "ready"
        model = client.post("/api/v1/ai/admin/models", json={
            "provider_id": provider_id,
            "model_key": f"test-model-{token}",
            "display_name": "Phase 7 test model",
            "capabilities": {"chat": True},
            "limits": {"max_context_tokens": 4096},
            "enabled": True,
        })
        assert model.status_code == 200, model.text
        prompt = client.post("/api/v1/ai/admin/prompts", json={
            "name": f"learner_qa_{token}",
            "purpose": "learner_qa",
            "version": 1,
            "system_template": "Answer only from authorized course context.",
            "variables": ["course_context", "question"],
            "status": "approved",
        })
        assert prompt.status_code == 200, prompt.text
        policy = client.put("/api/v1/ai/admin/policy", json={
            "enabled": True,
            "require_grounding": True,
            "employment_decisioning_allowed": False,
            "raw_prompt_storage_allowed": False,
            "raw_response_storage_allowed": False,
            "max_input_chars": 4000,
            "max_output_tokens": 1200,
            "allowed_provider_types": ["ollama"],
        })
        assert policy.status_code == 200, policy.text
        status_response = client.get("/api/v1/ai/status")
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["configured"] is True
        assert status_payload["governance"]["authorized_content_only"] is True
        assert status_payload["governance"]["employment_decisioning"] is False
        assert client.get("/api/v1/ai/admin/providers").json()["providers"]
        assert client.get("/api/v1/ai/admin/models").json()["models"]
        assert client.get("/api/v1/ai/admin/prompts").json()["prompts"]
        disabled_policy = client.put("/api/v1/ai/admin/policy", json={
            "enabled": False,
            "require_grounding": True,
            "employment_decisioning_allowed": False,
            "raw_prompt_storage_allowed": False,
            "raw_response_storage_allowed": False,
            "max_input_chars": 4000,
            "max_output_tokens": 1200,
            "allowed_provider_types": ["ollama"],
        })
        assert disabled_policy.status_code == 200
        disabled_provider = client.patch(f"/api/v1/ai/admin/providers/{provider_id}", json={
            "name": provider.json()["name"],
            "provider_type": "ollama",
            "endpoint_url": "http://127.0.0.1:11434",
            "secret_ref": "AI_TEST_TOKEN",
            "capabilities": {"chat": True, "grounding": True},
            "enabled": False,
        })
        assert disabled_provider.status_code == 200


def test_ai_provider_validation_rejects_invalid_secret_reference(client=None):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app, base_url="http://localhost") as client:
        assert client.post("/api/v1/auth/login", json={"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}).status_code == 200
        response = client.post("/api/v1/ai/admin/providers", json={
            "name": "Invalid Secret Provider",
            "provider_type": "ollama",
            "endpoint_url": "http://127.0.0.1:11434",
            "secret_ref": "not a secret",
            "enabled": False,
        })
        assert response.status_code == 422



def test_ai_query_returns_citations_for_authorized_evidence(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.routes import ai as ai_route
    from uuid import uuid4

    captured = {}

    async def fake_generate(prompt, provider, base_url, model, max_output_tokens=1200, system_override=None, secret_ref=None):
        captured["prompt"] = prompt
        captured["provider"] = provider
        captured["model"] = model
        captured["limit"] = max_output_tokens
        return "Authorized answer [S1]"

    async def fake_capability_sources(user, db, top_k=8):
        from app.services.ai_retrieval import RetrievedSource
        return [
            RetrievedSource(
                citation_id="S1",
                lesson_id="skill-evidence",
                course_id="course-evidence",
                course_title="Leadership Essentials",
                lesson_title="Skill gap: Coaching",
                chunk_index=0,
                text="Current proficiency: 1. Required proficiency: 3. Gap: 2. Published learning option: Leadership Essentials.",
                score=2.0,
            )
        ]

    monkeypatch.setattr(ai_route, "_generate", fake_generate)
    monkeypatch.setattr(ai_route, "retrieve_capability_sources", fake_capability_sources)
    with TestClient(app, base_url="http://localhost") as client:
        admin = {"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}
        learner = {"tenant_slug": "demo-corporation", "email": "learner@demo.corp", "password": "DemoOnly!1234"}
        assert client.post("/api/v1/auth/login", json=admin).status_code == 200
        token = uuid4().hex[:8]
        provider = client.post("/api/v1/ai/admin/providers", json={
            "name": f"Retrieval Test {token}",
            "provider_type": "ollama",
            "endpoint_url": "http://127.0.0.1:11434",
            "enabled": True,
        })
        assert provider.status_code == 200, provider.text
        provider_id = provider.json()["id"]
        provider_check = client.post(f"/api/v1/ai/admin/providers/{provider_id}/test")
        assert provider_check.status_code == 200, provider_check.text
        assert provider_check.json()["status"] == "passed"
        assert provider_check.json()["provider_status"] == "ready"
        model = client.post("/api/v1/ai/admin/models", json={
            "provider_id": provider_id,
            "model_key": f"retrieval-test-{token}",
            "display_name": "Retrieval test model",
            "limits": {"max_output_tokens": 256},
            "enabled": True,
        })
        assert model.status_code == 200, model.text
        policy = client.put("/api/v1/ai/admin/policy", json={
            "enabled": True,
            "require_grounding": True,
            "employment_decisioning_allowed": False,
            "raw_prompt_storage_allowed": False,
            "raw_response_storage_allowed": False,
            "max_input_chars": 4000,
            "max_output_tokens": 1200,
            "allowed_provider_types": ["ollama"],
        })
        assert policy.status_code == 200
        content_assist = client.post(
            "/api/v1/ai/content-assist",
            json={
                "instruction": "Rewrite this draft for clarity while preserving the source meaning.",
                "draft_text": "This controlled author draft explains expected workplace conduct and ethical decision-making.",
                "mode": "rewrite",
            },
        )
        assert content_assist.status_code == 200, content_assist.text
        assert content_assist.json()["governance"]["human_review_required"] is True
        assert content_assist.json()["sources"][0]["citation_id"] == "S1"

        assert client.post("/api/v1/auth/login", json=learner).status_code == 200
        assert client.post(
            "/api/v1/ai/content-assist",
            json={
                "instruction": "Rewrite this draft.",
                "draft_text": "This draft is long enough for the governed content assistance validation path.",
                "mode": "rewrite",
            },
        ).status_code == 403
        response = client.post("/api/v1/ai/query", json={"question": "What is expected conduct?", "mode": "qa"})
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["sources"]
        assert payload["sources"][0]["citation_id"] == "S1"
        assert payload["governance"]["authorized_content_only"] is True
        assert payload["answer"] == "Authorized answer [S1]"
        assert "UNTRUSTED_REFERENCE_CONTENT" in captured["prompt"]
        assert "AUTHORIZED EVIDENCE:" in captured["prompt"]
        assert captured["limit"] == 256

        recommendation = client.post(
            "/api/v1/ai/query",
            json={"question": "What learning should I prioritize?", "mode": "recommendation"},
        )
        assert recommendation.status_code == 200, recommendation.text
        assert recommendation.json()["sources"][0]["lesson_title"] == "Skill gap: Coaching"

        skill_gap = client.post(
            "/api/v1/ai/query",
            json={"question": "Explain my current skill gap.", "mode": "skill_gap"},
        )
        assert skill_gap.status_code == 200, skill_gap.text
        assert skill_gap.json()["governance"]["employment_decisioning"] is False

        assert client.post("/api/v1/auth/login", json=admin).status_code == 200
        interactions = client.get("/api/v1/ai/admin/interactions")
        assert interactions.status_code == 200, interactions.text
        interaction = next(item for item in interactions.json()["interactions"] if item["id"] == payload["governance"]["interaction_id"])
        assert interaction["review"] is None
        review = client.put(
            f"/api/v1/ai/admin/interactions/{interaction['id']}/review",
            json={"decision": "approved", "notes": "Grounded response verified in Phase 7 regression."},
        )
        assert review.status_code == 200, review.text
        assert review.json()["decision"] == "approved"
        telemetry = client.get("/api/v1/ai/admin/telemetry")
        assert telemetry.status_code == 200, telemetry.text
        assert telemetry.json()["requests"] >= 1
        assert telemetry.json()["human_reviews"] >= 1

        assert client.patch(f"/api/v1/ai/admin/providers/{provider_id}", json={
            "name": provider.json()["name"],
            "provider_type": "ollama",
            "endpoint_url": "http://127.0.0.1:11434",
            "enabled": False,
        }).status_code == 200
        assert client.put("/api/v1/ai/admin/policy", json={
            "enabled": False,
            "require_grounding": True,
            "employment_decisioning_allowed": False,
            "raw_prompt_storage_allowed": False,
            "raw_response_storage_allowed": False,
            "max_input_chars": 4000,
            "max_output_tokens": 1200,
            "allowed_provider_types": ["ollama"],
        }).status_code == 200



def test_grounded_answer_gate_accepts_valid_and_rejects_invalid_citations():
    from app.services.ai_governance import validate_grounded_answer

    validate_grounded_answer("Evidence supports this [S1].", {"S1", "S2"})
    try:
        validate_grounded_answer("Evidence supports this.", {"S1"})
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 502
    else:
        raise AssertionError("Uncited AI output was not rejected.")

    try:
        validate_grounded_answer("Evidence [S9].", {"S1"})
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 502
    else:
        raise AssertionError("Invalid AI citation was not rejected.")

    try:
        validate_grounded_answer("Evidence [S4].", {"S1", "S2", "S3", "S4"}, {"S1", "S2", "S3"})
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 502
    else:
        raise AssertionError("Low-relevance AI citation was not rejected.")
