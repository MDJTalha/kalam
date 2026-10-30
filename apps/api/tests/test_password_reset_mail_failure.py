from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.routes import auth


class _Result:
    def __init__(self, user):
        self.user = user

    def scalar_one_or_none(self):
        return self.user


class _FakeSession:
    def __init__(self, user):
        self.user = user
        self.committed = False
        self.rollback_calls = 0
        self.added = []

    async def execute(self, _statement):
        return _Result(self.user)

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rollback_calls += 1


@pytest.mark.asyncio
async def test_password_reset_token_is_committed_before_mail_delivery(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        email="person@example.com",
    )
    db = _FakeSession(user)

    async def fake_audit(*_args, **_kwargs):
        return None

    def failing_send_email(**_kwargs):
        assert db.committed, "reset token must be durable before mail delivery"
        raise RuntimeError("mail provider unavailable")

    monkeypatch.setattr(auth, "audit", fake_audit)
    monkeypatch.setattr(auth, "send_email", failing_send_email)

    result = await auth._request_password_reset(
        auth.ForgotPasswordRequest(
            tenant_slug="example-tenant",
            email="person@example.com",
        ),
        db,
    )

    assert result == {"status": "accepted"}
    assert db.committed is True
    assert db.rollback_calls == 0
    assert len(db.added) == 1
