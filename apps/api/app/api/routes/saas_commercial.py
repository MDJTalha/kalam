from __future__ import annotations

from datetime import datetime, timedelta, timezone
import csv
import io
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import is_platform_developer, require_permission
from app.core.config import settings
from app.db.models import (
    CRMAccount,
    CRMContact,
    CRMContract,
    CRMInvoice,
    CRMOnboardingItem,
    CRMPayment,
    CRMOpportunity,
    CRMSalesActivity,
    CRMSubscription,
    CRMTask,
    CRMTrial,
    MarketingInquiry,
    SaaSCertification,
    SessionRecord,
    SaaSOffer,
    SaaSPlan,
    Tenant,
    Role,
    RolePermission,
    Permission,
    User,
    UserRole,
)
from app.db.session import get_db
from app.services.audit import audit
from app.services.saas_renewals import reconcile_renewal_tasks

router = APIRouter()

PREDEFINED_TENANT_ROLES = {
    "Tenant Owner": ["tenant.read","reports.read","audit.read"],
    "Tenant Administrator": ["tenant.read","tenant.manage","users.read","users.manage","reports.read","audit.read","integrations.manage"],
    "HR / People Administrator": ["users.read","users.manage","reports.read","compliance.manage"],
    "L&D Administrator": ["courses.read","courses.manage","learning.access","assessments.manage","certificates.manage","reports.read","skills.manage","development.manage","users.read"],
    "Manager": ["users.read","courses.read","learning.access","reports.read","development.manage"],
    "Instructor": ["courses.read","learning.access","assessments.manage"],
    "Learner / Employee": ["courses.read","learning.access","development.manage"],
}

async def _ensure_tenant_roles(db: AsyncSession, tenant_id: UUID) -> None:
    permission_rows = list((await db.execute(
        select(Permission).where(Permission.key.in_(sorted({k for values in PREDEFINED_TENANT_ROLES.values() for k in values})))
    )).scalars().all())
    permissions = {item.key: item for item in permission_rows}
    for name, keys in PREDEFINED_TENANT_ROLES.items():
        role = await db.scalar(select(Role).where(Role.tenant_id == tenant_id, Role.name == name))
        if role is None:
            role = Role(tenant_id=tenant_id, name=name, description=f"Kalam predefined tenant role: {name}", role_kind="predefined")
            db.add(role)
            await db.flush()
        else:
            role.role_kind = "predefined"
        for key in keys:
            permission = permissions.get(key)
            if permission is None:
                continue
            exists = await db.scalar(select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id))
            if exists is None:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

def _ops_slug() -> str | None:
    return settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug


async def _ops_tenant(db: AsyncSession) -> Tenant | None:
    slug = _ops_slug()
    if not slug:
        return None
    return await db.scalar(select(Tenant).where(Tenant.slug == slug))


async def _is_platform_developer(user: User, db: AsyncSession) -> bool:
    return await is_platform_developer(user, db)


async def _is_demo_crm_user(user: User, db: AsyncSession) -> bool:
    if not settings.saas_demo_crm_enabled:
        return False
    demo_tenant = await db.scalar(select(Tenant).where(Tenant.slug == settings.saas_demo_tenant_slug))
    return bool(
        demo_tenant is not None
        and demo_tenant.status == "active"
        and user.tenant_id == demo_tenant.id
        and user.email.lower() == settings.saas_demo_admin_email.lower()
    )


async def _require_ops_user(
    user: User = Depends(require_permission("saas.crm.read")),
    db: AsyncSession = Depends(get_db),
) -> User:
    tenant = await _ops_tenant(db)
    if tenant is None:
        raise HTTPException(status_code=503, detail="SaaS operations tenant is not configured")
    if user.tenant_id == tenant.id:
        return user
    # CRM is an internal software-company capability. Tenant administrators
    # must never receive CRM merely because they can administer their tenant.
    # Platform Developer is the explicit exception for engineering/support.
    if await _is_platform_developer(user, db):
        # A support context substitutes the request tenant on the user object.
        # Never let it redirect internal CRM writes into a customer tenant.
        home_tenant_id = await db.scalar(select(User.tenant_id).where(User.id == user.id))
        if home_tenant_id == tenant.id:
            return user
    if await _is_demo_crm_user(user, db):
        return user
    raise HTTPException(status_code=403, detail="SaaS CRM is restricted to authorized operations or demo administration")


async def _require_managed_tenant_link(db: AsyncSession, user: User, tenant_id: UUID, account_id: UUID | None = None) -> Tenant:
    if await _is_demo_crm_user(user, db):
        raise HTTPException(status_code=403, detail="Demo CRM cannot link customer tenants")
    tenant = await db.get(Tenant, tenant_id)
    ops = await _ops_tenant(db)
    demo = await db.scalar(select(Tenant).where(Tenant.slug == settings.saas_demo_tenant_slug))
    if tenant is None or (ops and tenant.id == ops.id) or (demo and tenant.id == demo.id):
        raise HTTPException(status_code=422, detail="Managed tenant must reference a customer tenant")
    provenance = tenant.settings or {}
    if account_id is None or provenance.get("provisioning_source") != "saas_crm" or provenance.get("crm_account_id") != str(account_id):
        raise HTTPException(status_code=422, detail="Link tenants through their original CRM provisioning account")
    existing = await db.scalar(select(CRMAccount).where(
        CRMAccount.ops_tenant_id == user.tenant_id,
        CRMAccount.managed_tenant_id == tenant_id,
        *([CRMAccount.id != account_id] if account_id is not None else []),
    ))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant is already linked to a different CRM account")
    return tenant


async def _require_account(db: AsyncSession, tenant_id: UUID, account_id: UUID) -> CRMAccount:
    item = await db.scalar(select(CRMAccount).where(CRMAccount.id == account_id, CRMAccount.ops_tenant_id == tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="CRM account not found")
    return item


async def _require_plan(db: AsyncSession, tenant_id: UUID, plan_id: UUID | None) -> SaaSPlan | None:
    if plan_id is None:
        return None
    item = await db.scalar(select(SaaSPlan).where(SaaSPlan.id == plan_id, SaaSPlan.ops_tenant_id == tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="SaaS plan not found")
    return item


async def _require_offer(db: AsyncSession, tenant_id: UUID, offer_id: UUID | None) -> SaaSOffer | None:
    if offer_id is None:
        return None
    item = await db.scalar(select(SaaSOffer).where(SaaSOffer.id == offer_id, SaaSOffer.ops_tenant_id == tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="SaaS offer not found")
    return item


async def _require_owner(db: AsyncSession, tenant_id: UUID, owner_user_id: UUID | None) -> User | None:
    if owner_user_id is None:
        return None
    item = await db.scalar(select(User).where(User.id == owner_user_id, User.tenant_id == tenant_id, User.is_active.is_(True)))
    if item is None:
        raise HTTPException(status_code=404, detail="CRM owner not found")
    return item




def _validate_window(starts_at: datetime | None, ends_at: datetime | None, label: str) -> None:
    if starts_at is not None and ends_at is not None and ends_at <= starts_at:
        raise HTTPException(status_code=422, detail=f"{label} end must be after start")


def _validate_offer_terms(
    *,
    discount_type: str,
    discount_value: int,
    plan_id: UUID | None,
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> None:
    if discount_type not in {"percent", "fixed"}:
        raise HTTPException(status_code=422, detail="Unsupported discount type")
    if discount_type == "percent" and discount_value > 100:
        raise HTTPException(status_code=422, detail="Percentage discount cannot exceed 100%")
    if discount_type == "fixed" and plan_id is None:
        raise HTTPException(status_code=422, detail="Fixed-value offers must be linked to a plan with an explicit currency")
    _validate_window(starts_at, ends_at, "Offer")


def _validate_public_certification(
    *,
    public_visible: bool,
    status: str,
    registration_number: str | None,
    verification_url: str | None,
) -> None:
    if not public_visible:
        return
    if status not in {"active", "registered"}:
        raise HTTPException(status_code=422, detail="Only active or registered certifications can be published")
    if not (registration_number or verification_url):
        raise HTTPException(
            status_code=422,
            detail="A public certification requires a registration number or verification URL",
        )



def _validate_plan_bounds(minimum_seats: int, maximum_seats: int | None) -> None:
    if maximum_seats is not None and maximum_seats < minimum_seats:
        raise HTTPException(status_code=422, detail="Maximum seats cannot be lower than minimum seats")


def _validate_trial_seats(plan: SaaSPlan | None, seats: int) -> None:
    if plan is None:
        return
    if seats < plan.minimum_seats:
        raise HTTPException(status_code=422, detail="Trial seats are below the plan minimum")
    if plan.maximum_seats is not None and seats > plan.maximum_seats:
        raise HTTPException(status_code=422, detail="Trial seats exceed the plan maximum")


async def _validate_active_trial(db: AsyncSession, account: CRMAccount, starts_at: datetime | None, ends_at: datetime | None) -> None:
    if starts_at is None or ends_at is None:
        raise HTTPException(status_code=422, detail="Active trial requires start and end dates")
    start = starts_at if starts_at.tzinfo else starts_at.replace(tzinfo=timezone.utc)
    end = ends_at if ends_at.tzinfo else ends_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if not start <= now < end:
        raise HTTPException(status_code=422, detail="Active trial dates must include the current time")
    tenant = await db.get(Tenant, account.managed_tenant_id) if account.managed_tenant_id else None
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=422, detail="Active trial requires an active provisioned customer tenant")


def _offer_is_current(offer: SaaSOffer, now: datetime) -> bool:
    if offer.status != "active":
        return False
    if offer.starts_at is not None and offer.starts_at > now:
        return False
    if offer.ends_at is not None and offer.ends_at <= now:
        return False
    return True

class PlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    tagline: str | None = Field(default=None, max_length=240)
    description: str | None = None
    billing_model: str = Field(default="per_user", max_length=40)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    monthly_price_minor: int | None = Field(default=None, ge=0)
    annual_price_minor: int | None = Field(default=None, ge=0)
    trial_days: int = Field(default=0, ge=0, le=365)
    minimum_seats: int = Field(default=1, ge=1)
    maximum_seats: int | None = Field(default=None, ge=1)
    features: list[Any] = Field(default_factory=list)
    limits: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active", max_length=30)
    public_visible: bool = False
    sort_order: int = 100


class OfferCreate(BaseModel):
    plan_id: UUID | None = None
    code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    description: str | None = None
    discount_type: str = Field(default="percent", max_length=30)
    discount_value: int = Field(default=0, ge=0)
    public_visible: bool = False
    status: str = Field(default="draft", max_length=30)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=120)
    account_type: str = Field(default="prospect", max_length=30)
    lifecycle_stage: str = Field(default="lead", max_length=30)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=500)
    employee_band: str | None = Field(default=None, max_length=60)
    plan_id: UUID | None = None
    owner_user_id: UUID | None = None
    managed_tenant_id: UUID | None = None
    public_showcase: bool = False
    logo_url: str | None = Field(default=None, max_length=1000)
    testimonial: str | None = None
    notes: str | None = None
    record_metadata: dict[str, Any] = Field(default_factory=dict)


class ContactCreate(BaseModel):
    account_id: UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    job_title: str | None = Field(default=None, max_length=180)
    phone: str | None = Field(default=None, max_length=60)
    is_primary: bool = False


class TrialCreate(BaseModel):
    account_id: UUID
    plan_id: UUID | None = None
    status: str = Field(default="scheduled", pattern="^(scheduled|active|expired|converted|cancelled)$")
    seats: int = Field(default=25, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = None


class SubscriptionCreate(BaseModel):
    account_id: UUID
    managed_tenant_id: UUID | None = None
    plan_id: UUID | None = None
    offer_id: UUID | None = None
    status: str = Field(default="draft", max_length=30)
    billing_cycle: str = Field(default="annual", max_length=20)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    seats: int = Field(default=1, ge=1)
    list_price_minor: int = Field(default=0, ge=0)
    discount_minor: int = Field(default=0, ge=0)
    net_price_minor: int = Field(default=0, ge=0)
    starts_at: datetime | None = None
    renews_at: datetime | None = None
    ends_at: datetime | None = None
    contract_ref: str | None = Field(default=None, max_length=160)



class ContractCreate(BaseModel):
    account_id: UUID
    subscription_id: UUID | None = None
    reference: str = Field(min_length=2, max_length=160)
    status: str = Field(default="draft", max_length=30)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_value_minor: int = Field(default=0, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    signed_at: datetime | None = None
    renewal_terms: str | None = None
    notes: str | None = None


class ContractUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    total_value_minor: int | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    signed_at: datetime | None = None
    renewal_terms: str | None = None
    notes: str | None = None


class InvoiceCreate(BaseModel):
    account_id: UUID
    subscription_id: UUID | None = None
    contract_id: UUID | None = None
    invoice_number: str = Field(min_length=2, max_length=120)
    status: str = Field(default="draft", pattern="^(draft|issued)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    amount_minor: int = Field(default=0, ge=0)
    tax_minor: int = Field(default=0, ge=0)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    external_ref: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(draft|issued|void)$")
    amount_minor: int | None = Field(default=None, ge=0)
    tax_minor: int | None = Field(default=None, ge=0)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    external_ref: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: str = Field(default="received", pattern="^(received)$")
    received_at: datetime | None = None
    method: str | None = Field(default=None, max_length=60)
    reference: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class PaymentUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    received_at: datetime | None = None
    method: str | None = Field(default=None, max_length=60)
    reference: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class OpportunityCreate(BaseModel):
    account_id: UUID
    name: str = Field(min_length=2, max_length=180)
    stage: str = Field(default="discovery", max_length=40)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    amount_minor: int = Field(default=0, ge=0)
    probability_percent: int = Field(default=0, ge=0, le=100)
    expected_close_at: datetime | None = None
    owner_user_id: UUID | None = None
    notes: str | None = None


class TaskCreate(BaseModel):
    account_id: UUID | None = None
    subscription_id: UUID | None = None
    owner_user_id: UUID | None = None
    task_type: str = Field(default="follow_up", max_length=50)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    status: str = Field(default="open", max_length=30)
    priority: str = Field(default="normal", max_length=20)
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    owner_user_id: UUID | None = None
    task_type: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, max_length=30)
    priority: str | None = Field(default=None, max_length=20)
    due_at: datetime | None = None
    completed_at: datetime | None = None


class OnboardingItemCreate(BaseModel):
    account_id: UUID
    managed_tenant_id: UUID | None = None
    owner_user_id: UUID | None = None
    category: str = Field(default="general", max_length=50)
    title: str = Field(min_length=2, max_length=200)
    status: str = Field(default="pending", max_length=30)
    due_at: datetime | None = None
    notes: str | None = None
    sort_order: int = 100


class OnboardingItemUpdate(BaseModel):
    managed_tenant_id: UUID | None = None
    owner_user_id: UUID | None = None
    category: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, min_length=2, max_length=200)
    status: str | None = Field(default=None, max_length=30)
    due_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    sort_order: int | None = None


class ActivityCreate(BaseModel):
    account_id: UUID
    activity_type: str = Field(default="note", max_length=40)
    subject: str = Field(min_length=2, max_length=200)
    body: str | None = None
    happened_at: datetime | None = None



class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    tagline: str | None = Field(default=None, max_length=240)
    description: str | None = None
    status: str | None = Field(default=None, max_length=30)
    public_visible: bool | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    monthly_price_minor: int | None = Field(default=None, ge=0)
    annual_price_minor: int | None = Field(default=None, ge=0)
    trial_days: int | None = Field(default=None, ge=0, le=365)
    minimum_seats: int | None = Field(default=None, ge=1)
    maximum_seats: int | None = Field(default=None, ge=1)
    features: list[Any] | None = None
    limits: dict[str, Any] | None = None
    sort_order: int | None = None


class OfferUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    discount_type: str | None = Field(default=None, max_length=30)
    discount_value: int | None = Field(default=None, ge=0)
    public_visible: bool | None = None
    status: str | None = Field(default=None, max_length=30)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    lifecycle_stage: str | None = Field(default=None, max_length=30)
    account_type: str | None = Field(default=None, max_length=30)
    plan_id: UUID | None = None
    managed_tenant_id: UUID | None = None
    owner_user_id: UUID | None = None
    public_showcase: bool | None = None
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=500)
    employee_band: str | None = Field(default=None, max_length=60)
    logo_url: str | None = Field(default=None, max_length=1000)
    testimonial: str | None = None
    notes: str | None = None


class TrialUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(scheduled|active|expired|converted|cancelled)$")
    seats: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = None


class SubscriptionUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    seats: int | None = Field(default=None, ge=1)
    list_price_minor: int | None = Field(default=None, ge=0)
    discount_minor: int | None = Field(default=None, ge=0)
    net_price_minor: int | None = Field(default=None, ge=0)
    renews_at: datetime | None = None
    ends_at: datetime | None = None
    contract_ref: str | None = Field(default=None, max_length=160)


class OpportunityUpdate(BaseModel):
    stage: str | None = Field(default=None, max_length=40)
    amount_minor: int | None = Field(default=None, ge=0)
    probability_percent: int | None = Field(default=None, ge=0, le=100)
    expected_close_at: datetime | None = None
    notes: str | None = None


class CertificationUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    public_visible: bool | None = None
    registration_number: str | None = Field(default=None, max_length=180)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    verification_url: str | None = Field(default=None, max_length=1000)
    display_order: int | None = None


class InquiryConvert(BaseModel):
    lifecycle_stage: str = Field(default="qualified", max_length=30)
    plan_id: UUID | None = None
    create_opportunity: bool = True
    opportunity_amount_minor: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    create_trial: bool = False
    trial_seats: int = Field(default=25, ge=1)


def _crm_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:110] or "account"


