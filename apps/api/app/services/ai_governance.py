from __future__ import annotations

import os
import re
from urllib.parse import urlparse

from fastapi import HTTPException, status

ALLOWED_PROVIDER_TYPES = {"ollama", "openai_compatible", "azure_openai", "anthropic", "custom"}
SECRET_REF_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


def validate_provider_config(provider_type: str, endpoint_url: str | None, secret_ref: str | None, *, development: bool) -> None:
    normalized = provider_type.strip().lower()
    if normalized not in ALLOWED_PROVIDER_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported AI provider type.")
    if secret_ref and not SECRET_REF_PATTERN.fullmatch(secret_ref):
        raise HTTPException(status_code=422, detail="secret_ref must be an environment-variable style reference.")
    expected_secret = {
        "openai_compatible": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(normalized)
    if secret_ref and secret_ref != expected_secret:
        raise HTTPException(status_code=422, detail="Use only the fixed provider-specific credential reference.")
    if endpoint_url:
        parsed = urlparse(endpoint_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise HTTPException(status_code=422, detail="AI provider endpoint must be a valid HTTP(S) URL.")
        test_loopback_http = (
            os.getenv("APP_ENV", "").strip().lower() in {"test", "ci"}
            and parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        )
        if not development and parsed.scheme != "https" and not test_loopback_http:
            raise HTTPException(status_code=422, detail="AI provider endpoints must use HTTPS outside development.")
    if normalized != "ollama" and not endpoint_url:
        raise HTTPException(status_code=422, detail="endpoint_url is required for this AI provider type.")


def validate_policy(max_input_chars: int, max_output_tokens: int, provider_types: list[str], daily_token_budget: int = 0) -> None:
    if not 100 <= max_input_chars <= 20000:
        raise HTTPException(status_code=422, detail="max_input_chars must be between 100 and 20000.")
    if not 64 <= max_output_tokens <= 8192:
        raise HTTPException(status_code=422, detail="max_output_tokens must be between 64 and 8192.")
    if not 0 <= daily_token_budget <= 100_000_000:
        raise HTTPException(status_code=422, detail="daily_token_budget must be between 0 and 100000000.")
    invalid = sorted(set(provider_types) - ALLOWED_PROVIDER_TYPES)
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported provider types: {', '.join(invalid)}")


def validate_provider_activation(enabled: bool, provider_status: str) -> None:
    if enabled and provider_status != "ready":
        raise HTTPException(status_code=409, detail="Run and pass the provider connection test before enabling this provider.")


def validate_model_activation(enabled: bool, provider_enabled: bool, provider_status: str) -> None:
    if enabled and (not provider_enabled or provider_status != "ready"):
        raise HTTPException(status_code=409, detail="Enable a provider only after its connection test has passed before enabling a model.")


def validate_prompt_template(system_template: str, variables: list[str]) -> None:
    if not system_template.strip() or len(system_template) > 20000:
        raise HTTPException(status_code=422, detail="system_template must contain 1-20000 characters.")
    if len(variables) > 32 or any(not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", item) for item in variables):
        raise HTTPException(status_code=422, detail="Prompt variables must use safe identifier names and be limited to 32 entries.")


def public_provider(provider) -> dict:
    return {
        "id": str(provider.id),
        "name": provider.name,
        "provider_type": provider.provider_type,
        "endpoint_url": provider.endpoint_url,
        "secret_ref_configured": bool(provider.secret_ref),
        "status": provider.status,
        "capabilities": provider.capabilities,
        "priority": provider.priority,
        "enabled": provider.enabled,
        "last_checked_at": provider.last_checked_at.isoformat() if provider.last_checked_at else None,
        "last_check_status": provider.last_check_status,
        "last_check_message": provider.last_check_message,
    }


def public_model(model) -> dict:
    return {
        "id": str(model.id),
        "provider_id": str(model.provider_id),
        "model_key": model.model_key,
        "display_name": model.display_name,
        "capabilities": model.capabilities,
        "limits": model.limits,
        "enabled": model.enabled,
    }


def public_prompt(prompt) -> dict:
    return {
        "id": str(prompt.id),
        "name": prompt.name,
        "purpose": prompt.purpose,
        "version": prompt.version,
        "variables": prompt.variables,
        "status": prompt.status,
        "created_by": str(prompt.created_by) if prompt.created_by else None,
    }



def validate_grounded_answer(answer: str, citation_ids: set[str], preferred_citation_ids: set[str] | None = None) -> None:
    citations = set(re.findall(r"\[(S\d+)\]", answer))
    if not citations:
        raise HTTPException(status_code=502, detail="AI provider returned an uncited response; grounded evidence is required.")
    invalid = citations - citation_ids
    if invalid:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid evidence citation.")
    if preferred_citation_ids and not (citations & preferred_citation_ids):
        raise HTTPException(status_code=502, detail="AI provider cited evidence outside the highest-relevance retrieved sources.")
