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
from app.services.webhook_secrets import (
    WebhookSecretConfigurationError,
    encrypt_webhook_secret,
)

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
            "secret_configured": item.secret_encrypted is not None,
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
    try:
        encrypted_secret, key_id = encrypt_webhook_secret(raw_secret)
    except WebhookSecretConfigurationError:
        raise HTTPException(
            status_code=503,
            detail="Webhook secret encryption is not configured",
        ) from None

    endpoint = WebhookEndpoint(
        tenant_id=user.tenant_id,
        url=str(payload.url),
        secret_encrypted=encrypted_secret,
        secret_key_id=key_id,
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
        "secret_warning": "Store this secret securely; it is shown only once.",
    }


@router.post("/{webhook_id}/rotate-secret", status_code=200)
async def rotate_webhook_secret(
    webhook_id: UUID,
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

    raw_secret = secrets.token_urlsafe(36)
    try:
        encrypted_secret, key_id = encrypt_webhook_secret(raw_secret)
    except WebhookSecretConfigurationError:
        raise HTTPException(
            status_code=503,
            detail="Webhook secret encryption is not configured",
        ) from None

    endpoint.secret_encrypted = encrypted_secret
    endpoint.secret_key_id = key_id
    endpoint.active = True
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="webhook.secret_rotated",
        entity_type="webhook_endpoint",
        entity_id=str(endpoint.id),
        metadata={"key_id": key_id},
    )
    await db.commit()
    return {
        "id": str(endpoint.id),
        "active": endpoint.active,
        "secret": raw_secret,
        "secret_warning": "Store this secret securely; it is shown only once.",
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
    if active and endpoint.secret_encrypted is None:
        raise HTTPException(
            status_code=409,
            detail="Webhook secret must be rotated before the endpoint can be activated",
        )

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
