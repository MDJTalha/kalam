from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
import smtplib
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin

import httpx

from app.core.config import settings

SUPPORTED = {
    "hris", "oidc", "saml", "email", "calendar",
    "lti", "xapi", "scorm", "cmi5",
}

SENSITIVE_KEYS = {
    "password", "secret", "token", "client_secret",
    "private_key", "access_token", "refresh_token",
}


class IntegrationCheckError(ValueError):
    pass


def _validate_config(provider: str, config: dict) -> None:
    if provider not in SUPPORTED:
        raise IntegrationCheckError("Unsupported integration provider")
    for key in config:
        normalized = key.lower().replace("-", "_")
        if normalized.endswith("_env"):
            continue
        if normalized in SENSITIVE_KEYS or any(item in normalized for item in SENSITIVE_KEYS):
            raise IntegrationCheckError(
                f"Sensitive integration value '{key}' must use an environment reference"
            )
    if provider == "oidc" and config.get("login_enabled") is True:
        if not (config.get("issuer") or config.get("discovery_url")):
            raise IntegrationCheckError("OIDC login requires issuer or discovery_url")
        if not str(config.get("client_id") or "").strip():
            raise IntegrationCheckError("OIDC login requires client_id")
        if not str(config.get("client_secret_env") or "").strip():
            raise IntegrationCheckError("OIDC login requires client_secret_env")
    if provider == "saml" and config.get("login_enabled") is True:
        if not str(config.get("metadata_url") or "").strip():
            raise IntegrationCheckError("SAML login requires metadata_url")
        if not str(config.get("entity_id") or "").strip():
            raise IntegrationCheckError("SAML login requires entity_id")


