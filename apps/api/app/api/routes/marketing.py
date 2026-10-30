"""Public inquiry intake and a tenant-restricted Kalam review queue."""

import re
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, user_has_permission
from app.core.config import settings
from app.db.models import MarketingInquiry, Tenant, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com",
    "outlook.com", "live.com", "msn.com", "icloud.com", "me.com", "aol.com",
    "proton.me", "protonmail.com", "gmx.com", "mail.com", "yandex.com", "zoho.com",
}


class InquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    work_email: EmailStr
    organization: str = Field(min_length=2, max_length=200)
    job_title: str | None = Field(default=None, max_length=160)
    message: str | None = Field(default=None, max_length=1200)
    request_type: Literal["demo", "sales", "trial"] = "demo"
    plan_code: str | None = Field(default=None, max_length=80)
    source: str = Field(default="website", max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    country_name: str | None = Field(default=None, max_length=120)
    organization_size: str | None = Field(default=None, max_length=60)
    business_phone: str | None = Field(default=None, max_length=80)
    primary_objective: str | None = Field(default=None, max_length=180)
    evaluation_timeline: str | None = Field(default=None, max_length=80)
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=160)
    landing_path: str | None = Field(default=None, max_length=300)
    consent: Literal[True]
    website: str = Field(default="", max_length=200)  # Honeypot; leave empty.

    @field_validator("work_email")
    @classmethod
    def require_official_work_email(cls, value: EmailStr) -> EmailStr:
        domain = str(value).rsplit("@", 1)[-1].lower()
        if domain in PERSONAL_EMAIL_DOMAINS:
            raise ValueError("Please use your official organization email address.")
        return value

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("business_phone")
    @classmethod
    def validate_business_phone(cls, value: str | None) -> str | None:
        if not value:
            return value
        normalized = re.sub(r"[\s().-]", "", value)
        if not re.fullmatch(r"\+[1-9]\d{6,14}", normalized):
            raise ValueError("Business phone must be a valid international number.")
        return normalized

    @field_validator(
        "name", "organization", "job_title", "message", "country_name",
        "organization_size", "business_phone", "primary_objective",
        "evaluation_timeline", "utm_source", "utm_medium", "utm_campaign",
        "landing_path", mode="before",
    )
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
        request_type=payload.request_type,
        plan_code=payload.plan_code.lower() if payload.plan_code else None,
        source=payload.source,
        country_code=payload.country_code,
        country_name=payload.country_name or None,
        organization_size=payload.organization_size or None,
        business_phone=payload.business_phone or None,
        primary_objective=payload.primary_objective or None,
        evaluation_timeline=payload.evaluation_timeline or None,
        utm_source=payload.utm_source or None,
        utm_medium=payload.utm_medium or None,
        utm_campaign=payload.utm_campaign or None,
        landing_path=payload.landing_path or None,
        consent_at=datetime.now(UTC),
    )
    db.add(inquiry)
    await db.commit()
    return {"id": str(inquiry.id), "status": "received"}


async def _is_demo_crm_user(user: User, db: AsyncSession) -> bool:
    if not settings.saas_demo_crm_enabled:
        return False
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    return bool(
        tenant is not None
        and tenant.slug == settings.saas_demo_tenant_slug
        and tenant.status == "active"
        and user.email.lower() == settings.saas_demo_admin_email.lower()
    )


async def review_scope(user: User, db: AsyncSession) -> None:
    if not settings.marketing_inbox_enabled or not settings.marketing_review_tenant_slug:
        raise HTTPException(status_code=404, detail="Queue unavailable")
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is not None and tenant.slug == settings.marketing_review_tenant_slug and tenant.status == "active":
        return
    if await _is_demo_crm_user(user, db):
        return
    raise HTTPException(status_code=403, detail="Review access restricted")




async def require_marketing_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not (
        await user_has_permission(user, db, "tenant.manage")
        or await user_has_permission(user, db, "saas.crm.read")
        or await user_has_permission(user, db, "saas.crm.manage")
    ):
        raise HTTPException(status_code=403, detail="Review access restricted")
    return user


async def require_marketing_manage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not (
        await user_has_permission(user, db, "tenant.manage")
        or await user_has_permission(user, db, "saas.crm.manage")
    ):
        raise HTTPException(status_code=403, detail="Review access restricted")
    return user

@router.get("/inquiries")
async def list_inquiries(
    user: User = Depends(require_marketing_read),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
):
    await review_scope(user, db)
    if await _is_demo_crm_user(user, db):
        return []
    result = await db.execute(select(MarketingInquiry).order_by(MarketingInquiry.created_at.desc()).limit(limit))
    return [
        {
            "id": str(item.id), "name": item.name, "work_email": item.work_email,
            "organization": item.organization, "job_title": item.job_title,
            "message": item.message, "request_type": item.request_type,
            "plan_code": item.plan_code, "source": item.source,
            "country_code": item.country_code, "country_name": item.country_name,
            "organization_size": item.organization_size, "business_phone": item.business_phone,
            "primary_objective": item.primary_objective, "evaluation_timeline": item.evaluation_timeline,
            "utm_source": item.utm_source, "utm_medium": item.utm_medium,
            "utm_campaign": item.utm_campaign, "landing_path": item.landing_path,
            "status": item.status, "created_at": item.created_at,
            "crm_account_id": str(item.crm_account_id) if item.crm_account_id else None,
            "converted_at": item.converted_at,
        }
        for item in result.scalars().all()
    ]


@router.patch("/inquiries/{inquiry_id}")
async def update_inquiry(
    inquiry_id: UUID,
    payload: InquiryUpdate,
    user: User = Depends(require_marketing_manage),
    db: AsyncSession = Depends(get_db),
):
    await review_scope(user, db)
    if await _is_demo_crm_user(user, db):
        raise HTTPException(status_code=403, detail="Demo CRM cannot modify the production marketing inbox")
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
