import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes import files


class _Session:
    def __init__(self, item):
        self.item = item
        self.scalar_calls = 0

    async def scalar(self, _statement):
        self.scalar_calls += 1
        return self.item


def test_manual_scan_override_is_disabled_outside_development(monkeypatch):
    monkeypatch.setattr(files.settings, "app_env", "production")
    db = _Session(item=None)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            files.set_scan_result(
                file_id=uuid4(),
                clean=True,
                user=SimpleNamespace(id=uuid4(), tenant_id=uuid4()),
                db=db,
            )
        )

    assert raised.value.status_code == 409
    assert db.scalar_calls == 0


def test_manual_scan_override_cannot_reclassify_a_non_pending_file(monkeypatch):
    monkeypatch.setattr(files.settings, "app_env", "development")
    db = _Session(item=SimpleNamespace(status="rejected"))

    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            files.set_scan_result(
                file_id=uuid4(),
                clean=True,
                user=SimpleNamespace(id=uuid4(), tenant_id=uuid4()),
                db=db,
            )
        )

    assert raised.value.status_code == 409
    assert db.scalar_calls == 1
