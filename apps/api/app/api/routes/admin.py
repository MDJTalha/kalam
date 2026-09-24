from datetime import timedelta
from typing import Any
from secrets import token_urlsafe
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.core.security import session_token_hash, utcnow
from app.db.models import AuditLog, Invitation, OrgUnit, Role, Tenant, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.email import send_email

router = APIRouter()

class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: UUID
    expiry_days: int = Field(default=7, ge=1, le=30)

class OrgUnitCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    unit_type: str = Field(default="department", min_length=2, max_length=40)
    code: str | None = Field(default=None, max_length=80)
    parent_id: UUID | None = None

class TenantSettingsUpdate(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)

class UserUpdate(BaseModel):
    unlock_now: bool = False
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    employee_number: str | None = Field(default=None, max_length=80)
    job_title: str | None = Field(default=None, max_length=160)
    manager_id: UUID | None = None
    org_unit_id: UUID | None = None
    is_active: bool | None = None

@router.get("/tenant-settings")
async def get_tenant_settings(
    user: User = Depends(require_permission("tenant.read")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "settings": tenant.settings,
    }


@router.patch("/tenant-settings")
async def update_tenant_settings(
    payload: TenantSettingsUpdate,
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.settings = payload.settings
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="tenant.settings.updated",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={"keys": sorted(payload.settings.keys())},
    )
    await db.commit()
    return {"status": "updated", "settings": tenant.settings}


@router.get("/roles")
async def roles(user: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Role.id, Role.name, Role.description)
        .where(Role.tenant_id == user.tenant_id)
        .order_by(Role.name)
    )
    return [{"id": str(row.id), "name": row.name, "description": row.description} for row in result.all()]

@router.post("/invitations", status_code=201)
async def create_invitation(
    payload: InvitationCreate,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    role = await db.scalar(
        select(Role).where(Role.id == payload.role_id, Role.tenant_id == user.tenant_id)
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    existing = await db.scalar(
        select(User).where(User.tenant_id == user.tenant_id, User.email == str(payload.email).lower())
    )
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    raw_token = token_urlsafe(36)
    invitation = Invitation(
        tenant_id=user.tenant_id,
        email=str(payload.email).lower(),
        role_id=role.id,
        token_hash=session_token_hash(raw_token),
        expires_at=utcnow() + timedelta(days=payload.expiry_days),
    )
    db.add(invitation)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="user.invitation.created",
        entity_type="invitation",
        entity_id=str(invitation.id),
    )
    await db.commit()

    send_email(
        recipient=invitation.email,
        subject="Corporate LMS invitation",
        text=f"Invitation token: {raw_token}",
    )
    return {"id": str(invitation.id), "status": "sent"}

@router.get("/org-units")
async def list_org_units(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgUnit)
        .where(OrgUnit.tenant_id == user.tenant_id)
        .order_by(OrgUnit.name)
    )
    return [
        {
            "id": str(unit.id),
            "name": unit.name,
            "unit_type": unit.unit_type,
            "code": unit.code,
            "parent_id": str(unit.parent_id) if unit.parent_id else None,
        }
        for unit in result.scalars().all()
    ]

@router.post("/org-units", status_code=201)
async def create_org_unit(
    payload: OrgUnitCreate,
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
):
    if payload.parent_id:
        parent = await db.scalar(
            select(OrgUnit).where(
                OrgUnit.id == payload.parent_id,
                OrgUnit.tenant_id == user.tenant_id,
            )
        )
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent organization unit not found")

    unit = OrgUnit(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(unit)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="org_unit.created",
        entity_type="org_unit",
        entity_id=str(unit.id),
    )
    await db.commit()
    return {"id": str(unit.id), "name": unit.name}

@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    admin: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(
        select(User).where(User.id == user_id, User.tenant_id == admin.tenant_id)
    )
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.manager_id is not None:
        manager = await db.scalar(
            select(User).where(
                User.id == payload.manager_id,
                User.tenant_id == admin.tenant_id,
                User.is_active.is_(True),
            )
        )
        if manager is None:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager.id == target.id:
            raise HTTPException(status_code=422, detail="A user cannot manage themselves")
        target.manager_id = manager.id
    elif "manager_id" in payload.model_fields_set:
        target.manager_id = None

    if payload.org_unit_id is not None:
        unit = await db.scalar(
            select(OrgUnit).where(
                OrgUnit.id == payload.org_unit_id,
                OrgUnit.tenant_id == admin.tenant_id,
            )
        )
        if unit is None:
            raise HTTPException(status_code=404, detail="Organization unit not found")
        target.org_unit_id = unit.id
    elif "org_unit_id" in payload.model_fields_set:
        target.org_unit_id = None

    for field in ("first_name", "last_name", "employee_number", "job_title", "is_active"):
        value = getattr(payload, field)
        if field in payload.model_fields_set:
            setattr(target, field, value)

    if payload.unlock_now:
        target.failed_login_count = 0
        target.locked_until = None

    await audit(
        db,
        tenant_id=admin.tenant_id,
        actor_id=admin.id,
        action="user.updated",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"changed_fields": sorted(payload.model_fields_set)},
    )
    await db.commit()
    return {
        "id": str(target.id),
        "email": target.email,
        "manager_id": str(target.manager_id) if target.manager_id else None,
        "org_unit_id": str(target.org_unit_id) if target.org_unit_id else None,
        "is_active": target.is_active,
    }


@router.get("/audit")
async def audit_logs(
    user: User = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == user.tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(item.id),
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "actor_id": str(item.actor_id) if item.actor_id else None,
            "request_id": item.request_id,
            "summary": item.summary,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]
