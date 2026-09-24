from __future__ import annotations

from pathlib import Path
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
                if total > settings.max_upload_mb * 1024 * 1024:
                    path.unlink(missing_ok=True)
                    raise ValueError("File exceeds configured upload limit")
                handle.write(chunk)
        return object_key, total

    def open(self, object_key: str):
        return self.path_for(object_key).open("rb")

    def delete(self, object_key: str) -> None:
        self.path_for(object_key).unlink(missing_ok=True)


def get_storage() -> LocalStorage:
    if settings.storage_backend != "local":
        raise RuntimeError("Only local quarantine storage is configured; configure an object-storage adapter before production use")
    return LocalStorage(settings.storage_root)
