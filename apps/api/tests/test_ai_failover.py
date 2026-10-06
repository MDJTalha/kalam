import asyncio
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.api.routes import ai as ai_route
from app.db.models import AIModel, AIProvider
from app.db.session import SessionLocal
from app.main import app
from app.services.ai_retrieval import RetrievedSource


async def _mark_ready(provider_ids: list[UUID]) -> None:
    async with SessionLocal() as db:
        rows = (
            await db.scalars(select(AIProvider).where(AIProvider.id.in_(provider_ids)))
        ).all()
        for row in rows:
            row.status = "ready"
            row.last_check_status = "passed"
        await db.commit()


async def _cleanup(provider_ids: list[UUID]) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(AIModel).where(AIModel.provider_id.in_(provider_ids)))
        await db.execute(delete(AIProvider).where(AIProvider.id.in_(provider_ids)))
        await db.commit()


def test_governed_query_fails_over_to_next_ready_provider(monkeypatch):
    token = uuid4().hex[:8]
    calls: list[str] = []

    async def fake_sources(user, db, question, course_id=None, top_k=8, max_context_chars=18000):
        return [
            RetrievedSource(
                citation_id="S1",
                lesson_id="lesson-failover",
                course_id="course-failover",
                course_title="Failover Evidence",
                lesson_title="Governed fallback",
                chunk_index=0,
                text="This controlled source verifies governed provider fallback.",
                score=4.0,
            )
        ]

    async def fake_generate(prompt, provider, base_url, model, **kwargs):
        calls.append(model)
        if len(calls) == 1:
            raise HTTPException(status_code=502, detail="Primary provider failed.")
        return "Fallback response grounded in evidence [S1]"

    monkeypatch.setattr(ai_route, "retrieve_authorized_sources", fake_sources)
    monkeypatch.setattr(ai_route, "_generate", fake_generate)

    provider_ids: list[UUID] = []
    with TestClient(app, base_url="http://localhost") as client:
        admin = {"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}
        learner = {"tenant_slug": "demo-corporation", "email": "learner@demo.corp", "password": "DemoOnly!1234"}
        assert client.post("/api/v1/auth/login", json=admin).status_code == 200
        for index, priority in enumerate((0, 1), start=1):
            provider = client.post(
                "/api/v1/ai/admin/providers",
                json={
                    "name": f"Failover {index} {token}",
                    "provider_type": "ollama",
                    "endpoint_url": "http://127.0.0.1:11434",
                    "priority": priority,
                    "enabled": True,
                },
            )
            assert provider.status_code == 200, provider.text
            provider_id = UUID(provider.json()["id"])
            provider_ids.append(provider_id)
            asyncio.run(_mark_ready([provider_id]))
            model = client.post(
                "/api/v1/ai/admin/models",
                json={
                    "provider_id": str(provider_id),
                    "model_key": f"failover-model-{index}-{token}",
                    "display_name": f"Failover model {index}",
                    "limits": {"max_output_tokens": 256},
                    "enabled": True,
                },
            )
            assert model.status_code == 200, model.text
        policy = client.put(
            "/api/v1/ai/admin/policy",
            json={
                "enabled": True,
                "require_grounding": True,
                "employment_decisioning_allowed": False,
                "raw_prompt_storage_allowed": False,
                "raw_response_storage_allowed": False,
                "max_input_chars": 4000,
                "max_output_tokens": 1200,
                "allowed_provider_types": ["ollama"],
            },
        )
        assert policy.status_code == 200

        assert client.post("/api/v1/auth/login", json=learner).status_code == 200
        response = client.post(
            "/api/v1/ai/query",
            json={"question": "Explain governed fallback.", "mode": "qa"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert calls[:2] == [f"failover-model-1-{token}", f"failover-model-2-{token}"]
        assert payload["governance"]["fallback_used"] is True
        assert payload["governance"]["provider_priority"] == 1
        assert payload["answer"].endswith("[S1]")

        assert client.post("/api/v1/auth/login", json=admin).status_code == 200
        client.put(
            "/api/v1/ai/admin/policy",
            json={
                "enabled": False,
                "require_grounding": True,
                "employment_decisioning_allowed": False,
                "raw_prompt_storage_allowed": False,
                "raw_response_storage_allowed": False,
                "max_input_chars": 4000,
                "max_output_tokens": 1200,
                "allowed_provider_types": ["ollama"],
            },
        )

    asyncio.run(_cleanup(provider_ids))
