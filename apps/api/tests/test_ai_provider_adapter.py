import pytest
from fastapi import HTTPException

from app.api.routes.ai import AIContentAssistRequest, AIQueryRequest, _generate, governed_ai_query, governed_content_assist
from app.services.ai_governance import validate_model_activation, validate_provider_activation


@pytest.mark.asyncio
async def test_generate_rejects_unimplemented_provider_adapter():
    with pytest.raises(HTTPException) as exc:
        await _generate("Mode: qa", "azure_openai", "https://example.test", "model")
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_anthropic_requires_secret_reference(monkeypatch):
    monkeypatch.delenv("TEST_ANTHROPIC_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        await _generate(
            "Mode: qa",
            "anthropic",
            "https://example.test",
            "model",
            secret_ref="TEST_ANTHROPIC_KEY",
        )
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_user_facing_ai_routes_fail_closed_when_deployment_ai_is_disabled(monkeypatch):
    monkeypatch.setattr("app.api.routes.ai.settings.ai_enabled", False)

    with pytest.raises(HTTPException) as query_exc:
        await governed_ai_query(AIQueryRequest(question="Explain the policy."), user=None, db=None)
    with pytest.raises(HTTPException) as assist_exc:
        await governed_content_assist(
            AIContentAssistRequest(instruction="Rewrite this safely.", draft_text="A sufficiently long draft for the governed content assistant."),
            user=None,
            db=None,
        )

    assert query_exc.value.status_code == 503
    assert assist_exc.value.status_code == 503


def test_provider_and_model_activation_require_ready_provider():
    with pytest.raises(HTTPException) as provider_exc:
        validate_provider_activation(True, "configured")
    with pytest.raises(HTTPException) as model_exc:
        validate_model_activation(True, False, "ready")
    with pytest.raises(HTTPException) as untested_model_exc:
        validate_model_activation(True, True, "configured")

    assert provider_exc.value.status_code == 409
    assert model_exc.value.status_code == 409
    assert untested_model_exc.value.status_code == 409
    validate_provider_activation(True, "ready")
    validate_model_activation(True, True, "ready")


@pytest.mark.asyncio
async def test_openai_compatible_requires_secret_reference(monkeypatch):
    monkeypatch.delenv("TEST_AI_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        await _generate(
            "Mode: qa",
            "openai_compatible",
            "https://example.test",
            "model",
            secret_ref="TEST_AI_KEY",
        )
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_openai_compatible_contract_and_usage_mapping(monkeypatch):
    monkeypatch.setenv("TEST_AI_KEY", "test-secret")
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "Grounded adapter response [S1]"}}],
                "usage": {"prompt_tokens": 42, "completion_tokens": 17},
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setattr("app.api.routes.ai.httpx.AsyncClient", FakeClient)
    result = await _generate(
        "Mode: qa\nUser question/request: Explain policy.\nAUTHORIZED EVIDENCE:\n[S1] Policy evidence",
        "openai_compatible",
        "https://provider.example",
        "enterprise-model",
        max_output_tokens=256,
        secret_ref="TEST_AI_KEY",
    )
    assert result.answer == "Grounded adapter response [S1]"
    assert result.input_tokens == 42
    assert result.output_tokens == 17
    assert captured["url"] == "https://provider.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-secret"
    assert captured["json"]["model"] == "enterprise-model"
    assert captured["json"]["max_tokens"] == 256


@pytest.mark.asyncio
async def test_official_openai_uses_current_chat_completions_contract(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-secret")
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "Grounded response [S1]"}}],
                "usage": {"prompt_tokens": 21, "completion_tokens": 9},
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setattr("app.api.routes.ai.httpx.AsyncClient", FakeClient)
    result = await _generate(
        "Mode: qa\nAUTHORIZED EVIDENCE:\n[S1] Lesson excerpt",
        "openai_compatible",
        "https://api.openai.com/v1",
        "gpt-6-luna",
        max_output_tokens=384,
        secret_ref="OPENAI_API_KEY",
    )

    assert result.answer == "Grounded response [S1]"
    assert result.input_tokens == 21
    assert result.output_tokens == 9
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-openai-secret"
    assert captured["json"]["max_completion_tokens"] == 384
    assert "max_tokens" not in captured["json"]
    assert captured["json"]["messages"][0]["role"] == "developer"
