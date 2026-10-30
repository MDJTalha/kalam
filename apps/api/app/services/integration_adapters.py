from __future__ import annotations

import asyncio
import ipaddress
import os
import re
import smtplib
import socket
import time
from urllib.parse import urljoin, urlparse

import httpx
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from app.core.config import settings

SUPPORTED = {
    "hris", "oidc", "saml", "email", "calendar",
    "lti", "xapi", "scorm", "cmi5",
}

SENSITIVE_KEYS = {
    "password", "secret", "token", "client_secret",
    "private_key", "access_token", "refresh_token",
}
SECRET_ENV_NAME_PATTERN = re.compile(
    r"^KALAM_INTEGRATION_[A-Z0-9_]+_(?:PASSWORD|TOKEN|CLIENT_SECRET|API_KEY|ACCESS_TOKEN|REFRESH_TOKEN|SECRET)$"
)
LEGACY_SECRET_ENV_REFS = {
    ("oidc", "client_secret_env", "KOGNIVON_OIDC_CLIENT_SECRET"),
}


class IntegrationCheckError(ValueError):
    pass


def validate_secret_environment_reference(
    env_name: str,
    *,
    provider: str,
    key: str,
) -> str:
    """Allow only explicitly namespaced integration secrets, never arbitrary app env vars."""
    name = env_name.strip()
    if not name:
        raise IntegrationCheckError(f"{key} must name a configured integration secret")
    if (provider, key, name) in LEGACY_SECRET_ENV_REFS:
        return name
    if not SECRET_ENV_NAME_PATTERN.fullmatch(name):
        raise IntegrationCheckError(
            f"{key} must reference a KALAM_INTEGRATION_* secret variable; "
            "application and infrastructure environment variables cannot be referenced"
        )
    return name


def _validate_config(provider: str, config: dict) -> None:
    if provider not in SUPPORTED:
        raise IntegrationCheckError("Unsupported integration provider")
    for key, value in config.items():
        normalized = key.lower().replace("-", "_")
        if normalized.endswith("_env"):
            if value is not None and value != "":
                if not isinstance(value, str):
                    raise IntegrationCheckError(f"{key} must be a secret environment-variable name")
                validate_secret_environment_reference(value, provider=provider, key=key)
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
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise IntegrationCheckError("Handshake URL must use http or https")
    if settings.app_env in {"test", "ci"} and parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        # Test-only loopback endpoints support isolated protocol fixtures. This exception
        # is unavailable in development/production and does not permit arbitrary private hosts.
        return
    if settings.app_env != "development" and parsed.scheme != "https":
        raise IntegrationCheckError("Production integration handshakes require HTTPS")
    if settings.integration_allow_private_urls:
        return
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise IntegrationCheckError("Handshake host could not be resolved") from exc
    if not addresses:
        raise IntegrationCheckError("Handshake host did not resolve to an address")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast or ip.is_unspecified:
            raise IntegrationCheckError("Private or local handshake targets are blocked")


async def _get(url: str, headers: dict[str, str] | None, timeout: float) -> httpx.Response:
    _url_allowed(url)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        proxy=settings.outbound_http_proxy,
    ) as client:
        return await client.get(url, headers=headers or {})
def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_root(body: bytes, expected: str) -> None:
    try:
        root = ET.fromstring(body)
    except (ET.ParseError, DefusedXmlException) as exc:
        raise IntegrationCheckError("Handshake returned invalid or unsafe XML") from exc
    if _local_name(root.tag) != expected:
        raise IntegrationCheckError(f"Expected XML root {expected}")


def _env_value(config: dict, key: str) -> str | None:
    env_name = config.get(key)
    if not isinstance(env_name, str) or not env_name.strip():
        return None
    return os.getenv(env_name.strip())


def _validate_smtp_destination(host: str, port: int) -> None:
    if not host or any(character.isspace() for character in host):
        raise IntegrationCheckError("SMTP host is invalid")
    if port < 1 or port > 65535:
        raise IntegrationCheckError("SMTP port is invalid")
    if settings.app_env.strip().lower() in {"production", "prod"} and port not in {465, 587}:
        raise IntegrationCheckError("Production SMTP integrations must use port 465 or 587")

    test_loopback = settings.app_env.strip().lower() in {"test", "ci"} and host.lower() in {
        "localhost", "127.0.0.1", "::1"
    }
    if settings.integration_allow_private_urls or test_loopback:
        return

    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        }
    except (socket.gaierror, UnicodeError) as exc:
        raise IntegrationCheckError("SMTP host could not be resolved") from exc
    if not addresses:
        raise IntegrationCheckError("SMTP host did not resolve to an address")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise IntegrationCheckError("SMTP host resolved to an invalid IP address") from exc
        if not ip.is_global or ip.is_multicast or ip.is_unspecified:
            raise IntegrationCheckError("Private or local SMTP targets are blocked")


async def _smtp_check(config: dict) -> str:
    host = str(config.get("host") or settings.smtp_host or "").strip()
    if not host:
        raise IntegrationCheckError("SMTP host is not configured")
    port = int(config.get("port") or settings.smtp_port)
    _validate_smtp_destination(host, port)
    # Never send platform-wide SMTP credentials to a host supplied by an
    # integration record. Deployment credentials are used only for the exact
    # deployment-configured SMTP endpoint.
    configured_smtp_host = settings.smtp_host
    uses_platform_smtp = (
        configured_smtp_host is not None
        and host.casefold() == configured_smtp_host.strip().casefold()
        and port == settings.smtp_port
    )
    username = config.get("username")
    password = _env_value(config, "password_env")
    if uses_platform_smtp:
        username = username or settings.smtp_username
        password = password or settings.smtp_password
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
    for endpoint_name in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        endpoint = data.get(endpoint_name)
        if not isinstance(endpoint, str):
            raise IntegrationCheckError(f"OIDC discovery has an invalid {endpoint_name}")
        _url_allowed(endpoint)
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
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        proxy=settings.outbound_http_proxy,
    ) as client:
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
    "SUPPORTED",
    "IntegrationCheckError",
    "get_oidc_discovery",
    "run_integration_check",
    "validate_integration_config",
    "validate_secret_environment_reference",
]
