import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.integration_adapters import (
    IntegrationCheckError,
    _validate_smtp_destination,
    run_integration_check,
    validate_integration_config,
)

TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": os.environ["CI_FIXTURE_PASSWORD"]}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("/.well-known/openid-configuration"):
            body = json.dumps({
                "issuer": f"http://127.0.0.1:{self.server.server_port}",
                "authorization_endpoint": "http://127.0.0.1/auth",
                "token_endpoint": "http://127.0.0.1/token",
                "jwks_uri": "http://127.0.0.1/jwks",
            }).encode()
            content_type = "application/json"
        elif self.path == "/health":
            body = b"ok"
            content_type = "text/plain"
        elif self.path == "/.well-known/openid-configuration":
            body = json.dumps({
                "issuer": f"http://127.0.0.1:{self.server.server_port}",
                "authorization_endpoint": "http://127.0.0.1/auth",
                "token_endpoint": "http://127.0.0.1/token",
                "jwks_uri": "http://127.0.0.1/jwks",
            }).encode()
            content_type = "application/json"
        elif self.path == "/saml-metadata":
            body = b'<EntityDescriptor entityID="local"><IDPSSODescriptor/></EntityDescriptor>'
            content_type = "application/xml"
        elif self.path == "/xapi/about":
            body = b'{"version":["1.0.3"]}'
            content_type = "application/json"
        elif self.path == "/scorm/imsmanifest.xml":
            body = b'<manifest identifier="LOCAL-SCORM"><organizations/></manifest>'
            content_type = "application/xml"
        elif self.path == "/cmi5.xml":
            body = b'<courseStructure identifier="LOCAL-CMI5" xmlns="https://w3id.org/xapi/profiles/cmi5/v1/course"><course/></courseStructure>'
            content_type = "application/xml"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
@pytest.mark.parametrize(
    ("provider", "config_builder"),
    [
        ("hris", lambda base: {"health_url": base + "/health"}),
        ("calendar", lambda base: {"health_url": base + "/health"}),
        ("oidc", lambda base: {"issuer": base}),
        ("lti", lambda base: {"issuer": base}),
        ("saml", lambda base: {"metadata_url": base + "/saml-metadata"}),
        ("xapi", lambda base: {"endpoint": base + "/xapi"}),
        ("scorm", lambda base: {"manifest_url": base + "/scorm/imsmanifest.xml"}),
        ("cmi5", lambda base: {"manifest_url": base + "/cmi5.xml"}),
    ],
)
def test_provider_handshakes_are_protocol_checked(provider, config_builder, local_server):
    result = asyncio.run(run_integration_check(provider, config_builder(local_server)))
    assert result["ok"] is True
    assert result["status"] == "connected"
    assert result["latency_ms"] >= 0


def test_integration_config_rejects_secrets_in_tenant_metadata():
    with pytest.raises(IntegrationCheckError, match="environment reference"):
        asyncio.run(run_integration_check("hris", {"health_url": "http://127.0.0.1:1", "password": "plain-text"}))


def test_oidc_login_config_accepts_environment_secret_reference():
    validate_integration_config("oidc", {
        "issuer": "https://idp.example.com",
        "client_id": "kognivon",
        "client_secret_env": "KOGNIVON_OIDC_CLIENT_SECRET",
        "login_enabled": True,
    })


def test_oidc_login_config_requires_environment_secret_reference():
    with pytest.raises(IntegrationCheckError, match="client_secret_env"):
        validate_integration_config("oidc", {
            "issuer": "https://idp.example.com",
            "client_id": "kognivon",
            "login_enabled": True,
        })


def test_integration_secret_reference_cannot_read_application_secrets():
    with pytest.raises(IntegrationCheckError, match="KALAM_INTEGRATION"):
        validate_integration_config("hris", {
            "health_url": "https://hris.example.com/health",
            "token_env": "DATABASE_URL",
        })

    with pytest.raises(IntegrationCheckError, match="KALAM_INTEGRATION"):
        validate_integration_config("oidc", {
            "issuer": "https://idp.example.com",
            "client_id": "kalam",
            "client_secret_env": "AWS_SECRET_ACCESS_KEY",
            "login_enabled": True,
        })


def test_integration_secret_reference_accepts_namespaced_secret():
    validate_integration_config("hris", {
        "health_url": "https://hris.example.com/health",
        "token_env": "KALAM_INTEGRATION_HRIS_ACCESS_TOKEN",
    })


def test_smtp_integration_does_not_send_platform_credentials_to_tenant_host(monkeypatch):
    import smtplib

    login_calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def ehlo(self):
            return None

        def starttls(self):
            return None

        def login(self, username, password):
            login_calls.append((username, password))

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "integration_allow_private_urls", True)
    monkeypatch.setattr(settings, "smtp_host", "trusted-mail.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "platform-user")
    monkeypatch.setattr(settings, "smtp_password", "platform-secret")
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_ssl", False)

    result = asyncio.run(run_integration_check("email", {
        "host": "tenant-controlled.example.com",
        "port": 587,
    }))

    assert result["ok"] is True
    assert login_calls == []


def test_smtp_destination_rejects_link_local_metadata_address(monkeypatch):
    import socket

    def resolve_metadata(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "integration_allow_private_urls", False)
    monkeypatch.setattr(socket, "getaddrinfo", resolve_metadata)

    with pytest.raises(IntegrationCheckError, match="Private or local SMTP"):
        _validate_smtp_destination("smtp.attacker.example", 587)


def test_integration_route_persists_connection_check_evidence(local_server):
    settings.integration_allow_private_urls = True
    with TestClient(app, base_url="http://localhost") as client:
        login = client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **ADMIN})
        assert login.status_code == 200, login.text
        saved = client.put(
            "/api/v1/integrations/hris",
            json={
                "provider": "hris",
                "status": "configured",
                "config": {"health_url": local_server + "/health"},
            },
        )
        assert saved.status_code == 200, saved.text
        checked = client.post("/api/v1/integrations/hris/test")
        assert checked.status_code == 200, checked.text
        payload = checked.json()
        assert payload["status"] == "connected"
        listed = client.get("/api/v1/integrations")
        row = next(item for item in listed.json() if item["provider"] == "hris")
        assert row["last_check_status"] == "passed"
        assert row["last_check_message"]