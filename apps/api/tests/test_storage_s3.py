from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from app.services import storage


class _FakeClient:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def upload_file(self, filename: str, bucket: str, key: str, ExtraArgs: dict) -> None:
        assert ExtraArgs["ContentType"] == "application/pdf"
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def head_object(self, Bucket: str, Key: str) -> dict:
        if (Bucket, Key) not in self.objects:
            raise _FakeClientError(404)
        return {}

    def get_object(self, Bucket: str, Key: str) -> dict:
        return {"Body": _FakeBody(self.objects[(Bucket, Key)])}

    def delete_object(self, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)


class _FakeBody:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def read(self, size: int) -> bytes:
        result, self.value = self.value[:size], self.value[size:]
        return result

    def close(self) -> None:
        pass


class _FakeClientError(Exception):
    def __init__(self, status: int) -> None:
        self.response = {"ResponseMetadata": {"HTTPStatusCode": status}}


@pytest.fixture
def fake_s3(monkeypatch: pytest.MonkeyPatch) -> _FakeClient:
    client = _FakeClient()
    boto3 = ModuleType("boto3")
    boto3.client = lambda *_args, **_kwargs: client  # type: ignore[attr-defined]
    botocore = ModuleType("botocore")
    config = ModuleType("botocore.config")
    config.Config = lambda **_kwargs: object()  # type: ignore[attr-defined]
    exceptions = ModuleType("botocore.exceptions")
    exceptions.ClientError = _FakeClientError  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setitem(sys.modules, "botocore", botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", config)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", exceptions)
    monkeypatch.setattr(storage.settings, "s3_bucket", "private-test-bucket")
    monkeypatch.setattr(storage.settings, "s3_region", "us-east-1")
    monkeypatch.setattr(storage.settings, "s3_endpoint_url", None)
    monkeypatch.setattr(storage.settings, "s3_access_key_id", None)
    monkeypatch.setattr(storage.settings, "s3_secret_access_key", None)
    return client


def test_s3_storage_stages_then_uploads_and_streams(tmp_path: Path, fake_s3: _FakeClient) -> None:
    backend = storage.S3Storage(str(tmp_path))
    key = "tenant-id/object-id.pdf"
    staged = backend.path_for(key)
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"scanned-content")

    backend.finalize_upload(key, "application/pdf")

    assert not staged.exists()
    assert backend.exists(key)
    assert b"".join(backend.iter_bytes(key)) == b"scanned-content"
    backend.delete(key)
    assert not backend.exists(key)


def test_s3_storage_rejects_path_traversal(tmp_path: Path, fake_s3: _FakeClient) -> None:
    backend = storage.S3Storage(str(tmp_path))
    with pytest.raises(ValueError, match="Invalid object key"):
        backend.exists("../outside")
