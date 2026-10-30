"""Regression tests for second-pass audit findings without database access."""

import asyncio
import socket
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.saas_commercial import _validate_trial_seats
from app.api.routes.saas_finance import _invoice_financials
from app.db.models import CRMInvoice
from app.services import integration_adapters
from app.services.ai_governance import validate_provider_config


def test_ai_secret_reference_is_provider_specific_and_not_arbitrary_env_lookup():
    with pytest.raises(HTTPException) as exc:
        validate_provider_config(
            "openai_compatible",
            "https://api.openai.com/v1",
            "DATABASE_URL",
            development=False,
        )
    assert exc.value.status_code == 422


def test_production_oidc_discovery_rejects_private_metadata_endpoint(monkeypatch):
    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "issuer": "https://issuer.example",
                "authorization_endpoint": "https://metadata-attacker.example/authorize",
                "token_endpoint": "https://issuer.example/token",
                "jwks_uri": "https://issuer.example/keys",
            }

    async def fake_get(*args, **kwargs):
        return Response()

    def resolve_private(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.9", port or 443))]

    monkeypatch.setattr(integration_adapters, "_get", fake_get)
    monkeypatch.setattr(integration_adapters.socket, "getaddrinfo", resolve_private)
    monkeypatch.setattr(integration_adapters.settings, "app_env", "production")
    monkeypatch.setattr(integration_adapters.settings, "integration_allow_private_urls", False)

    with pytest.raises(integration_adapters.IntegrationCheckError):
        asyncio.run(
            integration_adapters.get_oidc_discovery(
                {"discovery_url": "https://issuer.example/.well-known/openid-configuration"}
            )
        )


def test_invoice_financial_read_model_does_not_mutate_invoice():
    invoice = CRMInvoice(
        id=uuid4(),
        ops_tenant_id=uuid4(),
        total_minor=1000,
        due_at=None,
        status="issued",
        paid_at=None,
    )

    class ReadOnlyDb:
        async def scalar(self, statement):
            return 250

    result = asyncio.run(_invoice_financials(ReadOnlyDb(), invoice))

    assert result["paid_minor"] == 250
    assert result["outstanding_minor"] == 750
    assert result["status"] == "partially_paid"
    assert invoice.status == "issued"
    assert invoice.paid_at is None


def test_xml_handshake_rejects_dtd_and_entity_expansion():
    malicious = (
        b'<!DOCTYPE EntityDescriptor [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        b'<EntityDescriptor>&xxe;</EntityDescriptor>'
    )
    with pytest.raises(integration_adapters.IntegrationCheckError, match="unsafe XML"):
        integration_adapters._xml_root(malicious, "EntityDescriptor")


def test_trial_seat_validation_rejects_null_seats():
    plan = SimpleNamespace(minimum_seats=1, maximum_seats=10)
    with pytest.raises(HTTPException) as exc:
        _validate_trial_seats(plan, None)
    assert exc.value.status_code == 422
