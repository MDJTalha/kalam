import hashlib
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import User, WebhookEndpoint
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


class WebhookCreate(BaseModel):
    url: AnyHttpUrl
    event_types: list[str] = Field(min_length=1, max_length=50)


@router.get("")
async def list_webhooks(
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.tenant_id == user.tenant_id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "url": item.url,
            "event_types": item.event_types,
            "active": item.active,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.post("", status_code=201)
async def create_webhook(
    payload: WebhookCreate,
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    raw_secret = secrets.token_urlsafe(36)
    endpoint = WebhookEndpoint(
        tenant_id=user.tenant_id,
        url=str(payload.url),
        secret_hash=hashlib.sha256(raw_secret.encode("utf-8")).hexdigest(),
        event_types=payload.event_types,
        active=True,
    )
    db.add(endpoint)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="webhook.created",
        entity_type="webhook_endpoint",
        entity_id=str(endpoint.id),
        metadata={"event_types": payload.event_types},
    )
    await db.commit()
    return {
        "id": str(endpoint.id),
        "url": endpoint.url,
        "event_types": endpoint.event_types,
        "active": endpoint.active,
        "secret": raw_secret,
        "secret_warning": "Store this secret securely; it cannot be recovered later.",
    }


@router.patch("/{webhook_id}")
async def toggle_webhook(
    webhook_id: UUID,
    active: bool,
    user: User = Depends(require_permission("integrations.manage")),
    db: AsyncSession = Depends(get_db),
):
    endpoint = await db.scalar(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.tenant_id == user.tenant_id,
        )
    )
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")

    endpoint.active = active
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="webhook.updated",
        entity_type="webhook_endpoint",
        entity_id=str(endpoint.id),
        metadata={"active": active},
    )
    await db.commit()
    return {"id": str(endpoint.id), "active": endpoint.active}
