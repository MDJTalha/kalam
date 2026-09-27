import asyncio
import hashlib
import hmac
import json
import time
from uuid import uuid4

from app.services.webhook_delivery import deliver_webhook, retry_delay, verify_webhook_signature


def test_retry_delay_is_bounded():
    assert retry_delay(1).total_seconds() == 60
    assert retry_delay(8).total_seconds() == 3600
    assert retry_delay(20).total_seconds() == 3600


def test_webhook_delivery_signs_payload(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *, content, headers):
            captured["url"] = url
            captured["content"] = content
            captured["headers"] = headers
            return Response()

    monkeypatch.setattr("app.services.webhook_delivery.httpx.AsyncClient", lambda **kwargs: Client())

    event_id = uuid4()
    tenant_id = uuid4()
    payload = {"id": str(uuid4()), "type": "course.completed", "title": "Completed", "body": "Done"}
    asyncio.run(
        deliver_webhook(
            url="https://example.test/webhook",
            secret="test-secret",
            event_type="notification.created",
            event_id=event_id,
            tenant_id=tenant_id,
            payload=payload,
        )
    )

    body = captured["content"]
    timestamp = captured["headers"]["X-LMS-Timestamp"]
    expected = hmac.new(
        b"test-secret",
        timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    assert captured["url"] == "https://example.test/webhook"
    assert json.loads(body) == payload
    assert captured["headers"]["X-LMS-Signature"] == f"sha256={expected}"
    assert captured["headers"]["X-LMS-Event-Id"] == str(event_id)
    assert captured["headers"]["X-LMS-Tenant"] == str(tenant_id)

def test_webhook_contract_rejects_tampered_payload_and_timestamp():
    secret = "test-secret"
    timestamp = "1790000000"
    original = b'{"event":"course.completed","id":"123"}'
    signature = hmac.new(secret.encode(), timestamp.encode() + b"." + original, hashlib.sha256).hexdigest()

    def valid(body: bytes, ts: str) -> bool:
        expected = hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    assert valid(original, timestamp) is True
    assert valid(b'{"event":"course.completed","id":"999"}', timestamp) is False
    assert valid(original, "1790000001") is False


def test_webhook_signature_verifier_accepts_fresh_payload_and_rejects_replay():
    secret = "test-secret"
    body = b'{"event":"course.completed","id":"123"}'
    timestamp = str(int(time.time()))
    signature = "sha256=" + hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(secret=secret, timestamp=timestamp, body=body, signature=signature) is True
    assert verify_webhook_signature(secret=secret, timestamp=str(int(timestamp) - 301), body=body, signature=signature) is False
    assert verify_webhook_signature(secret=secret, timestamp=timestamp, body=body + b"!", signature=signature) is False
