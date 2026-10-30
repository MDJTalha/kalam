"""Guard public inquiry validation and internal queue tenant isolation."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routes.marketing import InquiryCreate, create_inquiry, review_scope
from app.core.config import settings


class TenantLookup:
    def __init__(self, slug):
        self.slug = slug

    async def scalar(self, _query):
        return SimpleNamespace(slug=self.slug, status="active") if self.slug else None


def test_inquiry_requires_explicit_consent_and_valid_work_email():
    base = {"name": "Ada Example", "organization": "Acme", "work_email": "ada@acme.com"}
    with pytest.raises(ValidationError):
        InquiryCreate(**base, consent=False)
    with pytest.raises(ValidationError):
        InquiryCreate(**{**base, "work_email": "invalid"}, consent=True)
    payload = InquiryCreate(**base, consent=True, country_code="pk", country_name="Pakistan",
                            primary_objective="Skills & capability management")
    assert payload.organization == "Acme"
    assert payload.country_code == "PK"
    assert payload.primary_objective == "Skills & capability management"
    with pytest.raises(ValidationError):
        InquiryCreate(**{**base, "work_email": "ada@gmail.com"}, consent=True)


@pytest.mark.asyncio
async def test_review_queue_is_restricted_to_configured_tenant(monkeypatch):
    user = SimpleNamespace(tenant_id="internal-id")
    monkeypatch.setattr(settings, "marketing_inbox_enabled", False)
    monkeypatch.setattr(settings, "marketing_review_tenant_slug", "kognivon-ops")
    with pytest.raises(HTTPException) as off:
        await review_scope(user, TenantLookup("kognivon-ops"))
    assert off.value.status_code == 404

    monkeypatch.setattr(settings, "marketing_inbox_enabled", True)
    with pytest.raises(HTTPException) as foreign:
        await review_scope(user, TenantLookup("customer"))
    assert foreign.value.status_code == 403
    await review_scope(user, TenantLookup("kognivon-ops"))


@pytest.mark.asyncio
async def test_intake_rejects_missing_review_tenant(monkeypatch):
    monkeypatch.setattr(settings, "marketing_inbox_enabled", True)
    monkeypatch.setattr(settings, "marketing_review_tenant_slug", "missing-ops")
    payload = InquiryCreate(name="Ada Example", work_email="ada@example.com",
                            organization="Acme", consent=True)
    with pytest.raises(HTTPException) as missing:
        await create_inquiry(payload, TenantLookup(None))
    assert missing.value.status_code == 503