class TenantProvisionCreate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=100)


class TenantCommercialUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")

class CertificationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    issuer: str = Field(min_length=2, max_length=180)
    registration_number: str | None = Field(default=None, max_length=180)
    status: str = Field(default="planned", max_length=30)
    public_visible: bool = False
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    verification_url: str | None = Field(default=None, max_length=1000)
    display_order: int = 100


def _plan_payload(item: SaaSPlan) -> dict[str, Any]:
    return {
        "id": str(item.id), "code": item.code, "name": item.name, "tagline": item.tagline,
        "description": item.description, "status": item.status, "public_visible": item.public_visible,
        "billing_model": item.billing_model, "currency": item.currency,
        "monthly_price_minor": item.monthly_price_minor, "annual_price_minor": item.annual_price_minor,
        "trial_days": item.trial_days, "minimum_seats": item.minimum_seats,
        "maximum_seats": item.maximum_seats, "features": item.features, "limits": item.limits,
        "sort_order": item.sort_order,
    }


@router.get("/public/catalog")
async def public_catalog(db: AsyncSession = Depends(get_db)):
    tenant = await _ops_tenant(db)
    if tenant is None:
        return {"plans": [], "offers": [], "clients": [], "certifications": []}
    plans = (await db.execute(
        select(SaaSPlan).where(
            SaaSPlan.ops_tenant_id == tenant.id,
            SaaSPlan.public_visible.is_(True),
            SaaSPlan.status == "active",
            SaaSPlan.currency == "USD",
        ).order_by(SaaSPlan.sort_order, SaaSPlan.name)
    )).scalars().all()
    now = datetime.now(timezone.utc)
    offers = (await db.execute(
        select(SaaSOffer).where(
            SaaSOffer.ops_tenant_id == tenant.id,
            SaaSOffer.public_visible.is_(True),
            SaaSOffer.status == "active",
            or_(SaaSOffer.starts_at.is_(None), SaaSOffer.starts_at <= now),
            or_(SaaSOffer.ends_at.is_(None), SaaSOffer.ends_at > now),
        ).order_by(SaaSOffer.created_at.desc())
    )).scalars().all()
    visible_plan_ids = {plan.id for plan in plans}
    offers = [offer for offer in offers if offer.plan_id is None or offer.plan_id in visible_plan_ids]
    clients = (await db.execute(
        select(CRMAccount).where(
            CRMAccount.ops_tenant_id == tenant.id,
            CRMAccount.public_showcase.is_(True),
            CRMAccount.lifecycle_stage == "customer",
        ).order_by(CRMAccount.name)
    )).scalars().all()
    certifications = (await db.execute(
        select(SaaSCertification).where(
            SaaSCertification.ops_tenant_id == tenant.id,
            SaaSCertification.public_visible.is_(True),
            SaaSCertification.status.in_(["active", "registered"]),
            or_(SaaSCertification.expires_at.is_(None), SaaSCertification.expires_at > now),
        ).order_by(SaaSCertification.display_order, SaaSCertification.title)
    )).scalars().all()
    return {
        "plans": [_plan_payload(item) for item in plans],
        "offers": [{
            "id": str(item.id), "plan_id": str(item.plan_id) if item.plan_id else None,
            "code": item.code, "title": item.title, "description": item.description,
            "discount_type": item.discount_type, "discount_value": item.discount_value,
            "starts_at": item.starts_at, "ends_at": item.ends_at,
        } for item in offers],
        "clients": [{
            "id": str(item.id), "name": item.name, "industry": item.industry,
            "country": item.country, "website": item.website, "logo_url": item.logo_url,
            "testimonial": item.testimonial,
        } for item in clients],
        "certifications": [{
            "id": str(item.id), "title": item.title, "issuer": item.issuer,
            "registration_number": item.registration_number, "issued_at": item.issued_at,
            "expires_at": item.expires_at, "verification_url": item.verification_url,
        } for item in certifications],
    }