def _url_allowed(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise IntegrationCheckError("Handshake URL must use http or https")
    if settings.app_env != "development" and parsed.scheme != "https":
        raise IntegrationCheckError("Production integration handshakes require HTTPS")
    if settings.integration_allow_private_urls:
        return
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise IntegrationCheckError("Handshake host could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise IntegrationCheckError("Private or local handshake targets are blocked")


async def _get(url: str, headers: dict[str, str] | None, timeout: float) -> httpx.Response:
    _url_allowed(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        return await client.get(url, headers=headers or {})
def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_root(body: bytes, expected: str) -> None:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise IntegrationCheckError("Handshake returned invalid XML") from exc
    if _local_name(root.tag) != expected:
        raise IntegrationCheckError(f"Expected XML root {expected}")


def _env_value(config: dict, key: str) -> str | None:
    env_name = config.get(key)
    if not isinstance(env_name, str) or not env_name.strip():
        return None
    return os.getenv(env_name.strip())


async def _smtp_check(config: dict) -> str:
    host = str(config.get("host") or settings.smtp_host or "").strip()
    if not host:
        raise IntegrationCheckError("SMTP host is not configured")
    port = int(config.get("port") or settings.smtp_port)
    username = config.get("username") or settings.smtp_username
    password = _env_value(config, "password_env") or settings.smtp_password
    starttls = bool(config.get("starttls", settings.smtp_starttls))
    ssl_mode = bool(config.get("ssl", settings.smtp_ssl))

    def check() -> None:
        client = smtplib.SMTP_SSL(host, port, timeout=settings.smtp_timeout_seconds) if ssl_mode else smtplib.SMTP(host, port, timeout=settings.smtp_timeout_seconds)
        with client:
            client.ehlo()
            if starttls and not ssl_mode:
                client.starttls()
                client.ehlo()
            if username:
                if not password:
                    raise IntegrationCheckError("SMTP password must be supplied through password_env or deployment settings")
                client.login(str(username), str(password))
        return None
    await asyncio.to_thread(check)
    return f"SMTP connection authenticated successfully against {host}:{port}"


def _basic_headers(config: dict) -> dict[str, str]:
    headers = {"Accept": "application/json, application/xml, text/plain"}
    token = _env_value(config, "token_env")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def get_oidc_discovery(config: dict, timeout: float = 10.0) -> dict:
    discovery_url = str(config.get("discovery_url") or "").strip()
    issuer = str(config.get("issuer") or "").strip()
    if not discovery_url:
        if not issuer:
            raise IntegrationCheckError("OIDC issuer or discovery_url is required")
        discovery_url = urljoin(issuer.rstrip("/") + "/", ".well-known/openid-configuration")
    response = await _get(discovery_url, {"Accept": "application/json"}, timeout)
    if response.status_code >= 400:
        raise IntegrationCheckError(f"Discovery endpoint returned HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise IntegrationCheckError("Discovery endpoint did not return JSON") from exc
    required = {"issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"}
    missing = sorted(required - set(data))
    if missing:
        raise IntegrationCheckError("Discovery document is missing: " + ", ".join(missing))
    if issuer and str(data.get("issuer") or "").rstrip("/") != issuer.rstrip("/"):
        raise IntegrationCheckError("OIDC discovery issuer does not match configured issuer")
    return data


async def _oidc_check(config: dict, required: set[str], timeout: float) -> str:
    data = await get_oidc_discovery(config, timeout)
    missing = sorted(required - set(data))
    if missing:
        raise IntegrationCheckError("Discovery document is missing: " + ", ".join(missing))
    return f"OIDC discovery verified: {data.get('issuer')}"
async def _http_check(config: dict, timeout: float) -> str:
    url = str(config.get("health_url") or "").strip()
    if not url:
        raise IntegrationCheckError("health_url is required")
    response = await _get(url, _basic_headers(config), timeout)
    if response.status_code >= 400:
        raise IntegrationCheckError(f"Health endpoint returned HTTP {response.status_code}")
    return f"HTTP health check verified with HTTP {response.status_code}"


async def _xapi_check(config: dict, timeout: float) -> str:
    endpoint = str(config.get("endpoint") or "").rstrip("/")
    if not endpoint:
        raise IntegrationCheckError("xAPI endpoint is required")
    url = endpoint + "/about"
    headers = _basic_headers(config)
    username = str(config.get("username") or "").strip()
    password = _env_value(config, "password_env")
    auth = (username, password) if username and password else None
    _url_allowed(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.get(url, headers=headers, auth=auth)
    if response.status_code >= 400:
        raise IntegrationCheckError(f"xAPI /about returned HTTP {response.status_code}")
    return f"xAPI /about verified with HTTP {response.status_code}"


async def _manifest_check(config: dict, expected_root: str, timeout: float) -> str:
    url = str(config.get("manifest_url") or "").strip()
    if not url:
        raise IntegrationCheckError("manifest_url is required")
    response = await _get(url, {"Accept": "application/xml,text/xml"}, timeout)
    if response.status_code >= 400:
        raise IntegrationCheckError(f"Manifest returned HTTP {response.status_code}")
    _xml_root(response.content, expected_root)
    return f"{expected_root} manifest verified"
async def run_integration_check(provider: str, config: dict) -> dict[str, object]:
    _validate_config(provider, config)
    started = time.perf_counter()
    timeout = max(2.0, min(float(config.get("timeout_seconds") or 10), 30.0))
    if provider == "email":
        message = await _smtp_check(config)
    elif provider in {"oidc", "lti"}:
        required = {"issuer", "authorization_endpoint", "jwks_uri"}
        message = await _oidc_check(config, required, timeout)
    elif provider == "saml":
        url = str(config.get("metadata_url") or "").strip()
        if not url:
            raise IntegrationCheckError("metadata_url is required")
        response = await _get(url, {"Accept": "application/xml,text/xml"}, timeout)
        if response.status_code >= 400:
            raise IntegrationCheckError(f"SAML metadata returned HTTP {response.status_code}")
        _xml_root(response.content, "EntityDescriptor")
        message = "SAML metadata verified"
    elif provider == "xapi":
        message = await _xapi_check(config, timeout)
    elif provider in {"scorm", "cmi5"}:
        message = await _manifest_check(config, "manifest" if provider == "scorm" else "courseStructure", timeout)
    else:
        message = await _http_check(config, timeout)
    elapsed = int((time.perf_counter() - started) * 1000)
    return {"ok": True, "status": "connected", "message": message, "latency_ms": elapsed, "provider": provider}


def validate_integration_config(provider: str, config: dict) -> None:
    _validate_config(provider, config)


__all__ = [
    "IntegrationCheckError",
    "SUPPORTED",
    "run_integration_check",
    "validate_integration_config",
    "get_oidc_discovery",
]