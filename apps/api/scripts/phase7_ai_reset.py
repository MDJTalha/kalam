from __future__ import annotations

# ruff: noqa: E402

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient

from app.main import app

ADMIN = {"tenant_slug": "demo-corporation", "email": "admin@demo.corp", "password": "DemoOnly!1234"}


with TestClient(app, base_url="http://localhost") as client:
    assert client.post("/api/v1/auth/login", json=ADMIN).status_code == 200
    providers = client.get("/api/v1/ai/admin/providers").json()["providers"]
    for provider in providers:
        if provider["enabled"] and provider["name"].startswith(("Local Ollama E2E", "Retrieval Test", "Ollama Local")):
            client.patch(
                f"/api/v1/ai/admin/providers/{provider['id']}",
                json={
                    "name": provider["name"],
                    "provider_type": provider["provider_type"],
                    "endpoint_url": provider["endpoint_url"],
                    "enabled": False,
                },
            )
    models = client.get("/api/v1/ai/admin/models").json()["models"]
    for model in models:
        if model["enabled"]:
            client.patch(
                f"/api/v1/ai/admin/models/{model['id']}",
                json={
                    "provider_id": model["provider_id"],
                    "model_key": model["model_key"],
                    "display_name": model["display_name"],
                    "capabilities": model["capabilities"],
                    "limits": model["limits"],
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
    print("AI_REGISTRY_RESET=passed")
