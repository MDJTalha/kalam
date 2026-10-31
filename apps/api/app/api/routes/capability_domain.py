from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import (
    Capability,
    CapabilityCompetency,
    Competency,
    CompetencyLevel,
    OrgUnit,
    ProficiencyLevel,
    Role,
    RoleRequirement,
    Skill,
    StrategicObjective,
    StrategicObjectiveCapability,
    User,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


class ObjectivePayload(BaseModel):
    objective: str = Field(min_length=3, max_length=240)
    description: str | None = None
    owner_id: UUID | None = None
    business_unit_id: UUID | None = None
    priority: int = Field(default=3, ge=1, le=5)
    strategic_category: str | None = Field(default=None, max_length=120)
    status: str = Field(default="draft", pattern="^(draft|active|closed|retired)$")
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class ObjectiveCapabilityPayload(BaseModel):
    capability_id: UUID
    required_level: int = Field(default=3, ge=1, le=5)
    weight: int = Field(default=1, ge=1, le=100)


class CompetencyPayload(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    definition: str = Field(min_length=10)
    type: str = Field(default="behavioral", pattern="^(behavioral|functional|technical|leadership|other)$")
    status: str = Field(default="draft", pattern="^(draft|active|retired)$")
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class CompetencyLevelPayload(BaseModel):
    level: int = Field(ge=1, le=5)
    definition: str = Field(min_length=3)
    behavioral_indicators: list[str] = Field(default_factory=list)


class CapabilityCompetencyPayload(BaseModel):
    competency_id: UUID
    weight: int = Field(default=1, ge=1, le=100)


class RoleRequirementPayload(BaseModel):
    target_type: str = Field(pattern="^(capability|competency|skill)$")
    target_id: UUID
    required_level: int = Field(ge=1, le=5)
    criticality: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    weight: int = Field(default=1, ge=1, le=100)
    effective_from: datetime | None = None
    effective_to: datetime | None = None


async def _user(db, tenant_id, user_id):
    if user_id is None:
        return None
    item = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True)))
    if item is None:
        raise HTTPException(422, "Owner not found")
    return item


async def _role(db, tenant_id, role_id):
    item = await db.scalar(select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id))
    if item is None:
        raise HTTPException(422, "Role not found")
    return item


def _objective_json(item):
    return {
        "id": str(item.id),
        "objective": item.objective,
        "description": item.description,
        "owner_id": str(item.owner_id) if item.owner_id else None,
        "business_unit_id": str(item.business_unit_id) if item.business_unit_id else None,
        "priority": item.priority,
        "strategic_category": item.strategic_category,
        "status": item.status,
        "effective_from": item.effective_from,
        "effective_to": item.effective_to,
    }


def _validate_effective_window(effective_from: datetime | None, effective_to: datetime | None) -> None:
    if effective_to and effective_from and effective_to <= effective_from:
        raise HTTPException(422, "Effective end must be after effective start")


def _window_overlaps(existing_from: datetime | None, existing_to: datetime | None, new_from: datetime | None, new_to: datetime | None) -> bool:
    # Open-ended intervals are treated as unbounded on that side.
    return (existing_to is None or new_from is None or existing_to >= new_from) and (new_to is None or existing_from is None or new_to >= existing_from)


def _competency_json(item, levels):
    return {
        "id": str(item.id),
        "code": item.code,
        "name": item.name,
        "definition": item.definition,
        "type": item.type,
        "status": item.status,
        "effective_from": item.effective_from,
        "effective_to": item.effective_to,
        "levels": [
            {"level": x.level, "definition": x.definition, "behavioral_indicators": x.behavioral_indicators}
            for x in levels
        ],
    }


