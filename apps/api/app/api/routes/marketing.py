"""Public inquiry intake and a tenant-restricted Kognivon review queue."""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.config import settings
from app.db.models import MarketingInquiry, Tenant, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


class InquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    work_email: EmailStr
    organization: str = Field(min_length=2, max_length=200)
    job_title: str | None = Field(default=None, max_length=160)
    message: str | None = Field(default=None, max_length=1200)
    consent: Literal[True]
    website: str = Field(default="", max_length=200)  # Honeypot; leave empty.

    @field_validator("name", "organization", "job_title", "message", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class InquiryUpdate(BaseModel):
    status: Literal["new", "contacted", "closed"]


async def limit_inquiry(email: str) -> None:
    key = sha256(email.lower().encode("utf-8")).hexdigest()
    redis = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
    try:
        pipeline = redis.pipeline()
        pipeline.incr(f"marketing:email:{key}")
        pipeline.expire(f"marketing:email:{key}", 3600, nx=True)
        pipeline.incr("marketing:total:day")
        pipeline.expire("marketing:total:day", 86400, nx=True)
        results = await pipeline.execute()
        if int(results[0]) > 3 or int(results[2]) > 500:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Requests are temporarily unavailable.") from exc
    finally:
        await redis.aclose()


@router.post("/inquiries", status_code=201)
async def create_inquiry(payload: InquiryCreate, db: AsyncSession = Depends(get_db)):
    if not settings.marketing_inbox_enabled or not settings.marketing_review_tenant_slug:
        raise HTTPException(status_code=503, detail="Inquiries are not configured.")
    review_tenant = await db.scalar(select(Tenant).where(
        Tenant.slug == settings.marketing_review_tenant_slug, Tenant.status == "active"
    ))
    if review_tenant is None:
        raise HTTPException(status_code=503, detail="Inquiries are not configured.")
    if payload.website:
        return {"status": "received"}
    await limit_inquiry(str(payload.work_email))
    inquiry = MarketingInquiry(
        name=payload.name,
        work_email=str(payload.work_email).lower(),
        organization=payload.organization,
        job_title=payload.job_title or None,
        message=payload.message or None,
        consent_at=datetime.now(timezone.utc),
    )
    db.add(inquiry)
    await db.commit()
    return {"id": str(inquiry.id), "status": "received"}


async def review_scope(user: User, db: AsyncSession) -> None:
    if not settings.marketing_inbox_enabled or not settings.marketing_review_tenant_slug:
        raise HTTPException(status_code=404, detail="Queue unavailable")
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None or tenant.slug != settings.marketing_review_tenant_slug or tenant.status != "active":
        raise HTTPException(status_code=403, detail="Review access restricted")


@router.get("/inquiries")
async def list_inquiries(
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
):
    await review_scope(user, db)
    result = await db.execute(select(MarketingInquiry).order_by(MarketingInquiry.created_at.desc()).limit(limit))
    return [
        {
            "id": str(item.id), "name": item.name, "work_email": item.work_email,
            "organization": item.organization, "job_title": item.job_title,
            "message": item.message, "status": item.status, "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.patch("/inquiries/{inquiry_id}")
async def update_inquiry(
    inquiry_id: UUID,
    payload: InquiryUpdate,
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
):
    await review_scope(user, db)
    inquiry = await db.get(MarketingInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    previous_status = inquiry.status
    inquiry.status = payload.status
    inquiry.reviewed_by = user.id
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="marketing.inquiry.status_changed", entity_type="marketing_inquiry",
                entity_id=str(inquiry.id), metadata={"from": previous_status, "to": payload.status})
    await db.commit()
    return {"id": str(inquiry.id), "status": inquiry.status}
