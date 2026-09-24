from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import Integration, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

SUPPORTED_PROVIDERS = {
    "hris",
    "oidc",
    "saml",
    "email",
    "calendar",
    "lti",
    "xapi",
    "scorm",
    "cmi5",
}


class IntegrationUpsert(BaseModel):
    provider: str = Field(min_length=2, max_length=80)
    status: str = Field(default="configured", pattern=r"^(configured|connected|disabled|error)$")
    config: dict = Field(default_factory=dict)


@router.get("")
async def list_integrations(
    user: User = Depends(require_permission("tenant.read")),
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

    item = await db.scalar(
        select(Integration).where(
            Integration.tenant_id == user.tenant_id,
            Integration.provider == provider,
        )
    )
    if item is None:
        item = Integration(tenant_id=user.tenant_id, provider=provider)
        db.add(item)

    item.status = payload.status
    item.config = payload.config
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="integration.updated",
        entity_type="integration",
        entity_id=str(item.id),
        metadata={"provider": provider, "status": payload.status},
    )
    await db.commit()
    return {"id": str(item.id), "provider": item.provider, "status": item.status, "config": item.config}


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
