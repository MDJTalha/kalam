from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import OrgUnit, Role, User, UserRole
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class OrgUnitCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    unit_type: str = Field(default="department", min_length=2, max_length=40)
    code: str | None = Field(default=None, max_length=80)
    parent_id: UUID | None = None

class OrgUnitOut(BaseModel):
    id: UUID
    name: str
    unit_type: str
    code: str | None
    parent_id: UUID | None
    model_config = {"from_attributes": True}

class RoleOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_config = {"from_attributes": True}

@router.get("/units", response_model=list[OrgUnitOut])
async def list_units(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgUnit)
        .where(OrgUnit.tenant_id == user.tenant_id)
        .order_by(OrgUnit.unit_type, OrgUnit.name)
    )
    return list(result.scalars().all())

@router.post("/units", response_model=OrgUnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: OrgUnitCreate,
    user: User = Depends(require_permission("users.manage")),
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
            raise HTTPException(status_code=404, detail="Parent organizational unit not found")
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
    await db.refresh(unit)
    return unit

@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Role)
        .where(Role.tenant_id == user.tenant_id)
        .order_by(Role.name)
    )
    return list(result.scalars().all())

@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_201_CREATED)
async def assign_role(
    user_id: UUID,
    role_id: UUID,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(
        select(User).where(User.id == user_id, User.tenant_id == user.tenant_id)
    )
    role = await db.scalar(
        select(Role).where(Role.id == role_id, Role.tenant_id == user.tenant_id)
    )
    if target is None or role is None:
        raise HTTPException(status_code=404, detail="User or role not found")
    existing = await db.scalar(
        select(UserRole).where(
            UserRole.user_id == target.id,
            UserRole.role_id == role.id,
        )
    )
    if existing:
        return {"status": "already_assigned"}
    db.add(UserRole(user_id=target.id, role_id=role.id))
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="user.role.assigned",
        entity_type="user_role",
        entity_id=str(target.id),
        metadata={"role_id": str(role.id)},
    )
    await db.commit()
    return {"status": "assigned"}
