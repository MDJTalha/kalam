from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_platform_developer, is_saas_ops_user, is_saas_super_admin, require_permission, user_has_permission
from app.db.models import OrgUnit, Role, User, UserRole
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

BASIC_ASSIGNABLE_TENANT_ROLES = {
    "manager",
    "instructor",
    "learner / employee",
    "employee / learner",
}
ASSIGNABLE_SAAS_TEAM_ROLES = {
    "sales operations",
    "sales viewer",
    "saas finance administrator",
    "customer success manager",
}

async def _is_platform_developer(user: User, db: AsyncSession) -> bool:
    return await is_platform_developer(user, db)

class OrgUnitCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    unit_type: Literal["business_unit", "department", "location", "team"] = "department"
    code: str | None = Field(default=None, max_length=80)
    parent_id: UUID | None = None

class OrgUnitUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    unit_type: Literal["business_unit", "department", "location", "team"]
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
    role_kind: str
    model_config = {"from_attributes": True}

async def _require_organization_metadata(user: User, db: AsyncSession) -> None:
    if not (
        await user_has_permission(user, db, "users.read")
        or await user_has_permission(user, db, "organization.read")
    ):
        raise HTTPException(status_code=403, detail="Organization metadata access is restricted")


@router.get("/units", response_model=list[OrgUnitOut])
async def list_units(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_organization_metadata(user, db)
    result = await db.execute(
        select(OrgUnit)
        .where(OrgUnit.tenant_id == user.tenant_id)
        .order_by(OrgUnit.unit_type, OrgUnit.name)
    )
    return list(result.scalars().all())


@router.get("/units/summary")
async def organization_unit_summary(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """Return the tenant's hierarchy with direct active-member counts, not a people dump."""
    rows = await db.execute(
        select(OrgUnit, func.count(User.id).label("member_count"))
        .outerjoin(User, and_(
            User.org_unit_id == OrgUnit.id,
            User.tenant_id == user.tenant_id,
            User.is_active.is_(True),
        ))
        .where(OrgUnit.tenant_id == user.tenant_id)
        .group_by(OrgUnit.id)
        .order_by(OrgUnit.unit_type, OrgUnit.name)
    )
    units = [{
        "id": str(unit.id), "name": unit.name, "unit_type": unit.unit_type,
        "code": unit.code, "parent_id": str(unit.parent_id) if unit.parent_id else None,
        "member_count": int(member_count),
    } for unit, member_count in rows.all()]
    active_total = int(await db.scalar(select(func.count()).select_from(User).where(
        User.tenant_id == user.tenant_id, User.is_active.is_(True)
    )) or 0)
    assigned_total = sum(unit["member_count"] for unit in units)
    return {"units": units, "active_people": active_total, "assigned_people": assigned_total,
            "unassigned_people": max(0, active_total - assigned_total)}

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
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Unit name is too short")
    duplicate = await db.scalar(select(OrgUnit.id).where(
        OrgUnit.tenant_id == user.tenant_id,
        OrgUnit.parent_id == payload.parent_id,
        func.lower(OrgUnit.name) == name.lower(),
    ))
    if duplicate:
        raise HTTPException(status_code=409, detail="A unit with this name already exists under the selected parent")
    unit = OrgUnit(tenant_id=user.tenant_id, **{**payload.model_dump(), "name": name})
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

@router.get("/roles/catalog", response_model=list[RoleOut])
async def list_role_catalog(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Read role names for policy targeting without exposing user-role assignments."""
    await _require_organization_metadata(user, db)
    result = await db.execute(
        select(Role)
        .where(
            Role.tenant_id == user.tenant_id,
            Role.role_kind.in_(("predefined", "custom", "legacy")),
        )
        .order_by(Role.name)
    )
    return list(result.scalars().all())


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Role).where(Role.tenant_id == user.tenant_id)
    is_developer = await _is_platform_developer(user, db)
    is_super_admin = await is_saas_super_admin(user, db)
    is_ops_user = await is_saas_ops_user(user, db)
    can_manage_roles = await user_has_permission(user, db, "tenant.manage")
    can_manage_saas_team = is_ops_user and await user_has_permission(user, db, "saas.team.manage")
    if not is_developer and not is_super_admin and not can_manage_saas_team:
        stmt = stmt.where(Role.role_kind.in_(["predefined", "custom"]))
    if can_manage_saas_team and not is_super_admin and not is_developer:
        stmt = stmt.where(
            (Role.role_kind.in_(["predefined", "custom"]))
            | (
                (Role.role_kind == "platform")
                & func.lower(Role.name).in_(ASSIGNABLE_SAAS_TEAM_ROLES)
            )
        )
    elif not can_manage_roles:
        stmt = stmt.where(
            Role.role_kind == "predefined",
            func.lower(Role.name).in_(BASIC_ASSIGNABLE_TENANT_ROLES),
        )
    result = await db.execute(stmt.order_by(Role.name))
    return list(result.scalars().all())

@router.get("/users/{user_id}/roles", response_model=list[RoleOut])
async def list_user_roles(
    user_id: UUID,
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(select(User.id).where(User.id == user_id, User.tenant_id == user.tenant_id))
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.tenant_id == user.tenant_id)
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
    is_developer = await _is_platform_developer(user, db)
    is_super_admin = await is_saas_super_admin(user, db) and await is_saas_ops_user(user, db)
    can_manage_roles = await user_has_permission(user, db, "tenant.manage")
    can_manage_saas_team = (
        await is_saas_ops_user(user, db)
        and await user_has_permission(user, db, "saas.team.manage")
    )
    if role.role_kind not in ("predefined", "custom"):
        role_name = role.name.strip().lower()
        can_assign_platform_role = (
            is_developer
            or (
                is_super_admin
                and role_name != "platform developer"
            )
            or (
                can_manage_saas_team
                and role.role_kind == "platform"
                and role_name in ASSIGNABLE_SAAS_TEAM_ROLES
            )
        )
        if not can_assign_platform_role:
            raise HTTPException(status_code=403, detail="This platform role cannot be assigned by your SaaS team role")
    elif not can_manage_roles and not (
        role.role_kind == "predefined" and role.name.strip().lower() in BASIC_ASSIGNABLE_TENANT_ROLES
    ):
        raise HTTPException(status_code=403, detail="Assigning administrative or custom roles requires tenant administration permission")
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

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == user.tenant_id))
    role = await db.scalar(select(Role).where(Role.id == role_id, Role.tenant_id == user.tenant_id))
    if target is None or role is None:
        raise HTTPException(status_code=404, detail="User or role not found")
    if target.id == user.id:
        raise HTTPException(status_code=422, detail="You cannot remove a role from your own account")
    is_developer = await _is_platform_developer(user, db)
    is_super_admin = await is_saas_super_admin(user, db) and await is_saas_ops_user(user, db)
    can_manage_roles = await user_has_permission(user, db, "tenant.manage")
    can_manage_saas_team = (
        await is_saas_ops_user(user, db)
        and await user_has_permission(user, db, "saas.team.manage")
    )
    if role.role_kind not in ("predefined", "custom"):
        role_name = role.name.strip().lower()
        can_remove_platform_role = (
            is_developer
            or (
                is_super_admin
                and role_name != "platform developer"
            )
            or (
                can_manage_saas_team
                and role.role_kind == "platform"
                and role_name in ASSIGNABLE_SAAS_TEAM_ROLES
            )
        )
        if not can_remove_platform_role:
            raise HTTPException(status_code=403, detail="This platform role cannot be removed by your SaaS team role")
    elif not can_manage_roles and not (
        role.role_kind == "predefined" and role.name.strip().lower() in BASIC_ASSIGNABLE_TENANT_ROLES
    ):
        raise HTTPException(status_code=403, detail="Removing administrative or custom roles requires tenant administration permission")
    assignment = await db.scalar(select(UserRole).where(UserRole.user_id == target.id, UserRole.role_id == role.id))
    if assignment is None:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    if role.name.strip().lower() in {"tenant owner", "tenant administrator", "tenant admin"} and target.is_active:
        target_retains_admin_role = await db.scalar(
            select(UserRole.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == target.id)
            .where(Role.tenant_id == user.tenant_id)
            .where(Role.id != role.id)
            .where(func.lower(Role.name).in_(("tenant owner", "tenant administrator", "tenant admin")))
            .limit(1)
        )
        if target_retains_admin_role is None:
            another_active_tenant_admin = await db.scalar(
                select(User.id)
                .join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(User.tenant_id == user.tenant_id)
                .where(User.is_active.is_(True))
                .where(User.id != target.id)
                .where(Role.tenant_id == user.tenant_id)
                .where(func.lower(Role.name).in_(("tenant owner", "tenant administrator", "tenant admin")))
                .limit(1)
            )
            if another_active_tenant_admin is None:
                raise HTTPException(status_code=409, detail="The last active Tenant Owner or Administrator role cannot be removed")
    if role.name.strip().lower() == "saas super admin":
        remaining = await db.scalar(
            select(func.count())
            .select_from(UserRole)
            .join(User, User.id == UserRole.user_id)
            .where(UserRole.role_id == role.id)
            .where(UserRole.user_id != target.id)
            .where(User.is_active.is_(True))
        )
        if not remaining:
            raise HTTPException(status_code=409, detail="The last active SaaS Super Admin cannot be removed")
    await db.delete(assignment)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="user.role.removed",
                entity_type="user_role", entity_id=str(target.id), metadata={"role_id": str(role.id)})
    await db.commit()
    return {"status": "removed"}

@router.patch("/units/{unit_id}", response_model=OrgUnitOut)
async def update_unit(
    unit_id: UUID,
    payload: OrgUnitUpdate,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    unit = await db.scalar(select(OrgUnit).where(OrgUnit.id == unit_id, OrgUnit.tenant_id == user.tenant_id))
    if unit is None:
        raise HTTPException(status_code=404, detail="Organization unit not found")
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Unit name is too short")
    if payload.parent_id == unit.id:
        raise HTTPException(status_code=422, detail="A unit cannot be its own parent")
    cursor = payload.parent_id
    visited = {unit.id}
    while cursor:
        if cursor in visited:
            raise HTTPException(status_code=422, detail="Organization hierarchy cannot contain a cycle")
        visited.add(cursor)
        parent = await db.scalar(select(OrgUnit).where(OrgUnit.id == cursor, OrgUnit.tenant_id == user.tenant_id))
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent organizational unit not found")
        cursor = parent.parent_id
    duplicate = await db.scalar(select(OrgUnit.id).where(
        OrgUnit.tenant_id == user.tenant_id,
        OrgUnit.id != unit.id,
        OrgUnit.parent_id == payload.parent_id,
        func.lower(OrgUnit.name) == name.lower(),
    ))
    if duplicate:
        raise HTTPException(status_code=409, detail="A unit with this name already exists under the selected parent")
    before = {"name": unit.name, "unit_type": unit.unit_type, "code": unit.code, "parent_id": str(unit.parent_id) if unit.parent_id else None}
    unit.name = name
    unit.unit_type = payload.unit_type
    unit.code = payload.code.strip() or None if payload.code else None
    unit.parent_id = payload.parent_id
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="org_unit.updated", entity_type="org_unit", entity_id=str(unit.id),
        metadata={"before": before, "after": {"name": unit.name, "unit_type": unit.unit_type, "code": unit.code, "parent_id": str(unit.parent_id) if unit.parent_id else None}},
    )
    await db.commit()
    await db.refresh(unit)
    return unit

@router.delete("/units/{unit_id}")
async def delete_unit(
    unit_id: UUID,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    unit = await db.scalar(select(OrgUnit).where(OrgUnit.id == unit_id, OrgUnit.tenant_id == user.tenant_id))
    if unit is None:
        raise HTTPException(status_code=404, detail="Organization unit not found")
    child = await db.scalar(select(OrgUnit.id).where(OrgUnit.tenant_id == user.tenant_id, OrgUnit.parent_id == unit.id))
    member = await db.scalar(select(User.id).where(User.tenant_id == user.tenant_id, User.org_unit_id == unit.id))
    if child or member:
        raise HTTPException(status_code=409, detail="Move child units and people before deleting this unit")
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="org_unit.deleted", entity_type="org_unit", entity_id=str(unit.id),
        metadata={"name": unit.name, "unit_type": unit.unit_type},
    )
    await db.delete(unit)
    await db.commit()
    return {"status": "deleted"}
