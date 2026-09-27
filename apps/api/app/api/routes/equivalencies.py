from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import require_permission
from app.db.models import Course, CourseEquivalency, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


class CourseEquivalencyCreate(BaseModel):
    course_id: UUID
    equivalent_course_id: UUID
    equivalency_type: str = Field(default="full", pattern=r"^(full|partial|credit_transfer)$")
    notes: str | None = Field(default=None, max_length=2000)


class CourseEquivalencyUpdate(BaseModel):
    equivalency_type: str | None = Field(default=None, pattern=r"^(full|partial|credit_transfer)$")
    notes: str | None = Field(default=None, max_length=2000)
    active: bool | None = None


class CourseEquivalencyOut(BaseModel):
    id: UUID
    course_id: UUID
    course_title: str
    equivalent_course_id: UUID
    equivalent_course_title: str
    equivalency_type: str
    notes: str | None
    active: bool


async def serialize(item: CourseEquivalency, db: AsyncSession, tenant_id: UUID) -> dict:
    result = await db.execute(select(Course.id, Course.title).where(
        Course.tenant_id == tenant_id,
        Course.id.in_([item.course_id, item.equivalent_course_id]),
    ))
    title_map = {row.id: row.title for row in result.all()}
    return {
        "id": item.id,
        "course_id": item.course_id,
        "course_title": title_map[item.course_id],
        "equivalent_course_id": item.equivalent_course_id,
        "equivalent_course_title": title_map[item.equivalent_course_id],
        "equivalency_type": item.equivalency_type,
        "notes": item.notes,
        "active": item.active,
    }


@router.get("", response_model=list[CourseEquivalencyOut])
async def list_equivalencies(
    active_only: bool = Query(default=False),
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    primary = aliased(Course)
    equivalent = aliased(Course)
    statement = (
        select(CourseEquivalency, primary.title, equivalent.title)
        .join(primary, primary.id == CourseEquivalency.course_id)
        .join(equivalent, equivalent.id == CourseEquivalency.equivalent_course_id)
        .where(
            CourseEquivalency.tenant_id == user.tenant_id,
            primary.tenant_id == user.tenant_id,
            equivalent.tenant_id == user.tenant_id,
        )
    )
    if active_only:
        statement = statement.where(CourseEquivalency.active.is_(True))
    result = await db.execute(statement.order_by(CourseEquivalency.created_at.desc()))
    return [{
        "id": item.id,
        "course_id": item.course_id,
        "course_title": course_title,
        "equivalent_course_id": item.equivalent_course_id,
        "equivalent_course_title": equivalent_title,
        "equivalency_type": item.equivalency_type,
        "notes": item.notes,
        "active": item.active,
    } for item, course_title, equivalent_title in result.all()]


@router.post("", response_model=CourseEquivalencyOut, status_code=status.HTTP_201_CREATED)
async def create_equivalency(
    payload: CourseEquivalencyCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    if payload.course_id == payload.equivalent_course_id:
        raise HTTPException(status_code=422, detail="A course cannot be equivalent to itself")
    result = await db.execute(select(Course).where(
        Course.tenant_id == user.tenant_id,
        Course.id.in_([payload.course_id, payload.equivalent_course_id]),
    ))
    courses = {course.id: course for course in result.scalars().all()}
    if len(courses) != 2:
        raise HTTPException(status_code=404, detail="One or both courses were not found")
    duplicate = await db.scalar(select(CourseEquivalency).where(
        CourseEquivalency.tenant_id == user.tenant_id,
        (
            ((CourseEquivalency.course_id == payload.course_id) & (CourseEquivalency.equivalent_course_id == payload.equivalent_course_id))
            | ((CourseEquivalency.course_id == payload.equivalent_course_id) & (CourseEquivalency.equivalent_course_id == payload.course_id))
        ),
    ))
    if duplicate:
        raise HTTPException(status_code=409, detail="An equivalent course relationship already exists")
    item = CourseEquivalency(
        tenant_id=user.tenant_id,
        course_id=payload.course_id,
        equivalent_course_id=payload.equivalent_course_id,
        equivalency_type=payload.equivalency_type,
        notes=payload.notes,
    )
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.equivalency.created",
                entity_type="course_equivalency", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return await serialize(item, db, user.tenant_id)


@router.patch("/{equivalency_id}", response_model=CourseEquivalencyOut)
async def update_equivalency(
    equivalency_id: UUID,
    payload: CourseEquivalencyUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(CourseEquivalency).where(
        CourseEquivalency.id == equivalency_id,
        CourseEquivalency.tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Course equivalency not found")
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(item, field, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.equivalency.updated",
                entity_type="course_equivalency", entity_id=str(item.id),
                metadata={"fields": sorted(values)})
    await db.commit()
    await db.refresh(item)
    return await serialize(item, db, user.tenant_id)


@router.delete("/{equivalency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equivalency(
    equivalency_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(CourseEquivalency).where(
        CourseEquivalency.id == equivalency_id,
        CourseEquivalency.tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Course equivalency not found")
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.equivalency.deleted",
                entity_type="course_equivalency", entity_id=str(item.id))
    await db.delete(item)
    await db.commit()
