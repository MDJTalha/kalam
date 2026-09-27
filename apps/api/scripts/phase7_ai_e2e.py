from __future__ import annotations

# ruff: noqa: E402

import sys
from pathlib import Path
from uuid import uuid4

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient

from app.main import app

ADMIN = {"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"tenant_slug": "demo-corporation", "email": "learner@demo.corp", "password": "DemoOnly!1234"}
MODEL = "llama3.2:1b"


def main() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        provider_id = None
        model_id = None
        provider_name = None
        try:
            assert client.post("/api/v1/auth/login", json=ADMIN).status_code == 200
            token = uuid4().hex[:8]
            provider = client.post(
                "/api/v1/ai/admin/providers",
                json={
                    "name": f"Local Ollama E2E {token}",
                    "provider_type": "ollama",
                    "endpoint_url": "http://127.0.0.1:11434",
                    "enabled": True,
                },
            )
            assert provider.status_code == 200, provider.text
            provider_id = provider.json()["id"]
            provider_name = provider.json()["name"]

            check = client.post(f"/api/v1/ai/admin/providers/{provider_id}/test")
            assert check.status_code == 200, check.text

            existing_models = client.get("/api/v1/ai/admin/models")
            assert existing_models.status_code == 200, existing_models.text
            existing = next((item for item in existing_models.json()["models"] if item["model_key"] == MODEL), None)
            if existing:
                model_id = existing["id"]
                model = client.patch(
                    f"/api/v1/ai/admin/models/{model_id}",
                    json={
                        "provider_id": provider_id,
                        "model_key": MODEL,
                        "display_name": "Llama 3.2 1B",
                        "capabilities": {"chat": True},
                        "limits": {"max_output_tokens": 96},
                        "enabled": True,
                    },
                )
            else:
                model = client.post(
                    "/api/v1/ai/admin/models",
                    json={
                        "provider_id": provider_id,
                        "model_key": MODEL,
                        "display_name": "Llama 3.2 1B",
                        "capabilities": {"chat": True},
                        "limits": {"max_output_tokens": 96},
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
                    "max_output_tokens": 96,
                    "allowed_provider_types": ["ollama"],
                },
            )
            assert policy.status_code == 200, policy.text

            assert client.post("/api/v1/auth/login", json=LEARNER).status_code == 200
            response = client.post(
                "/api/v1/ai/query",
                json={"question": "What is the expected conduct principle in my enrolled ethics course?", "mode": "qa"},
            )
            print("AI_E2E_HTTP_STATUS=", response.status_code)
            if response.status_code == 200:
                payload = response.json()
                print("AI_E2E_GROUNDING=accepted")
                print("AI_E2E_SOURCES=", len(payload["sources"]))
                print("AI_E2E_ANSWER=", payload["answer"][:1000])
                assert payload["sources"]
                assert payload["governance"]["grounded"] is True
                assert payload["governance"]["authorized_content_only"] is True
                assert payload["answer"].strip()
            else:
                payload = response.json()
                print("AI_E2E_GROUNDING=blocked")
                print("AI_E2E_DETAIL=", payload.get("detail"))
                assert response.status_code == 502
                assert "uncited" in str(payload.get("detail", "")).lower() or "citation" in str(payload.get("detail", "")).lower()
        finally:
            assert client.post("/api/v1/auth/login", json=ADMIN).status_code == 200
            if model_id and provider_id:
                client.patch(
                    f"/api/v1/ai/admin/models/{model_id}",
                    json={
                        "provider_id": provider_id,
                        "model_key": MODEL,
                        "display_name": "Llama 3.2 1B",
                        "capabilities": {"chat": True},
                        "limits": {"max_output_tokens": 96},
                        "enabled": False,
                    },
                )
            if provider_id and provider_name:
                client.patch(
                    f"/api/v1/ai/admin/providers/{provider_id}",
                    json={
                        "name": provider_name,
                        "provider_type": "ollama",
                        "endpoint_url": "http://127.0.0.1:11434",
                        "enabled": False,
                    },
                )
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


if __name__ == "__main__":
    main()
