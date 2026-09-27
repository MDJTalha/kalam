from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta
from time import time
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.security import utcnow


def _signature(secret: str, timestamp: str, body: bytes) -> str:
    message = timestamp.encode("utf-8") + b"." + body
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


async def deliver_webhook(*, url: str, secret: str, event_type: str, event_id: UUID, tenant_id: UUID, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
    timestamp = str(int(utcnow().timestamp()))
    signature = _signature(secret, timestamp, body)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Corporate-LMS-Webhook/1.0",
        "X-LMS-Event": event_type,
        "X-LMS-Event-Id": str(event_id),
        "X-LMS-Timestamp": timestamp,
        "X-LMS-Signature": f"sha256={signature}",
        "X-LMS-Tenant": str(tenant_id),
    }
    timeout = max(1, settings.webhook_delivery_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.post(url, content=body, headers=headers)
        response.raise_for_status()


def verify_webhook_signature(*, secret: str, timestamp: str, body: bytes, signature: str, tolerance_seconds: int = 300) -> bool:
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(int(time()) - sent_at) > tolerance_seconds:
        return False
    expected = "sha256=" + _signature(secret, timestamp, body)
    return hmac.compare_digest(expected, signature)


def retry_delay(attempts: int) -> timedelta:
    return timedelta(minutes=min(60, 2 ** max(0, attempts - 1)))