@router.get("/proficiency-levels")
async def list_proficiency_levels(
    user: User = Depends(require_permission("competencies.read")),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(select(ProficiencyLevel).where(ProficiencyLevel.tenant_id == user.tenant_id).order_by(ProficiencyLevel.level))
    return [{"level": x.level, "name": x.name, "definition": x.definition} for x in rows.scalars()]


@router.get("/objectives/page")
async def page_objectives(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    q: str = Query(default="", max_length=160),
    status: str | None = Query(default=None),
    user: User = Depends(require_permission("strategic_objectives.read")),
    db: AsyncSession = Depends(get_db),
):
    conditions = [StrategicObjective.tenant_id == user.tenant_id]
    term = q.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions.append(StrategicObjective.objective.ilike(f"%{escaped}%", escape="\\"))
    if status:
        conditions.append(StrategicObjective.status == status)
    total = int(await db.scalar(select(func.count()).select_from(StrategicObjective).where(*conditions)) or 0)
    rows = (await db.scalars(
        select(StrategicObjective).where(*conditions)
        .order_by(StrategicObjective.priority, StrategicObjective.objective, StrategicObjective.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()
    return {
        "items": [_objective_json(item) for item in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/objectives")
async def list_objectives(
    user: User = Depends(require_permission("strategic_objectives.read")),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(select(StrategicObjective).where(StrategicObjective.tenant_id == user.tenant_id).order_by(StrategicObjective.priority, StrategicObjective.objective))
    return [_objective_json(x) for x in rows.scalars()]


@router.post("/objectives", status_code=201)
async def create_objective(
    payload: ObjectivePayload,
    user: User = Depends(require_permission("strategic_objectives.manage")),
    db: AsyncSession = Depends(get_db),
):
    _validate_effective_window(payload.effective_from, payload.effective_to)
    await _user(db, user.tenant_id, payload.owner_id)
    if payload.business_unit_id:
        unit = await db.scalar(select(OrgUnit).where(OrgUnit.id == payload.business_unit_id, OrgUnit.tenant_id == user.tenant_id))
        if unit is None:
            raise HTTPException(422, "Business unit not found")
    duplicate = await db.scalar(select(StrategicObjective.id).where(StrategicObjective.tenant_id == user.tenant_id, StrategicObjective.objective.ilike(payload.objective.strip())))
    if duplicate:
        raise HTTPException(409, "Strategic objective already exists")
    item = StrategicObjective(
        id=uuid4(), tenant_id=user.tenant_id, owner_id=payload.owner_id,
        business_unit_id=payload.business_unit_id, objective=payload.objective.strip(),
        description=payload.description.strip() if payload.description else None,
        priority=payload.priority, strategic_category=payload.strategic_category.strip() if payload.strategic_category else None,
        status=payload.status, effective_from=payload.effective_from, effective_to=payload.effective_to,
    )
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="strategic_objective.created", entity_type="strategic_objective", entity_id=str(item.id))
    await db.commit()
    return _objective_json(item)


@router.post("/objectives/{objective_id}/capabilities", status_code=201)
async def map_objective_capability(
    objective_id: UUID,
    payload: ObjectiveCapabilityPayload,
    user: User = Depends(require_permission("strategic_objectives.manage")),
    db: AsyncSession = Depends(get_db),
):
    objective = await db.scalar(select(StrategicObjective).where(StrategicObjective.id == objective_id, StrategicObjective.tenant_id == user.tenant_id))
    capability = await db.scalar(select(Capability).where(Capability.id == payload.capability_id, Capability.tenant_id == user.tenant_id))
    if objective is None or capability is None:
        raise HTTPException(404, "Strategic objective or capability not found")
    item = await db.scalar(select(StrategicObjectiveCapability).where(StrategicObjectiveCapability.objective_id == objective.id, StrategicObjectiveCapability.capability_id == capability.id))
    if item is None:
        item = StrategicObjectiveCapability(objective_id=objective.id, capability_id=capability.id, required_level=payload.required_level, weight=payload.weight)
        db.add(item)
    else:
        item.required_level = payload.required_level
        item.weight = payload.weight
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="strategic_objective.capability_mapped", entity_type="strategic_objective", entity_id=str(objective.id), metadata={"capability_id": str(capability.id), "required_level": payload.required_level})
    await db.commit()
    return {"objective_id": str(objective.id), "capability_id": str(capability.id), "capability": capability.name, "required_level": item.required_level, "weight": item.weight}


@router.get("/competencies")
async def list_competencies(
    user: User = Depends(require_permission("competencies.read")),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(select(Competency).where(Competency.tenant_id == user.tenant_id).order_by(Competency.name))
    result = []
    for item in rows.scalars():
        levels = await db.execute(select(CompetencyLevel).where(CompetencyLevel.competency_id == item.id).order_by(CompetencyLevel.level))
        result.append(_competency_json(item, list(levels.scalars())))
    return result


@router.get("/competencies/page")
async def page_competencies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    q: str = Query(default="", max_length=160),
    user: User = Depends(require_permission("competencies.read")),
    db: AsyncSession = Depends(get_db),
):
    """Tenant-scoped, searchable competency lookup with bounded level hydration."""
    conditions = [Competency.tenant_id == user.tenant_id]
    term = q.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        match = f"%{escaped}%"
        conditions.append(or_(Competency.name.ilike(match, escape="\\"), Competency.code.ilike(match, escape="\\")))
    total = int(await db.scalar(select(func.count()).select_from(Competency).where(*conditions)) or 0)
    rows = (await db.scalars(
        select(Competency).where(*conditions).order_by(Competency.name, Competency.id)
        .offset((page - 1) * page_size).limit(page_size)
    )).all()
    competency_ids = [item.id for item in rows]
    levels_by_competency: dict[UUID, list[CompetencyLevel]] = {}
    if competency_ids:
        level_rows = await db.scalars(
            select(CompetencyLevel).where(CompetencyLevel.competency_id.in_(competency_ids))
            .order_by(CompetencyLevel.competency_id, CompetencyLevel.level)
        )
        for level in level_rows:
            levels_by_competency.setdefault(level.competency_id, []).append(level)
    return {
        "items": [_competency_json(item, levels_by_competency.get(item.id, [])) for item in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/competencies", status_code=201)
async def create_competency(
    payload: CompetencyPayload,
    user: User = Depends(require_permission("competencies.manage")),
    db: AsyncSession = Depends(get_db),
):
    _validate_effective_window(payload.effective_from, payload.effective_to)
    code = payload.code.strip().upper()
    name = payload.name.strip()
    duplicate = await db.scalar(select(Competency.id).where(Competency.tenant_id == user.tenant_id, (Competency.code == code) | (Competency.name.ilike(name))))
    if duplicate:
        raise HTTPException(409, "Competency code or name already exists")
    item = Competency(
        id=uuid4(), tenant_id=user.tenant_id, code=code, name=name, definition=payload.definition.strip(),
        type=payload.type, status=payload.status, effective_from=payload.effective_from, effective_to=payload.effective_to,
    )
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="competency.created", entity_type="competency", entity_id=str(item.id))
    await db.commit()
    return _competency_json(item, [])


@router.put("/competencies/{competency_id}/levels")
async def replace_competency_levels(
    competency_id: UUID,
    levels: list[CompetencyLevelPayload],
    user: User = Depends(require_permission("competencies.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(Competency).where(Competency.id == competency_id, Competency.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(404, "Competency not found")
    by_level = {x.level: x for x in levels}
    if set(by_level) != {1, 2, 3, 4, 5}:
        raise HTTPException(422, "All five governed proficiency levels are required")
    existing = list((await db.execute(select(CompetencyLevel).where(CompetencyLevel.competency_id == item.id))).scalars())
    for old in existing:
        await db.delete(old)
    for level, payload in sorted(by_level.items()):
        db.add(CompetencyLevel(id=uuid4(), competency_id=item.id, level=level, definition=payload.definition.strip(), behavioral_indicators=payload.behavioral_indicators))
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="competency.levels.replaced", entity_type="competency", entity_id=str(item.id))
    await db.commit()
    levels_result = await db.execute(select(CompetencyLevel).where(CompetencyLevel.competency_id == item.id).order_by(CompetencyLevel.level))
    return _competency_json(item, list(levels_result.scalars()))


@router.get("/capabilities/{capability_id}/competencies")
async def list_capability_competencies(
    capability_id: UUID,
    user: User = Depends(require_permission("competencies.read")),
    db: AsyncSession = Depends(get_db),
):
    capability = await db.scalar(select(Capability).where(Capability.id == capability_id, Capability.tenant_id == user.tenant_id))
    if capability is None:
        raise HTTPException(404, "Capability not found")
    rows = await db.execute(
        select(CapabilityCompetency, Competency)
        .join(Competency, Competency.id == CapabilityCompetency.competency_id)
        .where(CapabilityCompetency.capability_id == capability.id, Competency.tenant_id == user.tenant_id)
        .order_by(Competency.name)
    )
    return [{"capability_id": str(capability.id), "competency_id": str(link.competency_id), "competency": competency.name, "weight": link.weight} for link, competency in rows.all()]


@router.post("/capabilities/{capability_id}/competencies", status_code=201)
async def map_capability_competency(
    capability_id: UUID,
    payload: CapabilityCompetencyPayload,
    user: User = Depends(require_permission("competencies.manage")),
    db: AsyncSession = Depends(get_db),
):
    capability = await db.scalar(select(Capability).where(Capability.id == capability_id, Capability.tenant_id == user.tenant_id))
    competency = await db.scalar(select(Competency).where(Competency.id == payload.competency_id, Competency.tenant_id == user.tenant_id))
    if capability is None or competency is None:
        raise HTTPException(404, "Capability or competency not found")
    item = await db.scalar(select(CapabilityCompetency).where(CapabilityCompetency.capability_id == capability.id, CapabilityCompetency.competency_id == competency.id))
    if item is None:
        item = CapabilityCompetency(capability_id=capability.id, competency_id=competency.id, weight=payload.weight)
        db.add(item)
    else:
        item.weight = payload.weight
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability.competency_mapped", entity_type="capability", entity_id=str(capability.id), metadata={"competency_id": str(competency.id)})
    await db.commit()
    return {"capability_id": str(capability.id), "competency_id": str(competency.id), "competency": competency.name, "weight": item.weight}


@router.get("/roles/{role_id}/requirements")
async def list_role_requirements(
    role_id: UUID,
    user: User = Depends(require_permission("role_requirements.read")),
    db: AsyncSession = Depends(get_db),
):
    role = await _role(db, user.tenant_id, role_id)
    rows = await db.execute(select(RoleRequirement).where(RoleRequirement.role_id == role.id, RoleRequirement.tenant_id == user.tenant_id))
    result = []
    for item in rows.scalars():
        target_type = "capability" if item.capability_id else "competency" if item.competency_id else "skill"
        target_id = item.capability_id or item.competency_id or item.skill_id
        target_name = None
        if item.capability_id:
            target_name = (await db.scalar(select(Capability.name).where(Capability.id == item.capability_id, Capability.tenant_id == user.tenant_id)))
        elif item.competency_id:
            target_name = (await db.scalar(select(Competency.name).where(Competency.id == item.competency_id, Competency.tenant_id == user.tenant_id)))
        else:
            target_name = (await db.scalar(select(Skill.name).where(Skill.id == item.skill_id, Skill.tenant_id == user.tenant_id)))
        result.append({"id": str(item.id), "role_id": str(role.id), "target_type": target_type, "target_id": str(target_id), "target_name": target_name, "required_level": item.required_level, "criticality": item.criticality, "weight": item.weight, "effective_from": item.effective_from, "effective_to": item.effective_to})
    return result


@router.post("/roles/{role_id}/requirements", status_code=201)
async def create_role_requirement(
    role_id: UUID,
    payload: RoleRequirementPayload,
    user: User = Depends(require_permission("role_requirements.manage")),
    db: AsyncSession = Depends(get_db),
):
    role = await _role(db, user.tenant_id, role_id)
    if payload.target_type == "capability":
        target = await db.scalar(select(Capability).where(Capability.id == payload.target_id, Capability.tenant_id == user.tenant_id))
        target_field = "capability_id"
    elif payload.target_type == "competency":
        target = await db.scalar(select(Competency).where(Competency.id == payload.target_id, Competency.tenant_id == user.tenant_id))
        target_field = "competency_id"
    else:
        target = await db.scalar(select(Skill).where(Skill.id == payload.target_id, Skill.tenant_id == user.tenant_id))
        target_field = "skill_id"
    if target is None:
        raise HTTPException(422, "Requirement target not found")
    _validate_effective_window(payload.effective_from, payload.effective_to)
    existing_rows = await db.execute(select(RoleRequirement).where(
        RoleRequirement.tenant_id == user.tenant_id,
        RoleRequirement.role_id == role.id,
        getattr(RoleRequirement, target_field) == payload.target_id,
    ))
    for existing in existing_rows.scalars():
        if _window_overlaps(existing.effective_from, existing.effective_to, payload.effective_from, payload.effective_to):
            raise HTTPException(409, "This role requirement overlaps an existing effective period for the same target")
    kwargs = {
        "id": uuid4(), "tenant_id": user.tenant_id, "role_id": role.id,
        "required_level": payload.required_level, "criticality": payload.criticality,
        "weight": payload.weight, "effective_from": payload.effective_from, "effective_to": payload.effective_to,
        target_field: payload.target_id,
    }
    item = RoleRequirement(**kwargs)
    db.add(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="role_requirement.created", entity_type="role_requirement", entity_id=str(item.id), metadata={"target_type": payload.target_type, "target_id": str(payload.target_id), "required_level": payload.required_level})
    await db.commit()
    return {"id": str(item.id), "role_id": str(role.id), "target_type": payload.target_type, "target_id": str(payload.target_id), "required_level": item.required_level, "criticality": item.criticality, "weight": item.weight}
