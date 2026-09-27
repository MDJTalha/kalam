from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import FileObject, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.file_scanner import FileScanError, scan_file
from app.services.storage import get_storage

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
}


@router.post("", status_code=201)
async def upload_file(
    upload: UploadFile = File(...),
    user: User = Depends(require_permission("files.manage")),
    db: AsyncSession = Depends(get_db),
):
    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    if not upload.filename:
        raise HTTPException(status_code=422, detail="Filename is required")

    storage = get_storage()
    try:
        object_key, size_bytes = await storage.save_upload(user.tenant_id, upload)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    path = storage.path_for(object_key)
    try:
        clean, scanner = await scan_file(path)
    except FileScanError as exc:
        storage.delete(object_key)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not clean:
        storage.delete(object_key)
        raise HTTPException(status_code=422, detail="File rejected by malware scanner")

    item = FileObject(
        tenant_id=user.tenant_id,
        uploaded_by=user.id,
        object_key=object_key,
        original_name=upload.filename[:255],
        mime_type=upload.content_type,
        size_bytes=size_bytes,
        status="available" if scanner != "not_configured" else "pending_scan",
        record_metadata={"scanner": scanner, "scan_result": "clean" if scanner != "not_configured" else "pending"},
    )
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="file.uploaded",
        entity_type="file",
        entity_id=str(item.id),
        metadata={"size_bytes": size_bytes, "status": item.status},
    )
    await db.commit()

    return {
        "id": str(item.id),
        "name": item.original_name,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "status": item.status,
    }


@router.get("")
async def list_files(
    user: User = Depends(require_permission("files.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FileObject)
        .where(FileObject.tenant_id == user.tenant_id)
        .order_by(FileObject.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": str(item.id),
            "name": item.original_name,
            "mime_type": item.mime_type,
            "size_bytes": item.size_bytes,
            "status": item.status,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    user: User = Depends(require_permission("files.read")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(FileObject).where(
            FileObject.id == file_id,
            FileObject.tenant_id == user.tenant_id,
            FileObject.status == "available",
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="File not found or not yet cleared")
    path = get_storage().path_for(item.object_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File content not found")
    return FileResponse(path=path, media_type=item.mime_type, filename=item.original_name)


@router.patch("/{file_id}/scan-result")
async def set_scan_result(
    file_id: UUID,
    clean: bool,
    user: User = Depends(require_permission("files.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(FileObject).where(
            FileObject.id == file_id,
            FileObject.tenant_id == user.tenant_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="File not found")

    item.status = "available" if clean else "rejected"
    item.record_metadata = {
        **item.record_metadata,
        "scanner": "privileged_workflow",
        "scan_result": "clean" if clean else "rejected",
    }
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="file.scan_result.updated",
        entity_type="file",
        entity_id=str(item.id),
        metadata={"clean": clean},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status}