@router.get("/crm/overview")
async def crm_overview(
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    account_count = await db.scalar(
        select(func.count()).select_from(CRMAccount).where(CRMAccount.ops_tenant_id == user.tenant_id)
    )
    customer_count = await db.scalar(
        select(func.count()).select_from(CRMAccount).where(
            CRMAccount.ops_tenant_id == user.tenant_id,
            CRMAccount.lifecycle_stage == "customer",
        )
    )
    active_trials = await db.scalar(
        select(func.count()).select_from(CRMTrial).where(
            CRMTrial.ops_tenant_id == user.tenant_id,
            CRMTrial.status == "active",
        )
    )
    scheduled_trials = await db.scalar(
        select(func.count()).select_from(CRMTrial).where(
            CRMTrial.ops_tenant_id == user.tenant_id,
            CRMTrial.status == "scheduled",
        )
    )
    active_subscriptions = await db.scalar(
        select(func.count()).select_from(CRMSubscription).where(
            CRMSubscription.ops_tenant_id == user.tenant_id,
            CRMSubscription.status == "active",
        )
    )
    now = datetime.now(timezone.utc)
    open_tasks = await db.scalar(
        select(func.count()).select_from(CRMTask).where(
            CRMTask.ops_tenant_id == user.tenant_id,
            CRMTask.status.in_(["open", "in_progress", "blocked"]),
        )
    )
    overdue_tasks = await db.scalar(
        select(func.count()).select_from(CRMTask).where(
            CRMTask.ops_tenant_id == user.tenant_id,
            CRMTask.status.in_(["open", "in_progress", "blocked"]),
            CRMTask.due_at.is_not(None),
            CRMTask.due_at < now,
        )
    )
    overdue_invoices = await db.scalar(
        select(func.count()).select_from(CRMInvoice).where(
            CRMInvoice.ops_tenant_id == user.tenant_id,
            CRMInvoice.status == "overdue",
        )
    )

    pipeline_rows = (await db.execute(
        select(
            CRMOpportunity.currency,
            func.coalesce(func.sum(CRMOpportunity.amount_minor), 0),
            func.count(CRMOpportunity.id),
        )
        .where(
            CRMOpportunity.ops_tenant_id == user.tenant_id,
            CRMOpportunity.stage.notin_(["won", "lost"]),
        )
        .group_by(CRMOpportunity.currency)
        .order_by(CRMOpportunity.currency)
    )).all()

    subscription_rows = (await db.execute(
        select(
            CRMSubscription.currency,
            CRMSubscription.billing_cycle,
            func.coalesce(func.sum(CRMSubscription.net_price_minor), 0),
            func.count(CRMSubscription.id),
        )
        .where(
            CRMSubscription.ops_tenant_id == user.tenant_id,
            CRMSubscription.status == "active",
        )
        .group_by(CRMSubscription.currency, CRMSubscription.billing_cycle)
        .order_by(CRMSubscription.currency, CRMSubscription.billing_cycle)
    )).all()

    return {
        "accounts": int(account_count or 0),
        "customers": int(customer_count or 0),
        "active_trials": int(active_trials or 0),
        "scheduled_trials": int(scheduled_trials or 0),
        "active_subscriptions": int(active_subscriptions or 0),
        "open_tasks": int(open_tasks or 0),
        "overdue_tasks": int(overdue_tasks or 0),
        "overdue_invoices": int(overdue_invoices or 0),
        "pipeline_by_currency": [
            {"currency": currency, "amount_minor": int(amount or 0), "opportunities": int(count or 0)}
            for currency, amount, count in pipeline_rows
        ],
        "subscriptions_by_currency_cycle": [
            {
                "currency": currency,
                "billing_cycle": billing_cycle,
                "net_value_minor": int(value or 0),
                "subscriptions": int(count or 0),
            }
            for currency, billing_cycle, value, count in subscription_rows
        ],
    }


@router.get("/crm/lookups/{kind}")
async def crm_lookup(
    kind: str,
    q: str | None = Query(default=None, max_length=160),
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    term = f"%{q.strip()}%" if q and q.strip() else None
    if kind == "accounts":
        account_stmt = select(CRMAccount).where(CRMAccount.ops_tenant_id == user.tenant_id)
        if status:
            account_stmt = account_stmt.where(CRMAccount.lifecycle_stage == status)
        if term:
            account_stmt = account_stmt.where(or_(CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term), CRMAccount.industry.ilike(term), CRMAccount.country.ilike(term)))
        account_rows = (await db.execute(account_stmt.order_by(CRMAccount.name).limit(limit))).scalars().all()
        return {"items": [{"id": str(row.id), "label": row.name, "meta": row.lifecycle_stage} for row in account_rows]}
    if kind == "plans":
        plan_stmt = select(SaaSPlan).where(SaaSPlan.ops_tenant_id == user.tenant_id)
        if status:
            plan_stmt = plan_stmt.where(SaaSPlan.status == status)
        if term:
            plan_stmt = plan_stmt.where(or_(SaaSPlan.name.ilike(term), SaaSPlan.code.ilike(term)))
        plan_rows = (await db.execute(plan_stmt.order_by(SaaSPlan.sort_order, SaaSPlan.name).limit(limit))).scalars().all()
        return {"items": [{"id": str(row.id), "label": row.name, "meta": row.code} for row in plan_rows]}
    if kind == "offers":
        offer_stmt = select(SaaSOffer).where(SaaSOffer.ops_tenant_id == user.tenant_id)
        if status:
            offer_stmt = offer_stmt.where(SaaSOffer.status == status)
        if term:
            offer_stmt = offer_stmt.where(or_(SaaSOffer.title.ilike(term), SaaSOffer.code.ilike(term)))
        offer_rows = (await db.execute(offer_stmt.order_by(SaaSOffer.created_at.desc()).limit(limit))).scalars().all()
        return {"items": [{"id": str(row.id), "label": row.title, "meta": row.code} for row in offer_rows]}
    if kind == "subscriptions":
        subscription_stmt = select(CRMSubscription, CRMAccount).join(CRMAccount, CRMAccount.id == CRMSubscription.account_id).where(CRMSubscription.ops_tenant_id == user.tenant_id)
        if account_id is not None:
            subscription_stmt = subscription_stmt.where(CRMSubscription.account_id == account_id)
        if status:
            subscription_stmt = subscription_stmt.where(CRMSubscription.status == status)
        if term:
            subscription_stmt = subscription_stmt.where(or_(CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term), CRMSubscription.status.ilike(term), CRMSubscription.billing_cycle.ilike(term)))
        subscription_rows = (await db.execute(subscription_stmt.order_by(CRMSubscription.created_at.desc()).limit(limit))).all()
        return {"items": [{"id": str(subscription.id), "label": f"{account.name} · {subscription.billing_cycle}", "meta": subscription.status, "account_id": str(account.id), "currency": subscription.currency, "net_price_minor": subscription.net_price_minor} for subscription, account in subscription_rows]}
    if kind == "contracts":
        contract_stmt = select(CRMContract, CRMAccount).join(CRMAccount, CRMAccount.id == CRMContract.account_id).where(CRMContract.ops_tenant_id == user.tenant_id)
        if account_id is not None:
            contract_stmt = contract_stmt.where(CRMContract.account_id == account_id)
        if status:
            contract_stmt = contract_stmt.where(CRMContract.status == status)
        if term:
            contract_stmt = contract_stmt.where(or_(CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term), CRMContract.reference.ilike(term), CRMContract.status.ilike(term)))
        contract_rows = (await db.execute(contract_stmt.order_by(CRMContract.updated_at.desc()).limit(limit))).all()
        return {"items": [{"id": str(contract.id), "label": f"{contract.reference} · {account.name}", "meta": contract.status, "account_id": str(account.id), "currency": contract.currency, "total_value_minor": contract.total_value_minor} for contract, account in contract_rows]}
    if kind == "invoices":
        invoice_stmt = select(CRMInvoice, CRMAccount).join(CRMAccount, CRMAccount.id == CRMInvoice.account_id).where(CRMInvoice.ops_tenant_id == user.tenant_id)
        if account_id is not None:
            invoice_stmt = invoice_stmt.where(CRMInvoice.account_id == account_id)
        if status:
            invoice_stmt = invoice_stmt.where(CRMInvoice.status == status)
        if term:
            invoice_stmt = invoice_stmt.where(or_(CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term), CRMInvoice.invoice_number.ilike(term), CRMInvoice.status.ilike(term)))
        invoice_rows = (await db.execute(invoice_stmt.order_by(CRMInvoice.due_at.asc().nullslast(), CRMInvoice.created_at.desc()).limit(limit))).all()
        items = []
        for invoice, account in invoice_rows:
            paid_minor, outstanding_minor = await _reconcile_invoice(db, invoice)
            if outstanding_minor <= 0:
                continue
            items.append({"id": str(invoice.id), "label": f"{invoice.invoice_number} · {account.name}", "meta": f"{outstanding_minor} {invoice.currency} outstanding", "account_id": str(account.id), "currency": invoice.currency, "outstanding_minor": outstanding_minor})
        return {"items": items[:limit]}
    raise HTTPException(status_code=404, detail="Unknown CRM lookup type")

@router.get("/crm/plans")
async def list_plans(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(SaaSPlan).where(SaaSPlan.ops_tenant_id == user.tenant_id).order_by(SaaSPlan.sort_order, SaaSPlan.name))).scalars().all()
    return [_plan_payload(item) for item in items]


@router.post("/crm/plans", status_code=201)
async def create_plan(payload: PlanCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    _validate_plan_bounds(payload.minimum_seats, payload.maximum_seats)
    item = SaaSPlan(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="saas.plan.created", entity_type="saas_plan", entity_id=str(item.id))
    await db.commit()
    return _plan_payload(item)


@router.get("/crm/accounts")
async def list_accounts(
    stage: str | None = Query(default=None, max_length=30),
    q: str | None = Query(default=None, max_length=160),
    owner_user_id: UUID | None = Query(default=None),
    country: str | None = Query(default=None, max_length=120),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMAccount).where(CRMAccount.ops_tenant_id == user.tenant_id)
    if stage:
        stmt = stmt.where(CRMAccount.lifecycle_stage == stage)
    if owner_user_id:
        stmt = stmt.where(CRMAccount.owner_user_id == owner_user_id)
    if country:
        stmt = stmt.where(CRMAccount.country.ilike(country))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            CRMAccount.name.ilike(term),
            CRMAccount.slug.ilike(term),
            CRMAccount.industry.ilike(term),
            CRMAccount.country.ilike(term),
        ))
    items = (await db.execute(stmt.order_by(CRMAccount.updated_at.desc(), CRMAccount.name))).scalars().all()
    return [{
        "id": str(item.id), "name": item.name, "slug": item.slug, "account_type": item.account_type,
        "lifecycle_stage": item.lifecycle_stage, "industry": item.industry, "country": item.country,
        "employee_band": item.employee_band, "public_showcase": item.public_showcase,
        "plan_id": str(item.plan_id) if item.plan_id else None,
        "managed_tenant_id": str(item.managed_tenant_id) if item.managed_tenant_id else None,
    } for item in items]


@router.get("/crm/page/accounts")
async def paged_accounts(
    stage: str | None = Query(default=None, max_length=30),
    q: str | None = Query(default=None, max_length=160),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMAccount).where(CRMAccount.ops_tenant_id == user.tenant_id)
    if stage:
        stmt = stmt.where(CRMAccount.lifecycle_stage == stage)
    if q and q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term),
            CRMAccount.industry.ilike(term), CRMAccount.country.ilike(term),
        ))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = (await db.execute(
        stmt.order_by(CRMAccount.updated_at.desc(), CRMAccount.id).offset(offset).limit(limit)
    )).scalars().all()
    return {
        "total": int(total or 0), "offset": offset, "limit": limit,
        "items": [{
            "id": str(item.id), "name": item.name, "slug": item.slug,
            "account_type": item.account_type, "lifecycle_stage": item.lifecycle_stage,
            "industry": item.industry, "country": item.country,
            "employee_band": item.employee_band, "public_showcase": item.public_showcase,
            "plan_id": str(item.plan_id) if item.plan_id else None,
            "managed_tenant_id": str(item.managed_tenant_id) if item.managed_tenant_id else None,
        } for item in items],
    }


@router.post("/crm/accounts", status_code=201)
async def create_account(payload: AccountCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _require_plan(db, user.tenant_id, payload.plan_id)
    await _require_owner(db, user.tenant_id, payload.owner_user_id)
    if payload.managed_tenant_id is not None:
        await _require_managed_tenant_link(db, user, payload.managed_tenant_id)
    if payload.public_showcase and payload.lifecycle_stage != "customer":
        raise HTTPException(status_code=422, detail="Only customer-stage accounts can be published as clients")
    item = CRMAccount(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.account.created", entity_type="crm_account", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "name": item.name, "lifecycle_stage": item.lifecycle_stage}


@router.post("/crm/contacts", status_code=201)
async def create_contact(payload: ContactCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    account = await db.scalar(select(CRMAccount).where(CRMAccount.id == payload.account_id, CRMAccount.ops_tenant_id == user.tenant_id))
    if account is None:
        raise HTTPException(status_code=404, detail="CRM account not found")
    item = CRMContact(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    return {"id": str(item.id)}


@router.get("/crm/trials")
async def list_trials(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(CRMTrial, CRMAccount, SaaSPlan)
        .join(CRMAccount, CRMAccount.id == CRMTrial.account_id)
        .outerjoin(SaaSPlan, SaaSPlan.id == CRMTrial.plan_id)
        .where(CRMTrial.ops_tenant_id == user.tenant_id)
        .order_by(CRMTrial.created_at.desc())
    )).all()
    return [{
        "id": str(trial.id), "account_id": str(trial.account_id), "account_name": account.name,
        "plan_id": str(trial.plan_id) if trial.plan_id else None, "plan_name": plan.name if plan else None,
        "status": trial.status, "seats": trial.seats, "starts_at": trial.starts_at, "ends_at": trial.ends_at
    } for trial, account, plan in rows]


@router.post("/crm/trials", status_code=201)
async def create_trial(payload: TrialCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id)
    plan = await _require_plan(db, user.tenant_id, payload.plan_id)
    _validate_window(payload.starts_at, payload.ends_at, "Trial")
    if payload.status == "active":
        await _validate_active_trial(db, account, payload.starts_at, payload.ends_at)
    _validate_trial_seats(plan, payload.seats)
    item = CRMTrial(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.trial.created", entity_type="crm_trial", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.get("/crm/subscriptions")
async def list_subscriptions(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(CRMSubscription).where(CRMSubscription.ops_tenant_id == user.tenant_id).order_by(CRMSubscription.created_at.desc()))).scalars().all()
    return [{"id": str(x.id), "account_id": str(x.account_id), "plan_id": str(x.plan_id) if x.plan_id else None, "status": x.status, "billing_cycle": x.billing_cycle, "currency": x.currency, "seats": x.seats, "list_price_minor": x.list_price_minor, "discount_minor": x.discount_minor, "net_price_minor": x.net_price_minor, "renews_at": x.renews_at} for x in items]


@router.get("/crm/page/subscriptions")
async def paged_subscriptions(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(CRMSubscription.id).where(CRMSubscription.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        base = base.where(CRMSubscription.account_id == account_id)
    if status:
        base = base.where(CRMSubscription.status == status)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = (await db.execute(
        select(CRMSubscription, CRMAccount, SaaSPlan)
        .join(CRMAccount, CRMAccount.id == CRMSubscription.account_id)
        .outerjoin(SaaSPlan, SaaSPlan.id == CRMSubscription.plan_id)
        .where(CRMSubscription.ops_tenant_id == user.tenant_id)
        .where(*([CRMSubscription.account_id == account_id] if account_id is not None else []))
        .where(*([CRMSubscription.status == status] if status else []))
        .order_by(CRMSubscription.created_at.desc(), CRMSubscription.id)
        .offset(offset).limit(limit)
    )).all()
    return {
        "total": int(total or 0), "offset": offset, "limit": limit,
        "items": [{
            "id": str(x.id), "account_id": str(x.account_id), "account_name": account.name,
            "plan_id": str(x.plan_id) if x.plan_id else None, "plan_name": plan.name if plan else None,
            "status": x.status, "billing_cycle": x.billing_cycle,
            "currency": x.currency, "seats": x.seats,
            "list_price_minor": x.list_price_minor, "discount_minor": x.discount_minor,
            "net_price_minor": x.net_price_minor, "renews_at": x.renews_at,
        } for x, account, plan in rows],
    }


@router.post("/crm/subscriptions", status_code=201)
async def create_subscription(payload: SubscriptionCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id)
    plan = await _require_plan(db, user.tenant_id, payload.plan_id)
    offer = await _require_offer(db, user.tenant_id, payload.offer_id)
    if payload.managed_tenant_id is not None and account.managed_tenant_id != payload.managed_tenant_id:
        raise HTTPException(status_code=422, detail="Subscription tenant must belong to the CRM account")
    if plan is not None:
        if plan.status != "active":
            raise HTTPException(status_code=422, detail="New subscriptions require an active plan")
        if plan.currency != payload.currency:
            raise HTTPException(status_code=422, detail="Subscription currency must match plan currency")
        _validate_trial_seats(plan, payload.seats)
    _validate_window(payload.starts_at, payload.ends_at, "Subscription")
    if offer is not None:
        if offer.plan_id is not None and (plan is None or offer.plan_id != plan.id):
            raise HTTPException(status_code=422, detail="Offer does not belong to the selected plan")
        if not _offer_is_current(offer, datetime.now(timezone.utc)):
            raise HTTPException(status_code=422, detail="Offer is not currently active")
    discount = payload.discount_minor
    if offer is not None:
        discount = (payload.list_price_minor * offer.discount_value + 50) // 100 if offer.discount_type == "percent" else offer.discount_value
    if discount > payload.list_price_minor:
        raise HTTPException(status_code=422, detail="Discount cannot exceed list price")
    values = payload.model_dump()
    values["discount_minor"] = discount
    values["net_price_minor"] = payload.list_price_minor - discount
    item = CRMSubscription(ops_tenant_id=user.tenant_id, **values)
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.subscription.created", entity_type="crm_subscription", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.get("/crm/opportunities")
async def list_opportunities(
    stage: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=180),
    owner_user_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMOpportunity, CRMAccount).join(CRMAccount, CRMAccount.id == CRMOpportunity.account_id).where(CRMOpportunity.ops_tenant_id == user.tenant_id)
    if stage:
        stmt = stmt.where(CRMOpportunity.stage == stage)
    if owner_user_id:
        stmt = stmt.where(CRMOpportunity.owner_user_id == owner_user_id)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(CRMOpportunity.name.ilike(term), CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term)))
    rows = (await db.execute(stmt.order_by(CRMOpportunity.updated_at.desc()))).all()
    return [{
        "id": str(x.id), "account_id": str(x.account_id), "account_name": account.name,
        "name": x.name, "stage": x.stage, "currency": x.currency, "amount_minor": x.amount_minor,
        "probability_percent": x.probability_percent, "expected_close_at": x.expected_close_at,
        "owner_user_id": str(x.owner_user_id) if x.owner_user_id else None
    } for x, account in rows]


@router.get("/crm/pipeline-forecast")
async def pipeline_forecast(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            CRMOpportunity.currency,
            CRMOpportunity.stage,
            func.coalesce(func.sum(CRMOpportunity.amount_minor), 0),
            func.coalesce(func.sum(CRMOpportunity.amount_minor * CRMOpportunity.probability_percent / 100.0), 0),
            func.count(CRMOpportunity.id),
        )
        .where(
            CRMOpportunity.ops_tenant_id == user.tenant_id,
            CRMOpportunity.stage.notin_(["won", "lost"]),
        )
        .group_by(CRMOpportunity.currency, CRMOpportunity.stage)
        .order_by(CRMOpportunity.currency, CRMOpportunity.stage)
    )).all()
    return [{
        "currency": currency,
        "stage": stage,
        "gross_amount_minor": int(gross or 0),
        "weighted_amount_minor": int(weighted or 0),
        "opportunities": int(count or 0),
    } for currency, stage, gross, weighted, count in rows]


