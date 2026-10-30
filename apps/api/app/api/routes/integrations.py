from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import Integration, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.integration_adapters import (
    SUPPORTED,
    IntegrationCheckError,
    run_integration_check,
    validate_integration_config,
)

router = APIRouter()

SUPPORTED_PROVIDERS = set(SUPPORTED)


class IntegrationUpsert(BaseModel):
    provider: str = Field(min_length=2, max_length=80)
    config: dict = Field(default_factory=dict)


@router.get("")
async def list_integrations(
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration)
        .where(Integration.tenant_id == user.tenant_id)
        .order_by(Integration.provider)
    )
    return [
        {
            "id": str(item.id),
            "provider": item.provider,
            "status": item.status,
            "config": item.config,
            "last_checked_at": item.last_checked_at,
            "last_check_status": item.last_check_status,
            "last_check_message": item.last_check_message,
        }
        for item in result.scalars().all()
    ]


@router.put("/{provider}")
async def upsert_integration(
    provider: str,
    payload: IntegrationUpsert,
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    if provider not in SUPPORTED_PROVIDERS or payload.provider != provider:
        raise HTTPException(status_code=422, detail="Unsupported integration provider")
    try:
        validate_integration_config(provider, payload.config)
    except IntegrationCheckError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    item = await db.scalar(
        select(Integration).where(
            Integration.tenant_id == user.tenant_id,
            Integration.provider == provider,
        )
    )
    if item is None:
        item = Integration(tenant_id=user.tenant_id, provider=provider)
        db.add(item)

    # Configuration submitted by a caller is never proof of a successful handshake.
    item.status = "configured"
    item.config = payload.config
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="integration.updated",
        entity_type="integration",
        entity_id=str(item.id),
        metadata={"provider": provider, "status": item.status},
    )
    await db.commit()
    return {
        "id": str(item.id),
        "provider": item.provider,
        "status": item.status,
        "config": item.config,
        "last_checked_at": item.last_checked_at,
        "last_check_status": item.last_check_status,
        "last_check_message": item.last_check_message,
    }


@router.post("/{provider}/test")
async def test_connection(
    provider: str,
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=422, detail="Unsupported integration provider")
    item = await db.scalar(
        select(Integration).where(
            Integration.tenant_id == user.tenant_id,
            Integration.provider == provider,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Integration not configured")
    item.last_checked_at = datetime.now(UTC)
    try:
        result = await run_integration_check(provider, item.config or {})
    except IntegrationCheckError as exc:
        item.status = "error"
        item.last_check_status = "failed"
        item.last_check_message = str(exc)
        await audit(
            db,
            tenant_id=user.tenant_id,
            actor_id=user.id,
            action="integration.tested",
            entity_type="integration",
            entity_id=str(item.id),
            metadata={"provider": provider, "status": "failed"},
        )
        await db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception as exc:
        item.status = "error"
        item.last_check_status = "failed"
        item.last_check_message = "Connection test failed"
        await db.commit()
        raise HTTPException(status_code=502, detail="Connection test failed") from exc

    item.status = "connected"
    item.last_check_status = "passed"
    item.last_check_message = str(result["message"])
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="integration.tested",
        entity_type="integration",
        entity_id=str(item.id),
        metadata={
            "provider": provider,
            "status": "passed",
            "latency_ms": result["latency_ms"],
        },
    )
    await db.commit()
    return result | {"integration_id": str(item.id)}


@router.post("/{provider}/disable")
async def disable_integration(
    provider: str,
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Integration).where(
            Integration.tenant_id == user.tenant_id,
            Integration.provider == provider,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Integration not configured")
    item.status = "disabled"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="integration.disabled",
        entity_type="integration",
        entity_id=str(item.id),
        metadata={"provider": provider},
    )
    await db.commit()
    return {"provider": provider, "status": "disabled"}
