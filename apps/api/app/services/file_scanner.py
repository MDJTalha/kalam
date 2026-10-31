from __future__ import annotations

import asyncio
import socket
import struct
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings


class FileScanError(RuntimeError):
    """Raised when the configured malware scanner cannot be reached."""


_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "application/zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
    ),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
    ),
}


def validate_file_content_type(path: Path, mime_type: str) -> None:
    """Reject common content-type spoofing before malware scanning.

    Plain text/CSV intentionally have no fixed magic number and are validated
    by their declared MIME type plus the malware scan pipeline.
    """
    signatures = _SIGNATURES.get(mime_type)
    if not signatures:
        return
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        raise FileScanError("Uploaded file could not be read for content validation") from exc
    if not any(header.startswith(signature) for signature in signatures):
        raise HTTPException(status_code=415, detail="Uploaded file content does not match its declared type.")


def _scan_clamd(path: Path) -> bool:
    try:
        with socket.create_connection(
            (settings.file_scan_host, settings.file_scan_port),
            timeout=settings.file_scan_timeout_seconds,
        ) as client:
            client.sendall(b"zINSTREAM\0")
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    client.sendall(struct.pack("!I", len(chunk)))
                    client.sendall(chunk)
                client.sendall(struct.pack("!I", 0))
            response = client.recv(4096).decode("utf-8", errors="replace").strip()
    except (OSError, TimeoutError) as exc:
        raise FileScanError("Malware scanner is unavailable") from exc
    normalized = response.rstrip("\x00").strip()
    if normalized.endswith("OK"):
        return True
    if "FOUND" in normalized:
        return False
    raise FileScanError(f"Unexpected malware scanner response: {response}")


async def scan_file(path: Path) -> tuple[bool, str]:
    provider = settings.file_scan_provider.lower().strip()
    if provider in {"", "none"}:
        return True, "not_configured"
    if provider == "clamd":
        clean = await asyncio.to_thread(_scan_clamd, path)
        return clean, "clamd"
    raise FileScanError(f"Unsupported file scan provider: {provider}")
