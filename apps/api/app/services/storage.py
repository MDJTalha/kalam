from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config import settings


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, object_key: str) -> Path:
        path = (self.root / object_key).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid object key")
        return path

    async def save_upload(self, tenant_id: UUID, upload: UploadFile) -> tuple[str, int]:
        suffix = Path(upload.filename or "").suffix.lower()
        object_key = f"{tenant_id}/{uuid4().hex}{suffix}"
        path = self.path_for(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with path.open("wb") as handle:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > settings.upload_limit_bytes:
                    path.unlink(missing_ok=True)
                    raise ValueError("File exceeds configured upload limit")
                handle.write(chunk)
        return object_key, total

    def open(self, object_key: str):
        return self.path_for(object_key).open("rb")

    def exists(self, object_key: str) -> bool:
        return self.path_for(object_key).is_file()

    def finalize_upload(self, object_key: str, content_type: str) -> None:
        del object_key, content_type

    def iter_bytes(self, object_key: str) -> Iterator[bytes]:
        with self.open(object_key) as handle:
            while chunk := handle.read(1024 * 1024):
                yield chunk

    def delete(self, object_key: str) -> None:
        self.path_for(object_key).unlink(missing_ok=True)


class S3Storage(LocalStorage):
    """S3-compatible object storage with local quarantine staging for malware scans."""

    def __init__(self, root: str):
        super().__init__(root)
        try:
            boto3 = import_module("boto3")
            config_module = import_module("botocore.config")
        except ImportError as exc:
            raise RuntimeError("S3 storage requires the API's boto3 dependency") from exc
        options = {
            "region_name": settings.s3_region,
            "endpoint_url": settings.s3_endpoint_url,
            "aws_access_key_id": settings.s3_access_key_id,
            "aws_secret_access_key": settings.s3_secret_access_key,
            "config": config_module.Config(s3={"addressing_style": "path"}),
        }
        self.client = boto3.client("s3", **options)
        self.bucket = settings.s3_bucket
        if not self.bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3")

    def finalize_upload(self, object_key: str, content_type: str) -> None:
        path = self.path_for(object_key)
        self.client.upload_file(
            str(path), self.bucket, object_key,
            ExtraArgs={"ContentType": content_type},
        )
        path.unlink(missing_ok=True)

    def exists(self, object_key: str) -> bool:
        client_error = import_module("botocore.exceptions").ClientError
        self.path_for(object_key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except client_error as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise

    def iter_bytes(self, object_key: str) -> Iterator[bytes]:
        self.path_for(object_key)
        response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        body = response["Body"]
        try:
            while chunk := body.read(1024 * 1024):
                yield chunk
        finally:
            body.close()

    def delete(self, object_key: str) -> None:
        self.path_for(object_key)
        super().delete(object_key)
        self.client.delete_object(Bucket=self.bucket, Key=object_key)


@lru_cache(maxsize=1)
def get_storage() -> LocalStorage | S3Storage:
    if settings.storage_backend.lower() == "s3":
        return S3Storage(settings.storage_root)
    return LocalStorage(settings.storage_root)


def download_headers(filename: str) -> dict[str, str]:
    encoded = quote(filename, safe="")
    return {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"}