@router.post("/crm/opportunities", status_code=201)
async def create_opportunity(payload: OpportunityCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _require_account(db, user.tenant_id, payload.account_id)
    await _require_owner(db, user.tenant_id, payload.owner_user_id)
    item = CRMOpportunity(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    return {"id": str(item.id), "stage": item.stage}


@router.get("/crm/offers")
async def list_offers(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(SaaSOffer).where(SaaSOffer.ops_tenant_id == user.tenant_id).order_by(SaaSOffer.created_at.desc()))).scalars().all()
    return [{"id": str(x.id), "plan_id": str(x.plan_id) if x.plan_id else None, "code": x.code, "title": x.title, "discount_type": x.discount_type, "discount_value": x.discount_value, "status": x.status, "public_visible": x.public_visible, "starts_at": x.starts_at, "ends_at": x.ends_at} for x in items]


@router.post("/crm/offers", status_code=201)
async def create_offer(payload: OfferCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _require_plan(db, user.tenant_id, payload.plan_id)
    _validate_offer_terms(
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        plan_id=payload.plan_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    item = SaaSOffer(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    return {"id": str(item.id), "code": item.code}


@router.get("/crm/certifications")
async def list_certifications(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(SaaSCertification).where(SaaSCertification.ops_tenant_id == user.tenant_id).order_by(SaaSCertification.display_order, SaaSCertification.title))).scalars().all()
    return [{"id": str(x.id), "title": x.title, "issuer": x.issuer, "registration_number": x.registration_number, "status": x.status, "public_visible": x.public_visible, "issued_at": x.issued_at, "expires_at": x.expires_at, "verification_url": x.verification_url} for x in items]


@router.post("/crm/certifications", status_code=201)
async def create_certification(payload: CertificationCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    _validate_public_certification(
        public_visible=payload.public_visible,
        status=payload.status,
        registration_number=payload.registration_number,
        verification_url=payload.verification_url,
    )
    _validate_window(payload.issued_at, payload.expires_at, "Certification")
    item = SaaSCertification(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    return {"id": str(item.id), "title": item.title}


@router.post("/crm/activities", status_code=201)
async def create_activity(payload: ActivityCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _require_account(db, user.tenant_id, payload.account_id)
    item = CRMSalesActivity(
        ops_tenant_id=user.tenant_id,
        actor_user_id=user.id,
        happened_at=payload.happened_at or datetime.now().astimezone(),
        **payload.model_dump(exclude={"happened_at"}),
    )
    db.add(item)
    await db.commit()
    return {"id": str(item.id)}


def _apply_patch(item: Any, payload: BaseModel) -> list[str]:
    changed: list[str] = []
    for field in payload.model_fields_set:
        setattr(item, field, getattr(payload, field))
        changed.append(field)
    return sorted(changed)


@router.patch("/crm/plans/{plan_id}")
async def update_plan(plan_id: UUID, payload: PlanUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(SaaSPlan).where(SaaSPlan.id == plan_id, SaaSPlan.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    minimum = payload.minimum_seats if "minimum_seats" in payload.model_fields_set else item.minimum_seats
    maximum = payload.maximum_seats if "maximum_seats" in payload.model_fields_set else item.maximum_seats
    if minimum is None:
        raise HTTPException(status_code=422, detail="Minimum seats are required")
    _validate_plan_bounds(minimum, maximum)
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="saas.plan.updated", entity_type="saas_plan", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return _plan_payload(item)


@router.patch("/crm/accounts/{account_id}")
async def update_account(account_id: UUID, payload: AccountUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMAccount).where(CRMAccount.id == account_id, CRMAccount.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="CRM account not found")
    if "plan_id" in payload.model_fields_set:
        await _require_plan(db, user.tenant_id, payload.plan_id)
    if "owner_user_id" in payload.model_fields_set:
        await _require_owner(db, user.tenant_id, payload.owner_user_id)
    if "managed_tenant_id" in payload.model_fields_set and payload.managed_tenant_id is not None:
        await _require_managed_tenant_link(db, user, payload.managed_tenant_id, account_id=item.id)
    future_lifecycle = payload.lifecycle_stage if "lifecycle_stage" in payload.model_fields_set else item.lifecycle_stage
    future_showcase = payload.public_showcase if "public_showcase" in payload.model_fields_set else item.public_showcase
    if future_showcase and future_lifecycle != "customer":
        raise HTTPException(status_code=422, detail="Only customer-stage accounts can be published as clients")
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.account.updated", entity_type="crm_account", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "lifecycle_stage": item.lifecycle_stage, "public_showcase": item.public_showcase}


@router.patch("/crm/offers/{offer_id}")
async def update_offer(offer_id: UUID, payload: OfferUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(SaaSOffer).where(SaaSOffer.id == offer_id, SaaSOffer.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    future_type = payload.discount_type if "discount_type" in payload.model_fields_set else item.discount_type
    future_value = payload.discount_value if "discount_value" in payload.model_fields_set else item.discount_value
    if future_type is None or future_value is None:
        raise HTTPException(status_code=422, detail="Discount type and value are required")
    future_start = payload.starts_at if "starts_at" in payload.model_fields_set else item.starts_at
    future_end = payload.ends_at if "ends_at" in payload.model_fields_set else item.ends_at
    _validate_offer_terms(
        discount_type=future_type,
        discount_value=future_value,
        plan_id=item.plan_id,
        starts_at=future_start,
        ends_at=future_end,
    )
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="saas.offer.updated", entity_type="saas_offer", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "status": item.status, "public_visible": item.public_visible}


@router.patch("/crm/trials/{trial_id}")
async def update_trial(trial_id: UUID, payload: TrialUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMTrial).where(CRMTrial.id == trial_id, CRMTrial.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Trial not found")
    future_start = payload.starts_at if "starts_at" in payload.model_fields_set else item.starts_at
    future_end = payload.ends_at if "ends_at" in payload.model_fields_set else item.ends_at
    future_seats = payload.seats if "seats" in payload.model_fields_set else item.seats
    if future_seats is None:
        raise HTTPException(status_code=422, detail="Trial seats are required")
    _validate_window(future_start, future_end, "Trial")
    plan = await _require_plan(db, user.tenant_id, item.plan_id)
    _validate_trial_seats(plan, future_seats)
    if "status" in payload.model_fields_set and payload.status is None:
        raise HTTPException(status_code=422, detail="Trial status is required")
    if (payload.status if "status" in payload.model_fields_set else item.status) == "active":
        account = await _require_account(db, user.tenant_id, item.account_id)
        await _validate_active_trial(db, account, future_start, future_end)
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.trial.updated", entity_type="crm_trial", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.patch("/crm/subscriptions/{subscription_id}")
async def update_subscription(subscription_id: UUID, payload: SubscriptionUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMSubscription).where(CRMSubscription.id == subscription_id, CRMSubscription.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    prospective_list = payload.list_price_minor if "list_price_minor" in payload.model_fields_set else item.list_price_minor
    prospective_discount = payload.discount_minor if "discount_minor" in payload.model_fields_set else item.discount_minor
    if item.offer_id is not None and "discount_minor" in payload.model_fields_set:
        raise HTTPException(status_code=422, detail="Discount is derived from the selected offer")
    plan = await _require_plan(db, user.tenant_id, item.plan_id)
    if plan is not None and "seats" in payload.model_fields_set:
        assert payload.seats is not None
        _validate_trial_seats(plan, payload.seats)
    if item.offer_id is not None and "list_price_minor" in payload.model_fields_set:
        offer = await _require_offer(db, user.tenant_id, item.offer_id)
        assert offer is not None and prospective_list is not None
        prospective_discount = (prospective_list * offer.discount_value + 50) // 100 if offer.discount_type == "percent" else offer.discount_value
    if prospective_discount is not None and prospective_list is not None and prospective_discount > prospective_list:
        raise HTTPException(status_code=422, detail="Discount cannot exceed list price")
    changed = _apply_patch(item, payload)
    if item.offer_id is not None and "list_price_minor" in payload.model_fields_set:
        item.discount_minor = int(prospective_discount or 0)
        changed.append("discount_minor")
    item.net_price_minor = int(prospective_list or 0) - int(prospective_discount or 0)
    if "net_price_minor" not in changed:
        changed.append("net_price_minor")
        changed.sort()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.subscription.updated", entity_type="crm_subscription", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "status": item.status, "net_price_minor": item.net_price_minor}


@router.patch("/crm/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: UUID, payload: OpportunityUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMOpportunity).where(CRMOpportunity.id == opportunity_id, CRMOpportunity.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.opportunity.updated", entity_type="crm_opportunity", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "stage": item.stage}


@router.patch("/crm/certifications/{certification_id}")
async def update_certification(certification_id: UUID, payload: CertificationUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(SaaSCertification).where(SaaSCertification.id == certification_id, SaaSCertification.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    future_status = payload.status if "status" in payload.model_fields_set else item.status
    future_public = payload.public_visible if "public_visible" in payload.model_fields_set else item.public_visible
    if future_status is None or future_public is None:
        raise HTTPException(status_code=422, detail="Certification status and visibility are required")
    future_registration = payload.registration_number if "registration_number" in payload.model_fields_set else item.registration_number
    future_verification = payload.verification_url if "verification_url" in payload.model_fields_set else item.verification_url
    future_issued = payload.issued_at if "issued_at" in payload.model_fields_set else item.issued_at
    future_expires = payload.expires_at if "expires_at" in payload.model_fields_set else item.expires_at
    _validate_public_certification(
        public_visible=future_public,
        status=future_status,
        registration_number=future_registration,
        verification_url=future_verification,
    )
    _validate_window(future_issued, future_expires, "Certification")
    changed = _apply_patch(item, payload)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="saas.certification.updated", entity_type="saas_certification", entity_id=str(item.id), metadata={"changed_fields": changed})
    await db.commit()
    return {"id": str(item.id), "status": item.status, "public_visible": item.public_visible}


@router.post("/crm/inquiries/{inquiry_id}/convert", status_code=201)
async def convert_inquiry(
    inquiry_id: UUID,
    payload: InquiryConvert,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    if await _is_demo_crm_user(user, db):
        raise HTTPException(status_code=403, detail="Demo CRM cannot convert production marketing inquiries")
    ops_tenant = await _ops_tenant(db)
    if ops_tenant is None:
        raise HTTPException(status_code=503, detail="SaaS operations tenant is not configured")
    if settings.marketing_review_tenant_slug and settings.marketing_review_tenant_slug != ops_tenant.slug:
        raise HTTPException(status_code=409, detail="Marketing review tenant and SaaS operations tenant must match for CRM conversion")
    inquiry = await db.get(MarketingInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    if inquiry.crm_account_id is not None:
        return {
            "account_id": str(inquiry.crm_account_id),
            "opportunity_id": None,
            "trial_id": None,
            "already_converted": True,
        }

    resolved_plan_id = payload.plan_id
    resolved_plan = None
    if resolved_plan_id is not None:
        resolved_plan = await _require_plan(db, user.tenant_id, resolved_plan_id)
    elif inquiry.plan_code:
        resolved_plan = await db.scalar(select(SaaSPlan).where(
            SaaSPlan.ops_tenant_id == user.tenant_id,
            SaaSPlan.code == inquiry.plan_code.lower(),
        ))
        resolved_plan_id = resolved_plan.id if resolved_plan else None

    base_slug = _crm_slug(inquiry.organization)
    existing = await db.scalar(
        select(CRMAccount).where(
            CRMAccount.ops_tenant_id == user.tenant_id,
            CRMAccount.slug == base_slug,
        )
    )
    account = existing
    if account is None:
        slug = base_slug
        suffix = 2
        while await db.scalar(select(CRMAccount.id).where(CRMAccount.ops_tenant_id == user.tenant_id, CRMAccount.slug == slug)):
            slug = f"{base_slug[:100]}-{suffix}"
            suffix += 1
        account = CRMAccount(
            ops_tenant_id=user.tenant_id,
            name=inquiry.organization,
            slug=slug,
            account_type="prospect",
            lifecycle_stage=payload.lifecycle_stage,
            plan_id=resolved_plan_id,
            owner_user_id=user.id,
            country=inquiry.country_name,
            employee_band=inquiry.organization_size,
            notes=inquiry.message,
            record_metadata={
                "source": "marketing_inquiry",
                "source_inquiry_id": str(inquiry.id),
                "inquiry_source": inquiry.source,
                "country_code": inquiry.country_code,
                "primary_objective": inquiry.primary_objective,
                "evaluation_timeline": inquiry.evaluation_timeline,
                "utm_source": inquiry.utm_source,
                "utm_medium": inquiry.utm_medium,
                "utm_campaign": inquiry.utm_campaign,
                "landing_path": inquiry.landing_path,
            },
        )
        db.add(account)
        await db.flush()
    else:
        if resolved_plan_id is not None:
            account.plan_id = resolved_plan_id
        if account.lifecycle_stage == "lead":
            account.lifecycle_stage = payload.lifecycle_stage
        if not account.country and inquiry.country_name:
            account.country = inquiry.country_name
        if not account.employee_band and inquiry.organization_size:
            account.employee_band = inquiry.organization_size
        metadata = dict(account.record_metadata or {})
        metadata.update({
            "latest_inquiry_id": str(inquiry.id),
            "latest_inquiry_source": inquiry.source,
            "primary_objective": inquiry.primary_objective,
            "evaluation_timeline": inquiry.evaluation_timeline,
            "utm_source": inquiry.utm_source,
            "utm_medium": inquiry.utm_medium,
            "utm_campaign": inquiry.utm_campaign,
            "landing_path": inquiry.landing_path,
        })
        account.record_metadata = metadata

    contact_exists = await db.scalar(
        select(CRMContact.id).where(
            CRMContact.account_id == account.id,
            CRMContact.email == inquiry.work_email,
        )
    )
    if contact_exists is None:
        name_parts = inquiry.name.strip().split(maxsplit=1)
        db.add(CRMContact(
            ops_tenant_id=user.tenant_id,
            account_id=account.id,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=inquiry.work_email,
            job_title=inquiry.job_title,
            phone=inquiry.business_phone,
            is_primary=True,
        ))

    opportunity_id = None
    if payload.create_opportunity:
        opportunity = CRMOpportunity(
            ops_tenant_id=user.tenant_id,
            account_id=account.id,
            owner_user_id=user.id,
            name=f"{account.name} — Kalam evaluation",
            stage="discovery",
            currency=payload.currency,
            amount_minor=payload.opportunity_amount_minor,
            probability_percent=10,
            notes=inquiry.message,
        )
        db.add(opportunity)
        await db.flush()
        opportunity_id = opportunity.id

    trial_id = None
    if payload.create_trial:
        _validate_trial_seats(resolved_plan, payload.trial_seats)
        if resolved_plan is not None and resolved_plan.trial_days <= 0:
            raise HTTPException(status_code=422, detail="Selected plan is not trial-enabled")
        trial = CRMTrial(
            ops_tenant_id=user.tenant_id,
            account_id=account.id,
            plan_id=resolved_plan_id,
            status="scheduled",
            seats=payload.trial_seats,
            notes="Created from website inquiry; dates require commercial review.",
        )
        db.add(trial)
        await db.flush()
        trial_id = trial.id
        account.lifecycle_stage = "trial"

    inquiry.status = "contacted"
    inquiry.reviewed_by = user.id
    inquiry.crm_account_id = account.id
    inquiry.converted_at = datetime.now(timezone.utc)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="marketing.inquiry.converted_to_crm",
        entity_type="marketing_inquiry",
        entity_id=str(inquiry.id),
        metadata={
            "crm_account_id": str(account.id),
            "opportunity_id": str(opportunity_id) if opportunity_id else None,
            "trial_id": str(trial_id) if trial_id else None,
        },
    )
    await db.commit()
    return {
        "account_id": str(account.id),
        "opportunity_id": str(opportunity_id) if opportunity_id else None,
        "trial_id": str(trial_id) if trial_id else None,
        "already_converted": False,
    }


@router.get("/crm/tenants")
async def list_managed_tenants(
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    if await _is_demo_crm_user(user, db):
        return []
    linked_ids = select(CRMAccount.managed_tenant_id).where(
        CRMAccount.ops_tenant_id == user.tenant_id,
        CRMAccount.managed_tenant_id.is_not(None),
    )
    result = await db.execute(
        select(Tenant, func.count(User.id))
        .outerjoin(User, User.tenant_id == Tenant.id)
        .where(Tenant.id.in_(linked_ids), Tenant.id != user.tenant_id, Tenant.slug != settings.saas_demo_tenant_slug)
        .group_by(Tenant.id)
        .order_by(Tenant.created_at.desc())
    )
    account_result = await db.execute(
        select(CRMAccount).where(
            CRMAccount.ops_tenant_id == user.tenant_id,
            CRMAccount.managed_tenant_id.is_not(None),
        )
    )
    account_by_tenant = {
        item.managed_tenant_id: item
        for item in account_result.scalars().all()
        if item.managed_tenant_id is not None
    }
    payload = []
    for tenant, user_count in result.all():
        account = account_by_tenant.get(tenant.id)
        payload.append({
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
            "user_count": int(user_count or 0),
            "created_at": tenant.created_at,
            "crm_account_id": str(account.id) if account else None,
            "crm_account_name": account.name if account else None,
            "lifecycle_stage": account.lifecycle_stage if account else None,
        })
    return payload


class ManagedUserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    job_title: str | None = Field(default=None, max_length=160)
    is_active: bool | None = None
    unlock_now: bool = False


@router.get("/crm/tenants/{tenant_id}/users")
async def list_managed_tenant_users(
    tenant_id: UUID,
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    ops = await _ops_tenant(db)
    if ops is None or not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Developer access is required for tenant identity administration")
    account = await db.scalar(select(CRMAccount).where(
        CRMAccount.ops_tenant_id == ops.id,
        CRMAccount.managed_tenant_id == tenant_id,
    ))
    if account is None:
        raise HTTPException(status_code=404, detail="Tenant is not linked to this CRM")
    rows = (await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.last_name, User.first_name, User.email)
    )).scalars().all()
    return [{
        "id": str(item.id),
        "email": item.email,
        "first_name": item.first_name,
        "last_name": item.last_name,
        "job_title": item.job_title,
        "is_active": item.is_active,
        "locked": bool(item.locked_until and item.locked_until > datetime.now(timezone.utc)),
        "last_login_at": item.last_login_at,
    } for item in rows]


@router.patch("/crm/tenants/{tenant_id}/users/{user_id}")
async def update_managed_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    payload: ManagedUserUpdate,
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    ops = await _ops_tenant(db)
    if ops is None or not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Developer access is required for tenant identity administration")
    account = await db.scalar(select(CRMAccount).where(
        CRMAccount.ops_tenant_id == ops.id,
        CRMAccount.managed_tenant_id == tenant_id,
    ))
    if account is None:
        raise HTTPException(status_code=404, detail="Tenant is not linked to this CRM")
    target = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.is_active is not None:
        target.is_active = payload.is_active
        if not payload.is_active:
            sessions = (await db.execute(
                select(SessionRecord).where(SessionRecord.user_id == target.id, SessionRecord.revoked_at.is_(None))
            )).scalars().all()
            now = datetime.now(timezone.utc)
            for session in sessions:
                session.revoked_at = now
    for field in ("first_name", "last_name", "job_title"):
        if field in payload.model_fields_set:
            setattr(target, field, getattr(payload, field))
    if payload.unlock_now:
        target.failed_login_count = 0
        target.locked_until = None
    await audit(db, tenant_id=ops.id, actor_id=user.id, action="saas.tenant.user.updated",
        entity_type="user", entity_id=str(target.id),
        metadata={"managed_tenant_id": str(tenant_id), "changed_fields": sorted(payload.model_fields_set)})
    await db.commit()
    return {
        "id": str(target.id), "email": target.email, "is_active": target.is_active,
        "locked": bool(target.locked_until and target.locked_until > datetime.now(timezone.utc)),
    }


@router.post("/crm/accounts/{account_id}/provision-tenant", status_code=201)
async def provision_tenant(
    account_id: UUID,
    payload: TenantProvisionCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    if await _is_demo_crm_user(user, db):
        raise HTTPException(status_code=403, detail="Demo CRM cannot provision customer tenants")
    account = await db.scalar(
        select(CRMAccount).where(
            CRMAccount.id == account_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="CRM account not found")
    if account.managed_tenant_id is not None:
        tenant = await db.get(Tenant, account.managed_tenant_id)
        if tenant is not None:
            return {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "already_provisioned": True,
            }

    tenant_slug = (payload.slug or account.slug).strip().lower()
    tenant_name = (payload.name or account.name).strip()
    existing = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(
        name=tenant_name,
        slug=tenant_slug,
        status="active",
        settings={
            "provisioning_source": "saas_crm",
            "crm_account_id": str(account.id),
            "commercial_lifecycle_stage": account.lifecycle_stage,
        },
    )
    db.add(tenant)
    await db.flush()
    await _ensure_tenant_roles(db, tenant.id)
    account.managed_tenant_id = tenant.id
    if account.lifecycle_stage in {"lead", "qualified"}:
        account.lifecycle_stage = "trial"

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="saas.tenant.provisioned",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={"crm_account_id": str(account.id), "tenant_slug": tenant.slug},
    )
    await db.commit()
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "already_provisioned": False,
    }


@router.patch("/crm/tenants/{tenant_id}")
async def update_managed_tenant(
    tenant_id: UUID,
    payload: TenantCommercialUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    if await _is_demo_crm_user(user, db):
        raise HTTPException(status_code=403, detail="Demo CRM cannot change customer tenant status")
    account = await db.scalar(select(CRMAccount).where(
        CRMAccount.ops_tenant_id == user.tenant_id,
        CRMAccount.managed_tenant_id == tenant_id,
    ))
    if tenant_id == user.tenant_id or await db.scalar(select(Tenant.id).where(Tenant.id == tenant_id, Tenant.slug == settings.saas_demo_tenant_slug)):
        raise HTTPException(status_code=403, detail="Operations and demo tenants cannot be changed here")
    if account is None:
        raise HTTPException(status_code=404, detail="Tenant is not linked to this CRM")
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    previous_status = tenant.status
    tenant.status = payload.status
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="saas.tenant.status_changed",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={"from": previous_status, "to": tenant.status},
    )
    await db.commit()
    return {"id": str(tenant.id), "status": tenant.status}


@router.get("/crm/accounts/{account_id}")
async def account_detail(
    account_id: UUID,
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    account = await db.scalar(
        select(CRMAccount).where(
            CRMAccount.id == account_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="CRM account not found")

    contacts = (await db.execute(
        select(CRMContact)
        .where(CRMContact.account_id == account.id, CRMContact.ops_tenant_id == user.tenant_id)
        .order_by(CRMContact.is_primary.desc(), CRMContact.created_at.desc())
    )).scalars().all()
    trials = (await db.execute(
        select(CRMTrial)
        .where(CRMTrial.account_id == account.id, CRMTrial.ops_tenant_id == user.tenant_id)
        .order_by(CRMTrial.created_at.desc())
    )).scalars().all()
    subscriptions = (await db.execute(
        select(CRMSubscription)
        .where(CRMSubscription.account_id == account.id, CRMSubscription.ops_tenant_id == user.tenant_id)
        .order_by(CRMSubscription.created_at.desc())
    )).scalars().all()
    opportunities = (await db.execute(
        select(CRMOpportunity)
        .where(CRMOpportunity.account_id == account.id, CRMOpportunity.ops_tenant_id == user.tenant_id)
        .order_by(CRMOpportunity.updated_at.desc())
    )).scalars().all()
    contracts = (await db.execute(
        select(CRMContract)
        .where(CRMContract.account_id == account.id, CRMContract.ops_tenant_id == user.tenant_id)
        .order_by(CRMContract.updated_at.desc())
    )).scalars().all()
    invoices = (await db.execute(
        select(CRMInvoice)
        .where(CRMInvoice.account_id == account.id, CRMInvoice.ops_tenant_id == user.tenant_id)
        .order_by(CRMInvoice.created_at.desc())
    )).scalars().all()
    payments = (await db.execute(
        select(CRMPayment)
        .where(CRMPayment.account_id == account.id, CRMPayment.ops_tenant_id == user.tenant_id)
        .order_by(CRMPayment.received_at.desc())
    )).scalars().all()
    invoice_financials: dict[UUID, tuple[int, int]] = {}
    for invoice in invoices:
        invoice_financials[invoice.id] = await _reconcile_invoice(db, invoice)
    activities = (await db.execute(
        select(CRMSalesActivity)
        .where(CRMSalesActivity.account_id == account.id, CRMSalesActivity.ops_tenant_id == user.tenant_id)
        .order_by(CRMSalesActivity.happened_at.desc())
        .limit(100)
    )).scalars().all()

    plan = await db.get(SaaSPlan, account.plan_id) if account.plan_id else None
    managed_tenant = await db.get(Tenant, account.managed_tenant_id) if account.managed_tenant_id else None
    owner = await db.get(User, account.owner_user_id) if account.owner_user_id else None

    return {
        "id": str(account.id),
        "name": account.name,
        "slug": account.slug,
        "account_type": account.account_type,
        "lifecycle_stage": account.lifecycle_stage,
        "industry": account.industry,
        "country": account.country,
        "website": account.website,
        "employee_band": account.employee_band,
        "public_showcase": account.public_showcase,
        "logo_url": account.logo_url,
        "testimonial": account.testimonial,
        "notes": account.notes,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "plan": {"id": str(plan.id), "name": plan.name, "code": plan.code} if plan else None,
        "managed_tenant": {
            "id": str(managed_tenant.id),
            "name": managed_tenant.name,
            "slug": managed_tenant.slug,
            "status": managed_tenant.status,
        } if managed_tenant else None,
        "owner": {
            "id": str(owner.id),
            "name": f"{owner.first_name} {owner.last_name}",
            "email": owner.email,
        } if owner else None,
        "contacts": [{
            "id": str(item.id),
            "first_name": item.first_name,
            "last_name": item.last_name,
            "email": item.email,
            "job_title": item.job_title,
            "phone": item.phone,
            "is_primary": item.is_primary,
        } for item in contacts],
        "trials": [{
            "id": str(item.id),
            "plan_id": str(item.plan_id) if item.plan_id else None,
            "status": item.status,
            "seats": item.seats,
            "starts_at": item.starts_at,
            "ends_at": item.ends_at,
        } for item in trials],
        "subscriptions": [{
            "id": str(item.id),
            "plan_id": str(item.plan_id) if item.plan_id else None,
            "status": item.status,
            "billing_cycle": item.billing_cycle,
            "currency": item.currency,
            "seats": item.seats,
            "list_price_minor": item.list_price_minor,
            "discount_minor": item.discount_minor,
            "net_price_minor": item.net_price_minor,
            "renews_at": item.renews_at,
            "contract_ref": item.contract_ref,
        } for item in subscriptions],
        "opportunities": [{
            "id": str(item.id),
            "name": item.name,
            "stage": item.stage,
            "currency": item.currency,
            "amount_minor": item.amount_minor,
            "probability_percent": item.probability_percent,
            "expected_close_at": item.expected_close_at,
        } for item in opportunities],
        "contracts": [{
            "id": str(item.id),
            "reference": item.reference,
            "status": item.status,
            "currency": item.currency,
            "total_value_minor": item.total_value_minor,
            "starts_at": item.starts_at,
            "ends_at": item.ends_at,
            "signed_at": item.signed_at,
        } for item in contracts],
        "invoices": [{
            "id": str(item.id),
            "invoice_number": item.invoice_number,
            "status": item.status,
            "currency": item.currency,
            "total_minor": item.total_minor,
            "paid_minor": invoice_financials[item.id][0],
            "outstanding_minor": invoice_financials[item.id][1],
            "issued_at": item.issued_at,
            "due_at": item.due_at,
            "paid_at": item.paid_at,
        } for item in invoices],
        "payments": [{
            "id": str(item.id),
            "invoice_id": str(item.invoice_id),
            "amount_minor": item.amount_minor,
            "currency": item.currency,
            "status": item.status,
            "received_at": item.received_at,
            "method": item.method,
            "reference": item.reference,
        } for item in payments],
        "activities": [{
            "id": str(item.id),
            "activity_type": item.activity_type,
            "subject": item.subject,
            "body": item.body,
            "happened_at": item.happened_at,
            "actor_user_id": str(item.actor_user_id) if item.actor_user_id else None,
        } for item in activities],
    }


@router.get("/crm/onboarding")
async def list_onboarding_items(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMOnboardingItem).where(CRMOnboardingItem.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMOnboardingItem.account_id == account_id)
    if status:
        stmt = stmt.where(CRMOnboardingItem.status == status)
    items = (await db.execute(
        stmt.order_by(
            CRMOnboardingItem.status,
            CRMOnboardingItem.due_at.asc().nullslast(),
            CRMOnboardingItem.sort_order,
            CRMOnboardingItem.created_at,
        )
    )).scalars().all()
    account_ids = {item.account_id for item in items}
    account_rows = (await db.execute(
        select(CRMAccount.id, CRMAccount.name).where(
            CRMAccount.ops_tenant_id == user.tenant_id, CRMAccount.id.in_(account_ids)
        )
    )).all() if account_ids else []
    account_names: dict[UUID, str] = {account_id: name for account_id, name in account_rows}
    return [{
        "id": str(item.id),
        "account_id": str(item.account_id),
        "account_name": account_names.get(item.account_id, "Unknown account"),
        "managed_tenant_id": str(item.managed_tenant_id) if item.managed_tenant_id else None,
        "owner_user_id": str(item.owner_user_id) if item.owner_user_id else None,
        "category": item.category,
        "title": item.title,
        "status": item.status,
        "due_at": item.due_at,
        "completed_at": item.completed_at,
        "notes": item.notes,
        "sort_order": item.sort_order,
        "created_at": item.created_at,
    } for item in items]


@router.post("/crm/onboarding", status_code=201)
async def create_onboarding_item(
    payload: OnboardingItemCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id)
    await _require_owner(db, user.tenant_id, payload.owner_user_id)
    if payload.managed_tenant_id is not None and payload.managed_tenant_id != account.managed_tenant_id:
        raise HTTPException(status_code=422, detail="Onboarding tenant must belong to the CRM account")
    values = payload.model_dump()
    if payload.status == "completed":
        values["completed_at"] = datetime.now(timezone.utc)
    item = CRMOnboardingItem(ops_tenant_id=user.tenant_id, **values)
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="crm.onboarding_item.created",
        entity_type="crm_onboarding_item",
        entity_id=str(item.id),
        metadata={"account_id": str(account.id), "category": item.category},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.patch("/crm/onboarding/{item_id}")
async def update_onboarding_item(
    item_id: UUID,
    payload: OnboardingItemUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMOnboardingItem).where(
        CRMOnboardingItem.id == item_id,
        CRMOnboardingItem.ops_tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Onboarding item not found")
    if "owner_user_id" in payload.model_fields_set:
        await _require_owner(db, user.tenant_id, payload.owner_user_id)
    if "managed_tenant_id" in payload.model_fields_set and payload.managed_tenant_id is not None:
        account = await _require_account(db, user.tenant_id, item.account_id)
        if payload.managed_tenant_id != account.managed_tenant_id:
            raise HTTPException(status_code=422, detail="Onboarding tenant must belong to the CRM account")
    changed = _apply_patch(item, payload)
    if "status" in payload.model_fields_set:
        if item.status == "completed" and item.completed_at is None:
            item.completed_at = datetime.now(timezone.utc)
            if "completed_at" not in changed:
                changed.append("completed_at")
        elif item.status != "completed" and "completed_at" not in payload.model_fields_set:
            item.completed_at = None
            if "completed_at" not in changed:
                changed.append("completed_at")
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="crm.onboarding_item.updated",
        entity_type="crm_onboarding_item",
        entity_id=str(item.id),
        metadata={"changed_fields": sorted(changed)},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status, "completed_at": item.completed_at}


@router.post("/crm/accounts/{account_id}/onboarding-template", status_code=201)
async def create_standard_onboarding(
    account_id: UUID,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, account_id)
    existing_count = await db.scalar(
        select(func.count()).select_from(CRMOnboardingItem).where(
            CRMOnboardingItem.ops_tenant_id == user.tenant_id,
            CRMOnboardingItem.account_id == account.id,
        )
    )
    if existing_count:
        raise HTTPException(status_code=409, detail="Onboarding checklist already exists for this account")

    template = [
        ("commercial", "Confirm signed commercial scope and internal handoff"),
        ("tenant", "Provision and validate customer tenant"),
        ("identity", "Confirm administrator access and identity approach"),
        ("data", "Confirm people, role and organizational data readiness"),
        ("integration", "Confirm required integrations and data flows"),
        ("validation", "Complete representative workflow validation / UAT"),
        ("go_live", "Confirm go-live readiness and operating ownership"),
        ("success", "Complete customer success handoff and review cadence"),
    ]
    created_ids: list[str] = []
    for index, (category, title) in enumerate(template, start=1):
        item = CRMOnboardingItem(
            ops_tenant_id=user.tenant_id,
            account_id=account.id,
            managed_tenant_id=account.managed_tenant_id,
            owner_user_id=user.id,
            category=category,
            title=title,
            status="pending",
            sort_order=index * 10,
        )
        db.add(item)
        await db.flush()
        created_ids.append(str(item.id))

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="crm.onboarding_template.created",
        entity_type="crm_account",
        entity_id=str(account.id),
        metadata={"items": len(created_ids)},
    )
    await db.commit()
    return {"account_id": str(account.id), "items_created": len(created_ids), "item_ids": created_ids}


@router.get("/crm/renewals")
async def list_renewals(
    days: int = Query(default=90, ge=1, le=730),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=days)
    rows = (await db.execute(
        select(CRMSubscription, CRMAccount, SaaSPlan)
        .join(CRMAccount, CRMAccount.id == CRMSubscription.account_id)
        .outerjoin(SaaSPlan, SaaSPlan.id == CRMSubscription.plan_id)
        .where(
            CRMSubscription.ops_tenant_id == user.tenant_id,
            CRMSubscription.status == "active",
            CRMSubscription.renews_at.is_not(None),
            CRMSubscription.renews_at <= horizon,
        )
        .order_by(CRMSubscription.renews_at.asc())
    )).all()
    return [{
        "subscription_id": str(subscription.id),
        "account_id": str(account.id),
        "account_name": account.name,
        "plan_id": str(plan.id) if plan else None,
        "plan_name": plan.name if plan else None,
        "currency": subscription.currency,
        "net_price_minor": subscription.net_price_minor,
        "billing_cycle": subscription.billing_cycle,
        "seats": subscription.seats,
        "renews_at": subscription.renews_at,
        "contract_ref": subscription.contract_ref,
        "days_until_renewal": (
            subscription.renews_at.date() - now.date()
        ).days if subscription.renews_at else None,
    } for subscription, account, plan in rows]


@router.get("/crm/team")
async def list_crm_team(
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(User, Role)
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .outerjoin(Role, Role.id == UserRole.role_id)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.is_active.desc(), User.first_name, User.last_name, Role.name)
    )).all()
    grouped: dict[UUID, dict[str, Any]] = {}
    for member, role in rows:
        record = grouped.setdefault(member.id, {
            "id": str(member.id),
            "name": f"{member.first_name} {member.last_name}".strip(),
            "email": member.email,
            "job_title": member.job_title,
            "is_active": member.is_active,
            "roles": [],
        })
        if role is not None and role.name not in record["roles"]:
            record["roles"].append(role.name)
    return list(grouped.values())


@router.get("/crm/export/accounts.csv")
async def export_accounts_csv(
    stage: str | None = Query(default=None, max_length=30),
    q: str | None = Query(default=None, max_length=160),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMAccount).where(CRMAccount.ops_tenant_id == user.tenant_id)
    if stage:
        stmt = stmt.where(CRMAccount.lifecycle_stage == stage)
    if q and q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            CRMAccount.name.ilike(term), CRMAccount.slug.ilike(term),
            CRMAccount.industry.ilike(term), CRMAccount.country.ilike(term),
        ))
    items = (await db.execute(stmt.order_by(CRMAccount.name))).scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    def safe_cell(value: str | None) -> str:
        text = value or ""
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text

    writer.writerow([
        "name", "slug", "account_type", "lifecycle_stage", "industry", "country",
        "employee_band", "owner_user_id", "plan_id", "managed_tenant_id",
        "public_showcase", "created_at", "updated_at",
    ])
    for item in items:
        writer.writerow([
            safe_cell(item.name),
            safe_cell(item.slug),
            item.account_type,
            item.lifecycle_stage,
            safe_cell(item.industry),
            safe_cell(item.country),
            safe_cell(item.employee_band),
            str(item.owner_user_id) if item.owner_user_id else "",
            str(item.plan_id) if item.plan_id else "",
            str(item.managed_tenant_id) if item.managed_tenant_id else "",
            "yes" if item.public_showcase else "no",
            item.created_at.isoformat() if item.created_at else "",
            item.updated_at.isoformat() if item.updated_at else "",
        ])
    filename = f"kognivon-crm-accounts-{datetime.now(timezone.utc).date().isoformat()}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _require_subscription(
    db: AsyncSession, tenant_id: UUID, subscription_id: UUID | None
) -> CRMSubscription | None:
    if subscription_id is None:
        return None
    item = await db.scalar(select(CRMSubscription).where(
        CRMSubscription.id == subscription_id,
        CRMSubscription.ops_tenant_id == tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return item


async def _require_contract(
    db: AsyncSession, tenant_id: UUID, contract_id: UUID | None
) -> CRMContract | None:
    if contract_id is None:
        return None
    item = await db.scalar(select(CRMContract).where(
        CRMContract.id == contract_id,
        CRMContract.ops_tenant_id == tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return item


async def _require_invoice(db: AsyncSession, tenant_id: UUID, invoice_id: UUID) -> CRMInvoice:
    item = await db.scalar(select(CRMInvoice).where(
        CRMInvoice.id == invoice_id,
        CRMInvoice.ops_tenant_id == tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return item


async def _reconcile_invoice(db: AsyncSession, invoice: CRMInvoice) -> tuple[int, int]:
    received = await db.scalar(
        select(func.coalesce(func.sum(CRMPayment.amount_minor), 0)).where(
            CRMPayment.invoice_id == invoice.id,
            CRMPayment.ops_tenant_id == invoice.ops_tenant_id,
            CRMPayment.status == "received",
        )
    )
    paid_minor = int(received or 0)
    outstanding = max(0, invoice.total_minor - paid_minor)
    now = datetime.now(timezone.utc)

    if invoice.status == "void":
        return paid_minor, outstanding
    if outstanding == 0 and invoice.total_minor > 0:
        invoice.status = "paid"
        invoice.paid_at = invoice.paid_at or now
    elif paid_minor > 0:
        invoice.status = "partially_paid"
        invoice.paid_at = None
    elif invoice.due_at is not None and invoice.due_at < now and invoice.status != "draft":
        invoice.status = "overdue"
        invoice.paid_at = None
    elif invoice.status not in {"draft", "issued"}:
        invoice.status = "issued"
        invoice.paid_at = None
    return paid_minor, outstanding


@router.get("/crm/contracts")
async def list_contracts(
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMContract, CRMAccount)
        .join(CRMAccount, CRMAccount.id == CRMContract.account_id)
        .where(CRMContract.ops_tenant_id == user.tenant_id)
    )
    if account_id is not None:
        stmt = stmt.where(CRMContract.account_id == account_id)
    rows = (await db.execute(stmt.order_by(CRMContract.updated_at.desc()))).all()
    return [{
        "id": str(contract.id),
        "account_id": str(account.id),
        "account_name": account.name,
        "subscription_id": str(contract.subscription_id) if contract.subscription_id else None,
        "reference": contract.reference,
        "status": contract.status,
        "currency": contract.currency,
        "total_value_minor": contract.total_value_minor,
        "starts_at": contract.starts_at,
        "ends_at": contract.ends_at,
        "signed_at": contract.signed_at,
        "renewal_terms": contract.renewal_terms,
        "notes": contract.notes,
    } for contract, account in rows]


@router.get("/crm/page/contracts")
async def paged_contracts(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [CRMContract.ops_tenant_id == user.tenant_id]
    if account_id is not None:
        filters.append(CRMContract.account_id == account_id)
    if status:
        filters.append(CRMContract.status == status)
    now = datetime.now(timezone.utc)
    stats = (await db.execute(select(
        func.count(CRMContract.id),
        func.count(CRMContract.id).filter(CRMContract.status.in_(["signed", "active"])),
        func.count(CRMContract.id).filter(
            CRMContract.ends_at > now,
            CRMContract.ends_at <= now + timedelta(days=90),
        ),
        func.count(CRMContract.id).filter(CRMContract.status.in_(["draft", "review"])),
    ).where(*filters))).one()
    rows = (await db.execute(
        select(CRMContract, CRMAccount)
        .join(CRMAccount, and_(
            CRMAccount.id == CRMContract.account_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
        ))
        .where(*filters)
        .order_by(CRMContract.updated_at.desc(), CRMContract.id)
        .offset(offset).limit(limit)
    )).all()
    return {
        "total": int(stats[0]), "offset": offset, "limit": limit,
        "counts": {
            "signed_active": int(stats[1]), "expiring_90_days": int(stats[2]),
            "draft_review": int(stats[3]),
        },
        "items": [{
            "id": str(contract.id), "account_id": str(account.id),
            "account_name": account.name,
            "subscription_id": str(contract.subscription_id) if contract.subscription_id else None,
            "reference": contract.reference, "status": contract.status,
            "currency": contract.currency,
            "total_value_minor": contract.total_value_minor,
            "starts_at": contract.starts_at, "ends_at": contract.ends_at,
            "signed_at": contract.signed_at,
            "renewal_terms": contract.renewal_terms, "notes": contract.notes,
        } for contract, account in rows],
    }


@router.post("/crm/contracts", status_code=201)
async def create_contract(
    payload: ContractCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id)
    subscription = await _require_subscription(db, user.tenant_id, payload.subscription_id)
    if subscription is not None:
        if subscription.account_id != account.id:
            raise HTTPException(status_code=422, detail="Subscription does not belong to this account")
        if subscription.currency != payload.currency:
            raise HTTPException(status_code=422, detail="Contract currency must match subscription currency")
    _validate_window(payload.starts_at, payload.ends_at, "Contract")
    item = CRMContract(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    if subscription is not None:
        subscription.contract_ref = item.reference
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.contract.created", entity_type="crm_contract", entity_id=str(item.id),
        metadata={"account_id": str(account.id), "reference": item.reference},
    )
    await db.commit()
    return {"id": str(item.id), "reference": item.reference, "status": item.status}


@router.patch("/crm/contracts/{contract_id}")
async def update_contract(
    contract_id: UUID,
    payload: ContractUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await _require_contract(db, user.tenant_id, contract_id)
    assert item is not None
    future_start = payload.starts_at if "starts_at" in payload.model_fields_set else item.starts_at
    future_end = payload.ends_at if "ends_at" in payload.model_fields_set else item.ends_at
    _validate_window(future_start, future_end, "Contract")
    changed = _apply_patch(item, payload)
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.contract.updated", entity_type="crm_contract", entity_id=str(item.id),
        metadata={"changed_fields": changed},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.get("/crm/invoices")
async def list_invoices(
    status: str | None = Query(default=None, max_length=30),
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMInvoice, CRMAccount)
        .join(CRMAccount, CRMAccount.id == CRMInvoice.account_id)
        .where(CRMInvoice.ops_tenant_id == user.tenant_id)
    )
    if status:
        stmt = stmt.where(CRMInvoice.status == status)
    if account_id is not None:
        stmt = stmt.where(CRMInvoice.account_id == account_id)
    rows = (await db.execute(stmt.order_by(CRMInvoice.due_at.asc().nullslast(), CRMInvoice.created_at.desc()))).all()
    result = []
    for invoice, account in rows:
        paid_minor, outstanding_minor = await _reconcile_invoice(db, invoice)
        result.append({
            "id": str(invoice.id),
            "account_id": str(account.id),
            "account_name": account.name,
            "subscription_id": str(invoice.subscription_id) if invoice.subscription_id else None,
            "contract_id": str(invoice.contract_id) if invoice.contract_id else None,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "currency": invoice.currency,
            "amount_minor": invoice.amount_minor,
            "tax_minor": invoice.tax_minor,
            "total_minor": invoice.total_minor,
            "paid_minor": paid_minor,
            "outstanding_minor": outstanding_minor,
            "issued_at": invoice.issued_at,
            "due_at": invoice.due_at,
            "paid_at": invoice.paid_at,
            "external_ref": invoice.external_ref,
            "notes": invoice.notes,
        })
    await db.commit()
    return result


@router.post("/crm/invoices", status_code=201)
async def create_invoice(
    payload: InvoiceCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id)
    subscription = await _require_subscription(db, user.tenant_id, payload.subscription_id)
    contract = await _require_contract(db, user.tenant_id, payload.contract_id)
    if subscription is not None and subscription.account_id != account.id:
        raise HTTPException(status_code=422, detail="Subscription does not belong to this account")
    if contract is not None and contract.account_id != account.id:
        raise HTTPException(status_code=422, detail="Contract does not belong to this account")
    if subscription is not None and subscription.currency != payload.currency:
        raise HTTPException(status_code=422, detail="Invoice currency must match subscription currency")
    if contract is not None and contract.currency != payload.currency:
        raise HTTPException(status_code=422, detail="Invoice currency must match contract currency")
    if payload.issued_at is not None and payload.due_at is not None and payload.due_at < payload.issued_at:
        raise HTTPException(status_code=422, detail="Invoice due date cannot be before issue date")
    if payload.status == "issued" and payload.amount_minor + payload.tax_minor <= 0:
        raise HTTPException(status_code=422, detail="Issued invoice must have a positive total")
    values = payload.model_dump()
    values["total_minor"] = payload.amount_minor + payload.tax_minor
    item = CRMInvoice(ops_tenant_id=user.tenant_id, **values)
    db.add(item)
    await db.flush()
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.invoice.created", entity_type="crm_invoice", entity_id=str(item.id),
        metadata={"account_id": str(account.id), "invoice_number": item.invoice_number},
    )
    await db.commit()
    return {"id": str(item.id), "invoice_number": item.invoice_number, "total_minor": item.total_minor}


@router.patch("/crm/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: UUID,
    payload: InvoiceUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMInvoice).where(
        CRMInvoice.id == invoice_id, CRMInvoice.ops_tenant_id == user.tenant_id,
    ).with_for_update())
    if item is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    future_issued = payload.issued_at if "issued_at" in payload.model_fields_set else item.issued_at
    future_due = payload.due_at if "due_at" in payload.model_fields_set else item.due_at
    if future_issued is not None and future_due is not None and future_due < future_issued:
        raise HTTPException(status_code=422, detail="Invoice due date cannot be before issue date")
    paid_before, _ = await _reconcile_invoice(db, item)
    future_amount = payload.amount_minor if "amount_minor" in payload.model_fields_set else item.amount_minor
    future_tax = payload.tax_minor if "tax_minor" in payload.model_fields_set else item.tax_minor
    if future_amount is None or future_tax is None:
        raise HTTPException(status_code=422, detail="Invoice amount and tax are required")
    if future_amount + future_tax < paid_before:
        raise HTTPException(status_code=422, detail="Invoice total cannot be less than payments received")
    if payload.status == "void" and paid_before > 0:
        raise HTTPException(status_code=422, detail="An invoice with received payments cannot be voided")
    if payload.status == "draft" and paid_before > 0:
        raise HTTPException(status_code=422, detail="An invoice with received payments cannot return to draft")
    if (payload.status or item.status) == "issued" and future_amount + future_tax <= 0:
        raise HTTPException(status_code=422, detail="Issued invoice must have a positive total")
    changed = _apply_patch(item, payload)
    item.total_minor = item.amount_minor + item.tax_minor
    if "total_minor" not in changed:
        changed.append("total_minor")
    paid_minor, outstanding_minor = await _reconcile_invoice(db, item)
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.invoice.updated", entity_type="crm_invoice", entity_id=str(item.id),
        metadata={"changed_fields": changed},
    )
    await db.commit()
    return {
        "id": str(item.id),
        "status": item.status,
        "total_minor": item.total_minor,
        "paid_minor": paid_minor,
        "outstanding_minor": outstanding_minor,
    }


@router.get("/crm/payments")
async def list_payments(
    invoice_id: UUID | None = Query(default=None),
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMPayment, CRMAccount, CRMInvoice)
        .join(CRMAccount, CRMAccount.id == CRMPayment.account_id)
        .join(CRMInvoice, CRMInvoice.id == CRMPayment.invoice_id)
        .where(CRMPayment.ops_tenant_id == user.tenant_id)
    )
    if invoice_id is not None:
        stmt = stmt.where(CRMPayment.invoice_id == invoice_id)
    if account_id is not None:
        stmt = stmt.where(CRMPayment.account_id == account_id)
    rows = (await db.execute(stmt.order_by(CRMPayment.received_at.desc()))).all()
    return [{
        "id": str(payment.id),
        "account_id": str(account.id),
        "account_name": account.name,
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "amount_minor": payment.amount_minor,
        "currency": payment.currency,
        "status": payment.status,
        "received_at": payment.received_at,
        "method": payment.method,
        "reference": payment.reference,
        "notes": payment.notes,
    } for payment, account, invoice in rows]


@router.post("/crm/payments", status_code=201)
async def create_payment(
    payload: PaymentCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    invoice = await db.scalar(select(CRMInvoice).where(
        CRMInvoice.id == payload.invoice_id, CRMInvoice.ops_tenant_id == user.tenant_id,
    ).with_for_update())
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.currency != payload.currency:
        raise HTTPException(status_code=422, detail="Payment currency must match invoice currency")
    if invoice.status in {"void", "draft"}:
        raise HTTPException(status_code=422, detail="Issue the invoice before recording a payment")
    existing_paid, outstanding = await _reconcile_invoice(db, invoice)
    if payload.status == "received" and payload.amount_minor > outstanding:
        raise HTTPException(status_code=422, detail="Payment exceeds outstanding invoice balance")
    item = CRMPayment(
        ops_tenant_id=user.tenant_id,
        account_id=invoice.account_id,
        invoice_id=invoice.id,
        received_at=payload.received_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"received_at", "invoice_id"}),
    )
    db.add(item)
    await db.flush()
    paid_minor, outstanding_minor = await _reconcile_invoice(db, invoice)
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.payment.created", entity_type="crm_payment", entity_id=str(item.id),
        metadata={
            "invoice_id": str(invoice.id),
            "amount_minor": item.amount_minor,
            "currency": item.currency,
            "previous_paid_minor": existing_paid,
        },
    )
    await db.commit()
    return {
        "id": str(item.id),
        "invoice_id": str(invoice.id),
        "invoice_status": invoice.status,
        "paid_minor": paid_minor,
        "outstanding_minor": outstanding_minor,
    }


@router.get("/crm/forecast")
async def commercial_forecast(
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    opportunity_rows = (await db.execute(
        select(
            CRMOpportunity.currency,
            CRMOpportunity.stage,
            func.coalesce(func.sum(CRMOpportunity.amount_minor), 0),
            func.coalesce(func.sum(CRMOpportunity.amount_minor * CRMOpportunity.probability_percent / 100.0), 0),
            func.count(CRMOpportunity.id),
        )
        .where(
            CRMOpportunity.ops_tenant_id == user.tenant_id,
            CRMOpportunity.stage.notin_(["won", "lost"]),
        )
        .group_by(CRMOpportunity.currency, CRMOpportunity.stage)
        .order_by(CRMOpportunity.currency, CRMOpportunity.stage)
    )).all()

    open_invoices = (await db.execute(
        select(CRMInvoice)
        .where(
            CRMInvoice.ops_tenant_id == user.tenant_id,
            CRMInvoice.status.in_(["issued", "partially_paid", "overdue"]),
        )
        .order_by(CRMInvoice.currency, CRMInvoice.due_at.asc().nullslast())
    )).scalars().all()
    receivables: dict[str, dict[str, int]] = {}
    for invoice in open_invoices:
        _, outstanding = await _reconcile_invoice(db, invoice)
        if outstanding <= 0:
            continue
        bucket = receivables.setdefault(invoice.currency, {"outstanding_minor": 0, "invoices": 0})
        bucket["outstanding_minor"] += outstanding
        bucket["invoices"] += 1
    await db.commit()

    return {
        "pipeline": [{
            "currency": currency,
            "stage": stage,
            "gross_minor": int(gross or 0),
            "weighted_minor": int(weighted or 0),
            "opportunities": int(count or 0),
        } for currency, stage, gross, weighted, count in opportunity_rows],
        "open_invoices": [{
            "currency": currency,
            "outstanding_minor": values["outstanding_minor"],
            "invoices": values["invoices"],
        } for currency, values in sorted(receivables.items())],
    }


@router.patch("/crm/payments/{payment_id}")
async def update_payment(
    payment_id: UUID,
    payload: PaymentUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMPayment).where(
        CRMPayment.id == payment_id,
        CRMPayment.ops_tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    invoice = await db.scalar(select(CRMInvoice).where(
        CRMInvoice.id == item.invoice_id, CRMInvoice.ops_tenant_id == user.tenant_id,
    ).with_for_update())
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if "status" in payload.model_fields_set and payload.status not in {"received", "reversed"}:
        raise HTTPException(status_code=422, detail="Payment status must be received or reversed")
    if payload.status == "received" and item.status != "received":
        if invoice.status in {"void", "draft"}:
            raise HTTPException(status_code=422, detail="Cannot restore payment on an unissued or void invoice")
        _, outstanding = await _reconcile_invoice(db, invoice)
        if item.amount_minor > outstanding:
            raise HTTPException(status_code=422, detail="Reactivated payment exceeds outstanding invoice balance")

    changed = _apply_patch(item, payload)
    paid_minor, outstanding_minor = await _reconcile_invoice(db, invoice)
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.payment.updated", entity_type="crm_payment", entity_id=str(item.id),
        metadata={"changed_fields": changed, "invoice_id": str(invoice.id)},
    )
    await db.commit()
    return {
        "id": str(item.id),
        "status": item.status,
        "invoice_id": str(invoice.id),
        "invoice_status": invoice.status,
        "paid_minor": paid_minor,
        "outstanding_minor": outstanding_minor,
    }


@router.get("/crm/tasks")
async def list_crm_tasks(
    status: str | None = Query(default=None, max_length=30),
    task_type: str | None = Query(default=None, max_length=50),
    owner_user_id: UUID | None = Query(default=None),
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMTask, CRMAccount, CRMSubscription)
        .outerjoin(CRMAccount, CRMAccount.id == CRMTask.account_id)
        .outerjoin(CRMSubscription, CRMSubscription.id == CRMTask.subscription_id)
        .where(CRMTask.ops_tenant_id == user.tenant_id)
    )
    if status:
        stmt = stmt.where(CRMTask.status == status)
    if task_type:
        stmt = stmt.where(CRMTask.task_type == task_type)
    if owner_user_id is not None:
        stmt = stmt.where(CRMTask.owner_user_id == owner_user_id)
    if account_id is not None:
        stmt = stmt.where(CRMTask.account_id == account_id)
    rows = (await db.execute(
        stmt.order_by(
            CRMTask.status,
            CRMTask.due_at.asc().nullslast(),
            CRMTask.priority.desc(),
            CRMTask.created_at.desc(),
        )
    )).all()
    return [{
        "id": str(task.id),
        "account_id": str(task.account_id) if task.account_id else None,
        "account_name": account.name if account else None,
        "subscription_id": str(task.subscription_id) if task.subscription_id else None,
        "owner_user_id": str(task.owner_user_id) if task.owner_user_id else None,
        "task_type": task.task_type,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_at": task.due_at,
        "completed_at": task.completed_at,
        "source_key": task.source_key,
        "created_at": task.created_at,
    } for task, account, subscription in rows]


@router.get("/crm/page/tasks")
async def paged_crm_tasks(
    status: str | None = Query(default=None, max_length=30),
    task_type: str | None = Query(default=None, max_length=50),
    owner_user_id: UUID | None = Query(default=None),
    account_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [CRMTask.ops_tenant_id == user.tenant_id]
    if status:
        filters.append(CRMTask.status == status)
    if task_type:
        filters.append(CRMTask.task_type == task_type)
    if owner_user_id is not None:
        filters.append(CRMTask.owner_user_id == owner_user_id)
    if account_id is not None:
        filters.append(CRMTask.account_id == account_id)
    now = datetime.now(timezone.utc)
    open_status = CRMTask.status.in_(["open", "in_progress", "blocked"])
    stats = (await db.execute(select(
        func.count(CRMTask.id),
        func.count(CRMTask.id).filter(open_status),
        func.count(CRMTask.id).filter(
            CRMTask.status != "completed", CRMTask.due_at < now,
        ),
        func.count(CRMTask.id).filter(
            CRMTask.status != "completed",
            CRMTask.due_at >= now,
            CRMTask.due_at <= now + timedelta(days=7),
        ),
        func.count(CRMTask.id).filter(CRMTask.status == "completed"),
    ).where(*filters))).one()
    rows = (await db.execute(
        select(CRMTask, CRMAccount)
        .outerjoin(CRMAccount, and_(
            CRMAccount.id == CRMTask.account_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
        ))
        .where(*filters)
        .order_by(
            CRMTask.status, CRMTask.due_at.asc().nullslast(),
            CRMTask.priority.desc(), CRMTask.created_at.desc(), CRMTask.id,
        ).offset(offset).limit(limit)
    )).all()
    return {
        "total": int(stats[0]), "offset": offset, "limit": limit,
        "counts": {
            "open": int(stats[1]), "overdue": int(stats[2]),
            "due_soon": int(stats[3]), "completed": int(stats[4]),
        },
        "items": [{
            "id": str(task.id),
            "account_id": str(task.account_id) if task.account_id else None,
            "account_name": account.name if account else None,
            "subscription_id": str(task.subscription_id) if task.subscription_id else None,
            "owner_user_id": str(task.owner_user_id) if task.owner_user_id else None,
            "task_type": task.task_type, "title": task.title,
            "description": task.description, "status": task.status,
            "priority": task.priority, "due_at": task.due_at,
            "completed_at": task.completed_at, "source_key": task.source_key,
            "created_at": task.created_at,
        } for task, account in rows],
    }


@router.post("/crm/tasks", status_code=201)
async def create_crm_task(
    payload: TaskCreate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    account = await _require_account(db, user.tenant_id, payload.account_id) if payload.account_id else None
    subscription = await _require_subscription(db, user.tenant_id, payload.subscription_id)
    await _require_owner(db, user.tenant_id, payload.owner_user_id)
    if subscription is not None:
        if account is not None and subscription.account_id != account.id:
            raise HTTPException(status_code=422, detail="Subscription does not belong to this account")
        if account is None:
            account = await _require_account(db, user.tenant_id, subscription.account_id)
    values = payload.model_dump()
    values["account_id"] = account.id if account else None
    if payload.status == "completed":
        values["completed_at"] = datetime.now(timezone.utc)
    item = CRMTask(ops_tenant_id=user.tenant_id, **values)
    db.add(item)
    await db.flush()
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.task.created", entity_type="crm_task", entity_id=str(item.id),
        metadata={"task_type": item.task_type, "account_id": str(item.account_id) if item.account_id else None},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.patch("/crm/tasks/{task_id}")
async def update_crm_task(
    task_id: UUID,
    payload: TaskUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMTask).where(
        CRMTask.id == task_id,
        CRMTask.ops_tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="CRM task not found")
    if "owner_user_id" in payload.model_fields_set:
        await _require_owner(db, user.tenant_id, payload.owner_user_id)
    changed = _apply_patch(item, payload)
    if "status" in payload.model_fields_set:
        if item.status == "completed" and item.completed_at is None:
            item.completed_at = datetime.now(timezone.utc)
            if "completed_at" not in changed:
                changed.append("completed_at")
        elif item.status != "completed" and "completed_at" not in payload.model_fields_set:
            item.completed_at = None
            if "completed_at" not in changed:
                changed.append("completed_at")
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.task.updated", entity_type="crm_task", entity_id=str(item.id),
        metadata={"changed_fields": sorted(changed)},
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status, "completed_at": item.completed_at}


@router.post("/crm/tasks/generate-renewals")
async def generate_renewal_tasks(
    horizon_days: int = Query(default=120, ge=30, le=365),
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    result = await reconcile_renewal_tasks(db, user.tenant_id, horizon_days)
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="crm.renewal_tasks.generated", entity_type="crm_task",
        entity_id="bulk",
        metadata={"horizon_days": horizon_days, **result},
    )
    await db.commit()
    return result
