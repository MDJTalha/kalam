import pytest
from fastapi import HTTPException

from app.api.routes.ai import _generate


@pytest.mark.asyncio
async def test_generate_rejects_unimplemented_provider_adapter():
    with pytest.raises(HTTPException) as exc:
        await _generate("Mode: qa", "anthropic", "https://example.test", "model")
    assert exc.value.status_code == 503


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
