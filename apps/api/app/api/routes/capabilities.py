from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import (
    Capability,
    CapabilityCategory,
    CapabilityLevel,
    CapabilitySkill,
    Skill,
    User,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()
LEVEL_NAMES = {
    1: "Foundational",
    2: "Developing",
    3: "Proficient",
    4: "Advanced",
    5: "Expert",
}


class CategoryPayload(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    active: bool = True


class CapabilityPayload(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    definition: str = Field(min_length=10)
    category_id: UUID | None = None
    owner_id: UUID | None = None
    criticality: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    status: str = Field(default="draft", pattern="^(draft|active|retired)$")
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    governance: dict = Field(default_factory=dict)


class LevelPayload(BaseModel):
    level: int = Field(ge=1, le=5)
    name: str | None = Field(default=None, max_length=80)
    definition: str = Field(min_length=3)
    indicators: list[str] = Field(default_factory=list)


class SkillMapPayload(BaseModel):
    skill_id: UUID
    weight: int = Field(default=1, ge=1, le=100)


async def _category(db, tenant_id, category_id):
    if category_id is None:
        return None
    item = await db.scalar(
        select(CapabilityCategory).where(
            CapabilityCategory.id == category_id,
            CapabilityCategory.tenant_id == tenant_id,
        )
    )
    if item is None:
        raise HTTPException(422, "Capability category not found")
    return item


async def _owner(db, tenant_id, owner_id):
    if owner_id is None:
        return None
    item = await db.scalar(
        select(User).where(
            User.id == owner_id, User.tenant_id == tenant_id, User.is_active.is_(True)
        )
    )
    if item is None:
        raise HTTPException(422, "Capability owner not found")
    return item


@router.get("/categories")
async def list_categories(
    user: User = Depends(require_permission("capabilities.read")),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(CapabilityCategory)
        .where(CapabilityCategory.tenant_id == user.tenant_id)
        .order_by(CapabilityCategory.name)
    )
    return [
        {
            "id": str(x.id),
            "name": x.name,
            "description": x.description,
            "active": x.active,
        }
        for x in rows.scalars()
    ]


@router.post("/categories", status_code=201)
async def create_category(
    payload: CategoryPayload,
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    name = payload.name.strip()
    exists = await db.scalar(
        select(CapabilityCategory.id).where(
            CapabilityCategory.tenant_id == user.tenant_id,
            CapabilityCategory.name.ilike(name),
        )
    )
    if exists:
        raise HTTPException(409, "Capability category already exists")
    item = CapabilityCategory(
        id=uuid4(),
        tenant_id=user.tenant_id,
        name=name,
        description=payload.description.strip() if payload.description else None,
        active=payload.active,
    )
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability_category.created",
        entity_type="capability_category",
        entity_id=str(item.id),
    )
    await db.commit()
    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "active": item.active,
    }


@router.get("/page")
async def page_capabilities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    q: str = Query(default="", max_length=100),
    status: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    user: User = Depends(require_permission("capabilities.read")),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Capability.tenant_id == user.tenant_id]
    term = q.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        match = f"%{escaped}%"
        conditions.append(
            or_(
                Capability.name.ilike(match, escape="\\"),
                Capability.code.ilike(match, escape="\\"),
            )
        )
    if status:
        conditions.append(Capability.status == status)
    if criticality:
        conditions.append(Capability.criticality == criticality)
    total = int(await db.scalar(select(func.count()).select_from(Capability).where(*conditions)) or 0)
    rows = (await db.scalars(
        select(Capability).where(*conditions)
        .order_by(Capability.name, Capability.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()
    category_ids = {item.category_id for item in rows if item.category_id}
    category_map = {}
    if category_ids:
        category_rows = await db.execute(
            select(CapabilityCategory).where(
                CapabilityCategory.tenant_id == user.tenant_id,
                CapabilityCategory.id.in_(category_ids),
            )
        )
        category_map = {row.id: row for row in category_rows.scalars()}
    capability_ids = [item.id for item in rows]
    levels_by_capability: dict[UUID, list[CapabilityLevel]] = {}
    if capability_ids:
        level_rows = await db.execute(
            select(CapabilityLevel)
            .where(CapabilityLevel.capability_id.in_(capability_ids))
            .order_by(CapabilityLevel.capability_id, CapabilityLevel.level)
        )
        for level in level_rows.scalars():
            levels_by_capability.setdefault(level.capability_id, []).append(level)
    return {
        "items": [
            _serialize_capability_payload(
                item,
                category_map.get(item.category_id) if item.category_id else None,
                levels_by_capability.get(item.id, []),
            )
            for item in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("")
async def list_capabilities(
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    user: User = Depends(require_permission("capabilities.read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Capability).where(Capability.tenant_id == user.tenant_id)
    if q:
        stmt = stmt.where(Capability.name.ilike(f"%{q.strip()}%"))
    if status:
        stmt = stmt.where(Capability.status == status)
    if criticality:
        stmt = stmt.where(Capability.criticality == criticality)
    rows = await db.execute(stmt.order_by(Capability.name).limit(250))
    items = list(rows.scalars())
    if not items:
        return []

    category_ids = {item.category_id for item in items if item.category_id}
    category_map = {}
    if category_ids:
        category_rows = await db.execute(
            select(CapabilityCategory).where(
                CapabilityCategory.tenant_id == user.tenant_id,
                CapabilityCategory.id.in_(category_ids),
            )
        )
        category_map = {row.id: row for row in category_rows.scalars()}

    level_rows = await db.execute(
        select(CapabilityLevel)
        .where(CapabilityLevel.capability_id.in_([item.id for item in items]))
        .order_by(CapabilityLevel.capability_id, CapabilityLevel.level)
    )
    levels_by_capability: dict[UUID, list[CapabilityLevel]] = {}
    for level in level_rows.scalars():
        levels_by_capability.setdefault(level.capability_id, []).append(level)

    return [
        _serialize_capability_payload(
            item,
            category_map.get(item.category_id) if item.category_id else None,
            levels_by_capability.get(item.id, []),
        )
        for item in items
    ]


def _serialize_capability_payload(item, category, levels):
    return {
        "id": str(item.id),
        "code": item.code,
        "name": item.name,
        "definition": item.definition,
        "category_id": str(item.category_id) if item.category_id else None,
        "category": category.name if category else None,
        "owner_id": str(item.owner_id) if item.owner_id else None,
        "criticality": item.criticality,
        "status": item.status,
        "effective_from": item.effective_from,
        "effective_to": item.effective_to,
        "level_min": item.level_min,
        "level_max": item.level_max,
        "governance": item.governance,
        "levels": [
            {
                "level": level.level,
                "name": level.name,
                "definition": level.definition,
                "indicators": level.indicators,
            }
            for level in levels
        ],
    }


async def _serialize_capability(db, item):
    category = (
        await db.scalar(
            select(CapabilityCategory).where(
                CapabilityCategory.id == item.category_id,
                CapabilityCategory.tenant_id == item.tenant_id,
            )
        )
        if item.category_id
        else None
    )
    levels = (
        await db.execute(
            select(CapabilityLevel)
            .where(CapabilityLevel.capability_id == item.id)
            .order_by(CapabilityLevel.level)
        )
    ).scalars().all()
    return _serialize_capability_payload(item, category, levels)


@router.get("/{capability_id}")
async def get_capability(
    capability_id: UUID,
    user: User = Depends(require_permission("capabilities.read")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Capability).where(
            Capability.id == capability_id, Capability.tenant_id == user.tenant_id
        )
    )
    if item is None:
        raise HTTPException(404, "Capability not found")
    category = (
        await db.scalar(
            select(CapabilityCategory).where(
                CapabilityCategory.id == item.category_id,
                CapabilityCategory.tenant_id == user.tenant_id,
            )
        )
        if item.category_id
        else None
    )
    levels = (
        await db.execute(
            select(CapabilityLevel)
            .where(CapabilityLevel.capability_id == item.id)
            .order_by(CapabilityLevel.level)
        )
    ).scalars().all()
    return _serialize_capability_payload(item, category, levels)


@router.post("", status_code=201)
async def create_capability(
    payload: CapabilityPayload,
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    if (
        payload.effective_to
        and payload.effective_from
        and payload.effective_to <= payload.effective_from
    ):
        raise HTTPException(422, "Effective end must be after effective start")
    await _category(db, user.tenant_id, payload.category_id)
    await _owner(db, user.tenant_id, payload.owner_id)
    duplicate = await db.scalar(
        select(Capability.id).where(
            Capability.tenant_id == user.tenant_id,
            Capability.code == payload.code.strip().upper(),
        )
    )
    if duplicate:
        raise HTTPException(409, "Capability code already exists")
    item = Capability(
        id=uuid4(),
        tenant_id=user.tenant_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        definition=payload.definition.strip(),
        category_id=payload.category_id,
        owner_id=payload.owner_id,
        criticality=payload.criticality,
        status=payload.status,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        governance=payload.governance,
    )
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.created",
        entity_type="capability",
        entity_id=str(item.id),
    )
    await db.commit()
    return await _serialize_capability(db, item)


@router.patch("/{capability_id}")
async def update_capability(
    capability_id: UUID,
    payload: CapabilityPayload,
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Capability).where(
            Capability.id == capability_id, Capability.tenant_id == user.tenant_id
        )
    )
    if item is None:
        raise HTTPException(404, "Capability not found")
    if (
        payload.effective_to
        and payload.effective_from
        and payload.effective_to <= payload.effective_from
    ):
        raise HTTPException(422, "Effective end must be after effective start")
    await _category(db, user.tenant_id, payload.category_id)
    await _owner(db, user.tenant_id, payload.owner_id)
    duplicate = await db.scalar(
        select(Capability.id).where(
            Capability.tenant_id == user.tenant_id,
            Capability.id != item.id,
            Capability.code == payload.code.strip().upper(),
        )
    )
    if duplicate:
        raise HTTPException(409, "Capability code already exists")
    for key in (
        "code",
        "name",
        "definition",
        "category_id",
        "owner_id",
        "criticality",
        "status",
        "effective_from",
        "effective_to",
        "governance",
    ):
        setattr(item, key, getattr(payload, key))
    item.code = item.code.strip().upper()
    item.name = item.name.strip()
    item.definition = item.definition.strip()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.updated",
        entity_type="capability",
        entity_id=str(item.id),
    )
    await db.commit()
    return await _serialize_capability(db, item)


@router.put("/{capability_id}/levels", status_code=200)
async def replace_levels(
    capability_id: UUID,
    levels: list[LevelPayload],
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Capability).where(
            Capability.id == capability_id, Capability.tenant_id == user.tenant_id
        )
    )
    if item is None:
        raise HTTPException(404, "Capability not found")
    by_level = {x.level: x for x in levels}
    if set(by_level) != set(range(item.level_min, item.level_max + 1)):
        raise HTTPException(
            422, "Every governed proficiency level in the capability range is required"
        )
    existing = list(
        (
            await db.execute(
                select(CapabilityLevel).where(CapabilityLevel.capability_id == item.id)
            )
        ).scalars()
    )
    for old in existing:
        await db.delete(old)
    for level, payload in sorted(by_level.items()):
        db.add(
            CapabilityLevel(
                id=uuid4(),
                capability_id=item.id,
                level=level,
                name=LEVEL_NAMES[level],
                definition=payload.definition.strip(),
                indicators=payload.indicators,
            )
        )
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.levels.replaced",
        entity_type="capability",
        entity_id=str(item.id),
        metadata={"levels": sorted(by_level)},
    )
    await db.commit()
    return await _serialize_capability(db, item)


@router.post("/{capability_id}/skills", status_code=201)
async def map_skill(
    capability_id: UUID,
    payload: SkillMapPayload,
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Capability).where(
            Capability.id == capability_id, Capability.tenant_id == user.tenant_id
        )
    )
    skill = await db.scalar(
        select(Skill).where(
            Skill.id == payload.skill_id, Skill.tenant_id == user.tenant_id
        )
    )
    if item is None or skill is None:
        raise HTTPException(404, "Capability or skill not found")
    mapping = await db.scalar(
        select(CapabilitySkill).where(
            CapabilitySkill.capability_id == item.id,
            CapabilitySkill.skill_id == skill.id,
        )
    )
    if mapping is None:
        mapping = CapabilitySkill(
            capability_id=item.id, skill_id=skill.id, weight=payload.weight
        )
        db.add(mapping)
    else:
        mapping.weight = payload.weight
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.skill_mapped",
        entity_type="capability",
        entity_id=str(item.id),
        metadata={"skill_id": str(skill.id), "weight": payload.weight},
    )
    await db.commit()
    return {
        "capability_id": str(item.id),
        "skill_id": str(skill.id),
        "skill": skill.name,
        "weight": mapping.weight,
    }


@router.delete("/{capability_id}/skills/{skill_id}", status_code=204)
async def unmap_skill(
    capability_id: UUID,
    skill_id: UUID,
    user: User = Depends(require_permission("capabilities.manage")),
    db: AsyncSession = Depends(get_db),
):
    mapping = await db.scalar(
        select(CapabilitySkill)
        .join(Capability, Capability.id == CapabilitySkill.capability_id)
        .where(
            CapabilitySkill.capability_id == capability_id,
            CapabilitySkill.skill_id == skill_id,
            Capability.tenant_id == user.tenant_id,
        )
    )
    if mapping is None:
        raise HTTPException(404, "Capability skill mapping not found")
    await db.delete(mapping)
    await db.commit()
