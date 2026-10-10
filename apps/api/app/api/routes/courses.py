from datetime import datetime, timezone
from uuid import UUID
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import ComplianceAssignment, Course, CourseCategory, CourseContentVersion, CourseModule, CourseSkill, Enrollment, FileObject, Lesson, LessonProgress, OrgUnit, User, UserSkill
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()


LESSON_BLOCK_TYPES = {"heading", "paragraph", "bullets", "numbered", "callout", "image", "video", "file", "link", "divider"}
LESSON_CALL_OUT_VARIANTS = {"info", "success", "warning", "important"}


def validate_http_url(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 2000:
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


async def validate_lesson_content(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    content_type: str,
    content: dict,
) -> None:
    if not isinstance(content, dict):
        raise HTTPException(status_code=422, detail="Lesson content must be an object")
    if content_type != "rich_text":
        if not validate_http_url(content.get("url")):
            raise HTTPException(status_code=422, detail="Lesson resource must use a valid http(s) URL")
        return
    blocks = content.get("blocks")
    if not isinstance(blocks, list) or not blocks or len(blocks) > 80:
        legacy_body = content.get("body")
        if isinstance(legacy_body, str) and legacy_body.strip():
            return
        raise HTTPException(status_code=422, detail="Structured lessons require 1 to 80 content blocks")
    file_ids: list[UUID] = []
    for index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict) or block.get("type") not in LESSON_BLOCK_TYPES:
            raise HTTPException(status_code=422, detail=f"Invalid lesson block at position {index}")
        block_type = block["type"]
        text = block.get("text")
        if block_type in {"heading", "paragraph", "bullets", "numbered", "callout", "link"} and (
            not isinstance(text, str) or not text.strip()
        ):
            raise HTTPException(status_code=422, detail=f"Lesson block {index} requires text")
        if block_type == "heading" and block.get("level") not in {2, 3, 4, None}:
            raise HTTPException(status_code=422, detail=f"Heading block {index} has an invalid level")
        if block_type == "callout" and block.get("variant") not in LESSON_CALL_OUT_VARIANTS | {None}:
            raise HTTPException(status_code=422, detail=f"Callout block {index} has an invalid style")
        if block_type in {"image", "file"}:
            file_id = block.get("file_id")
            if file_id:
                try:
                    file_ids.append(UUID(str(file_id)))
                except ValueError as exc:
                    raise HTTPException(status_code=422, detail=f"Lesson block {index} contains an invalid file reference") from exc
            elif not validate_http_url(block.get("url")):
                raise HTTPException(status_code=422, detail=f"Lesson block {index} requires a file reference or valid URL")
        if block_type in {"video", "link"} and not validate_http_url(block.get("url")):
            raise HTTPException(status_code=422, detail=f"Lesson block {index} requires a valid URL")
    if file_ids:
        result = await db.execute(select(FileObject.id).where(
            FileObject.tenant_id == tenant_id,
            FileObject.id.in_(list(dict.fromkeys(file_ids))),
            FileObject.status == "available",
        ))
        available = set(result.scalars().all())
        if available != set(file_ids):
            raise HTTPException(status_code=422, detail="One or more referenced learning files are unavailable")


def normalize_tags(tags: list[str]) -> list[str]:
    cleaned: list[str] = []
    for tag in tags:
        value = " ".join(tag.strip().split())
        if not value:
            continue
        if len(value) > 80:
            raise HTTPException(status_code=422, detail="Course tags must be 80 characters or fewer")
        lowered = value.casefold()
        if not any(existing.casefold() == lowered for existing in cleaned):
            cleaned.append(value)
    return cleaned


async def validate_audience_org_units(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    org_unit_ids: list[UUID],
) -> list[str]:
    unique_ids = list(dict.fromkeys(org_unit_ids))
    if not unique_ids:
        return []
    count = await db.scalar(select(func.count(OrgUnit.id)).where(
        OrgUnit.tenant_id == tenant_id,
        OrgUnit.id.in_(unique_ids),
    ))
    if count != len(unique_ids):
        raise HTTPException(status_code=422, detail="One or more audience organization units are invalid")
    return [str(item) for item in unique_ids]


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
    category_id: UUID | None = None
    owner_id: UUID | None = None
    visibility: str = Field(default="tenant", pattern=r"^(tenant|private)$")
    enrollment_policy: str = Field(default="open", pattern=r"^(open|approval|assignment_only)$")
    capacity: int | None = Field(default=None, ge=1, le=100000)
    audience_org_units: list[UUID] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=30)
    prerequisites: list[UUID] = Field(default_factory=list, max_length=20)

class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
    category_id: UUID | None = None
    owner_id: UUID | None = None
    visibility: str | None = Field(default=None, pattern=r"^(tenant|private)$")
    enrollment_policy: str | None = Field(default=None, pattern=r"^(open|approval|assignment_only)$")
    capacity: int | None = Field(default=None, ge=1, le=100000)
    audience_org_units: list[UUID] | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=30)
    prerequisites: list[UUID] | None = Field(default=None, max_length=20)

class ModuleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    description: str | None = None
    position: int = Field(ge=1)

class LessonCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    content_type: str = Field(default="rich_text", pattern=r"^(rich_text|video|document|link)$")
    content: dict = Field(default_factory=dict)
    position: int = Field(ge=1)
    change_note: str | None = Field(default=None, max_length=500)

class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=240)
    content_type: str | None = Field(default=None, pattern=r"^(rich_text|video|document|link)$")
    content: dict | None = None
    position: int | None = Field(default=None, ge=1)
    change_note: str | None = Field(default=None, max_length=500)

class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=240)
    description: str | None = None
    position: int | None = Field(default=None, ge=1)

class PositionUpdate(BaseModel):
    position: int = Field(ge=1, le=1000)

class CourseOut(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str | None
    status: str
    estimated_minutes: int | None
    category_id: UUID | None
    owner_id: UUID | None
    visibility: str
    enrollment_policy: str
    capacity: int | None
    audience_org_units: list[UUID]
    tags: list[str]
    prerequisites: list[UUID]
    model_config = {"from_attributes": True}

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None

class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    active: bool | None = None

class CategoryOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    active: bool
    model_config = {"from_attributes": True}

class EnrollmentDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)

class BulkEnrollmentCreate(BaseModel):
    user_ids: list[UUID] = Field(min_length=1, max_length=500)
    due_at: datetime | None = None

class EnrollmentOut(BaseModel):
    id: UUID
    course_id: UUID
    user_id: UUID
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    model_config = {"from_attributes": True}

class ContentVersionOut(BaseModel):
    id: UUID
    lesson_id: UUID
    version_number: int
    title: str
    content_type: str
    content: dict
    change_note: str | None
    changed_by: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    manage: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = select(CourseCategory).where(CourseCategory.tenant_id == user.tenant_id)
    if not (manage and await user_has_permission(user, db, "courses.manage")):
        statement = statement.where(CourseCategory.active.is_(True))
    result = await db.execute(statement.order_by(CourseCategory.name.asc()))
    return list(result.scalars().all())


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    normalized_name = " ".join(payload.name.strip().split())
    existing = await db.scalar(
        select(CourseCategory).where(
            CourseCategory.tenant_id == user.tenant_id,
            func.lower(CourseCategory.name) == normalized_name.lower(),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Course category already exists")
    category = CourseCategory(
        tenant_id=user.tenant_id,
        name=normalized_name,
        description=payload.description,
    )
    db.add(category)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.category.created",
                entity_type="course_category", entity_id=str(category.id))
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    category = await db.scalar(select(CourseCategory).where(
        CourseCategory.id == category_id,
        CourseCategory.tenant_id == user.tenant_id,
    ))
    if category is None:
        raise HTTPException(status_code=404, detail="Course category not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and values["name"] is not None:
        duplicate = await db.scalar(select(CourseCategory).where(
            CourseCategory.tenant_id == user.tenant_id,
            CourseCategory.id != category.id,
            func.lower(CourseCategory.name) == values["name"].lower(),
        ))
        if duplicate:
            raise HTTPException(status_code=409, detail="Course category already exists")
        values["name"] = " ".join(values["name"].strip().split())
    for field, value in values.items():
        setattr(category, field, value)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="course.category.updated",
        entity_type="course_category",
        entity_id=str(category.id),
        metadata={"fields": sorted(values)},
    )
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/audience-options")
async def course_audience_options(
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgUnit)
        .where(OrgUnit.tenant_id == user.tenant_id)
        .order_by(OrgUnit.name.asc())
    )
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "unit_type": item.unit_type,
            "code": item.code,
        }
        for item in result.scalars().all()
    ]


@router.get("", response_model=list[CourseOut])
async def list_courses(
    manage: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Course).where(Course.tenant_id == user.tenant_id)
    can_manage = manage and await user_has_permission(user, db, "courses.manage")
    if not can_manage:
        assigned_course_ids = select(Enrollment.course_id).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.user_id == user.id,
        )
        statement = statement.where(
            Course.status == "published",
            or_(Course.visibility == "tenant", Course.id.in_(assigned_course_ids)),
        )
    result = await db.execute(statement.order_by(Course.title.asc()))
    return list(result.scalars().all())


@router.get("/page")
async def page_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    q: str = Query(default="", max_length=160),
    scope: str = Query(default="all", pattern="^(all|learning|available)$"),
    manage: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bounded tenant course catalog with per-learner enrollment status."""
    can_manage = manage and await user_has_permission(user, db, "courses.manage")
    conditions = [Course.tenant_id == user.tenant_id]
    if not can_manage:
        conditions.extend([
            Course.status == "published",
            or_(
                Course.visibility == "tenant",
                Course.id.in_(select(Enrollment.course_id).where(
                    Enrollment.tenant_id == user.tenant_id,
                    Enrollment.user_id == user.id,
                )),
            ),
        ])
        enrollment_exists = select(Enrollment.id).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.user_id == user.id,
            Enrollment.course_id == Course.id,
            Enrollment.status != "rejected",
        ).exists()
        if scope == "learning":
            conditions.append(enrollment_exists)
        elif scope == "available":
            conditions.append(~enrollment_exists)
    term = q.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        match = f"%{escaped}%"
        conditions.append(or_(
            Course.title.ilike(match, escape="\\"),
            Course.slug.ilike(match, escape="\\"),
            Course.description.ilike(match, escape="\\"),
        ))
    total = int(await db.scalar(select(func.count(Course.id)).where(*conditions)) or 0)
    rows = (await db.scalars(
        select(Course).where(*conditions).order_by(Course.title.asc(), Course.id.asc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()
    course_ids = [course.id for course in rows]
    enrollment_by_course: dict[UUID, str] = {}
    if course_ids and not can_manage:
        enrollments = await db.scalars(
            select(Enrollment).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.user_id == user.id,
                Enrollment.course_id.in_(course_ids),
            ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc())
        )
        for enrollment in enrollments:
            enrollment_by_course.setdefault(enrollment.course_id, enrollment.status)
    items = []
    for course in rows:
        item = CourseOut.model_validate(course).model_dump(mode="json")
        item["enrollment_status"] = enrollment_by_course.get(course.id)
        items.append(item)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/{course_id}", response_model=dict)
async def course_detail(
    course_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(
        select(Course).where(
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    can_manage = await user_has_permission(user, db, "courses.manage")
    enrollment = await db.scalar(
        select(Enrollment).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.user_id == user.id,
        ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc())
    )
    if not can_manage and course.status != "published":
        raise HTTPException(status_code=404, detail="Course not found")
    if not can_manage and course.visibility == "private" and enrollment is None:
        raise HTTPException(status_code=404, detail="Course not found")

    modules_result = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course.id)
        .order_by(CourseModule.position.asc())
    )
    modules = list(modules_result.scalars().all())
    can_view_content = can_manage or (enrollment is not None and enrollment.status in {"enrolled", "in_progress", "completed"})
    payload = []
    for module in modules:
        lessons_result = await db.execute(
            select(Lesson)
            .where(Lesson.module_id == module.id)
            .order_by(Lesson.position.asc())
        )
        payload.append(
            {
                "id": str(module.id),
                "title": module.title,
                "description": module.description,
                "position": module.position,
                "lessons": [
                    {
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "content_type": lesson.content_type,
                        "content": lesson.content if can_view_content else {},
                        "position": lesson.position,
                    }
                    for lesson in lessons_result.scalars().all()
                ],
            }
        )
    completed_lesson_ids: list[str] = []
    if enrollment:
        progress_result = await db.execute(
            select(LessonProgress.lesson_id).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.status == "completed",
            )
        )
        completed_lesson_ids = [str(item) for item in progress_result.scalars().all()]
    total_lessons = 0
    for module_payload in payload:
        lessons = module_payload.get("lessons")
        if isinstance(lessons, list):
            total_lessons += len(lessons)
    progress_percent = round((len(completed_lesson_ids) / total_lessons) * 100) if total_lessons else 0
    return {
        "id": str(course.id),
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "status": course.status,
        "estimated_minutes": course.estimated_minutes,
        "category_id": str(course.category_id) if course.category_id else None,
        "owner_id": str(course.owner_id) if course.owner_id else None,
        "visibility": course.visibility,
        "enrollment_policy": course.enrollment_policy,
        "capacity": course.capacity,
        "audience_org_units": course.audience_org_units,
        "tags": course.tags,
        "prerequisites": course.prerequisites,
        "modules": payload,
        "completed_lesson_ids": completed_lesson_ids,
        "progress_percent": progress_percent,
        "enrollment": {
            "id": str(enrollment.id),
            "status": enrollment.status,
            "due_at": enrollment.due_at,
            "completed_at": enrollment.completed_at,
        } if enrollment else None,
    }

@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    duplicate = await db.execute(
        select(Course).where(Course.tenant_id == user.tenant_id, Course.slug == payload.slug)
    )
    if duplicate.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Course slug already exists")
    values = payload.model_dump()
    values["tags"] = normalize_tags(values["tags"])
    values["prerequisites"] = [str(item) for item in values["prerequisites"]]
    values["audience_org_units"] = await validate_audience_org_units(
        db,
        tenant_id=user.tenant_id,
        org_unit_ids=values["audience_org_units"],
    )
    if values["owner_id"] is None:
        values["owner_id"] = user.id
    if values["category_id"]:
        category = await db.scalar(select(CourseCategory).where(
            CourseCategory.id == values["category_id"], CourseCategory.tenant_id == user.tenant_id
        ))
        if category is None:
            raise HTTPException(status_code=422, detail="Category does not belong to this tenant")
    if values["owner_id"]:
        owner = await db.scalar(select(User).where(
            User.id == values["owner_id"], User.tenant_id == user.tenant_id, User.is_active.is_(True)
        ))
        if owner is None:
            raise HTTPException(status_code=422, detail="Owner does not belong to this tenant")
    if values["prerequisites"]:
        prerequisite_count = await db.scalar(select(func.count(Course.id)).where(
            Course.tenant_id == user.tenant_id, Course.id.in_(values["prerequisites"])
        ))
        if prerequisite_count != len(set(values["prerequisites"])):
            raise HTTPException(status_code=422, detail="One or more prerequisites are invalid")
    course = Course(tenant_id=user.tenant_id, **values)
    db.add(course)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.created", entity_type="course", entity_id=str(course.id))
    await db.commit()
    await db.refresh(course)
    return course

@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    values = payload.model_dump(exclude_unset=True)
    if "tags" in values and values["tags"] is not None:
        values["tags"] = normalize_tags(values["tags"])
    if "prerequisites" in values and values["prerequisites"] is not None:
        values["prerequisites"] = [str(item) for item in values["prerequisites"]]
    if "audience_org_units" in values and values["audience_org_units"] is not None:
        values["audience_org_units"] = await validate_audience_org_units(
            db,
            tenant_id=user.tenant_id,
            org_unit_ids=values["audience_org_units"],
        )
    if "category_id" in values and values["category_id"]:
        category = await db.scalar(select(CourseCategory).where(
            CourseCategory.id == values["category_id"], CourseCategory.tenant_id == user.tenant_id
        ))
        if category is None:
            raise HTTPException(status_code=422, detail="Category does not belong to this tenant")
    if "owner_id" in values and values["owner_id"]:
        owner = await db.scalar(select(User).where(
            User.id == values["owner_id"], User.tenant_id == user.tenant_id, User.is_active.is_(True)
        ))
        if owner is None:
            raise HTTPException(status_code=422, detail="Owner does not belong to this tenant")
    if "prerequisites" in values and values["prerequisites"]:
        prerequisite_count = await db.scalar(select(func.count(Course.id)).where(
            Course.tenant_id == user.tenant_id,
            Course.id.in_(values["prerequisites"]),
            Course.id != course.id,
        ))
        if prerequisite_count != len(set(values["prerequisites"])):
            raise HTTPException(status_code=422, detail="One or more prerequisites are invalid")
    for field, value in values.items():
        setattr(course, field, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.updated", entity_type="course", entity_id=str(course.id), metadata={"fields": sorted(values)})
    await db.commit()
    await db.refresh(course)
    return course

async def record_content_version(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    lesson: Lesson,
    changed_by: UUID,
    change_note: str | None,
) -> CourseContentVersion:
    latest = await db.scalar(
        select(func.max(CourseContentVersion.version_number)).where(
            CourseContentVersion.lesson_id == lesson.id,
        )
    )
    version = CourseContentVersion(
        tenant_id=tenant_id,
        lesson_id=lesson.id,
        version_number=(latest or 0) + 1,
        title=lesson.title,
        content_type=lesson.content_type,
        content=lesson.content,
        change_note=change_note,
        changed_by=changed_by,
    )
    db.add(version)
    await db.flush()
    return version


@router.post("/{course_id}/modules", response_model=dict)
async def create_module(
    course_id: UUID,
    payload: ModuleCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    module = CourseModule(course_id=course.id, **payload.model_dump())
    db.add(module)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.module.created", entity_type="course_module", entity_id=str(module.id))
    await db.commit()
    return {"id": str(module.id), "title": module.title, "position": module.position}

@router.post("/{course_id}/modules/{module_id}/lessons", response_model=dict)
async def create_lesson(
    course_id: UUID,
    module_id: UUID,
    payload: LessonCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    module = await db.scalar(
        select(CourseModule).join(Course).where(
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
            CourseModule.id == module_id,
        )
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    await validate_lesson_content(
        db,
        tenant_id=user.tenant_id,
        content_type=payload.content_type,
        content=payload.content,
    )
    lesson_values = payload.model_dump(exclude={"change_note"})
    lesson = Lesson(module_id=module.id, **lesson_values)
    db.add(lesson)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="lesson.created", entity_type="lesson", entity_id=str(lesson.id))
    await record_content_version(
        db,
        tenant_id=user.tenant_id,
        lesson=lesson,
        changed_by=user.id,
        change_note=payload.change_note or "Initial lesson version",
    )
    await db.commit()
    return {"id": str(lesson.id), "title": lesson.title, "position": lesson.position, "content_type": lesson.content_type}



@router.patch("/{course_id}/modules/{module_id}/position", response_model=dict)
async def move_module(
    course_id: UUID,
    module_id: UUID,
    payload: PositionUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    result = await db.execute(select(CourseModule).where(CourseModule.course_id == course_id).order_by(CourseModule.position.asc()))
    modules = list(result.scalars().all())
    moving = next((item for item in modules if item.id == module_id), None)
    if moving is None:
        raise HTTPException(status_code=404, detail="Module not found")
    if payload.position > len(modules):
        raise HTTPException(status_code=422, detail="Target position exceeds module count")
    ordered = [item for item in modules if item.id != module_id]
    ordered.insert(payload.position - 1, moving)
    for position, item in enumerate(ordered, start=1):
        item.position = position
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.module.reordered", entity_type="course_module", entity_id=str(module_id), metadata={"course_id": str(course_id), "position": payload.position})
    await db.commit()
    return {"status": "reordered", "module_id": str(module_id), "position": payload.position}

@router.patch("/{course_id}/modules/{module_id}/lessons/{lesson_id}/position", response_model=dict)
async def move_lesson(
    course_id: UUID,
    module_id: UUID,
    lesson_id: UUID,
    payload: PositionUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    module = await db.scalar(select(CourseModule).join(Course).where(CourseModule.id == module_id, Course.id == course_id, Course.tenant_id == user.tenant_id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    result = await db.execute(select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position.asc()))
    lessons = list(result.scalars().all())
    moving = next((item for item in lessons if item.id == lesson_id), None)
    if moving is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if payload.position > len(lessons):
        raise HTTPException(status_code=422, detail="Target position exceeds lesson count")
    ordered = [item for item in lessons if item.id != lesson_id]
    ordered.insert(payload.position - 1, moving)
    for position, item in enumerate(ordered, start=1):
        item.position = position
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="lesson.reordered", entity_type="lesson", entity_id=str(lesson_id), metadata={"course_id": str(course_id), "module_id": str(module_id), "position": payload.position})
    await db.commit()
    return {"status": "reordered", "lesson_id": str(lesson_id), "position": payload.position}

@router.patch("/{course_id}/modules/{module_id}", response_model=dict)
async def update_module(
    course_id: UUID,
    module_id: UUID,
    payload: ModuleUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    module = await db.scalar(
        select(CourseModule).join(Course).where(
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    values = payload.model_dump(exclude_unset=True)
    values.pop("change_note", None)
    for field, value in values.items():
        setattr(module, field, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.module.updated", entity_type="course_module", entity_id=str(module.id), metadata={"fields": sorted(values)})
    await db.commit()
    await db.refresh(module)
    return {"id": str(module.id), "title": module.title, "description": module.description, "position": module.position}


@router.patch("/{course_id}/modules/{module_id}/lessons/{lesson_id}", response_model=dict)
async def update_lesson(
    course_id: UUID,
    module_id: UUID,
    lesson_id: UUID,
    payload: LessonUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    lesson = await db.scalar(
        select(Lesson).join(CourseModule, CourseModule.id == Lesson.module_id).join(Course).where(
            Lesson.id == lesson_id,
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    values = payload.model_dump(exclude_unset=True)
    change_note = values.pop("change_note", None)
    content_changed = any(field in values for field in ("title", "content_type", "content"))
    if content_changed:
        await validate_lesson_content(
            db,
            tenant_id=user.tenant_id,
            content_type=values.get("content_type", lesson.content_type),
            content=values.get("content", lesson.content),
        )
    for field, value in values.items():
        setattr(lesson, field, value)
    if content_changed:
        await record_content_version(db, tenant_id=user.tenant_id, lesson=lesson, changed_by=user.id, change_note=change_note or "Lesson content updated")
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="lesson.updated", entity_type="lesson", entity_id=str(lesson.id), metadata={"fields": sorted(values), "versioned": content_changed})
    await db.commit()
    await db.refresh(lesson)
    return {"id": str(lesson.id), "title": lesson.title, "content_type": lesson.content_type, "content": lesson.content, "position": lesson.position}



@router.delete("/{course_id}/modules/{module_id}", response_model=dict)
async def delete_module(
    course_id: UUID,
    module_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    module = await db.scalar(
        select(CourseModule).join(Course).where(
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    lessons_result = await db.execute(select(Lesson).where(Lesson.module_id == module.id))
    lessons = list(lessons_result.scalars().all())
    for lesson in lessons:
        await db.delete(lesson)
    await db.delete(module)
    remaining_result = await db.execute(
        select(CourseModule).where(CourseModule.course_id == course_id).order_by(CourseModule.position.asc())
    )
    for position, remaining in enumerate(remaining_result.scalars().all(), start=1):
        remaining.position = position
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="course.module.deleted", entity_type="course_module", entity_id=str(module_id),
        metadata={"lesson_count": len(lessons)},
    )
    await db.commit()
    return {"id": str(module_id), "deleted": True, "lesson_count": len(lessons)}

@router.delete("/{course_id}/modules/{module_id}/lessons/{lesson_id}", response_model=dict)
async def delete_lesson(
    course_id: UUID,
    module_id: UUID,
    lesson_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    lesson = await db.scalar(
        select(Lesson).join(CourseModule, CourseModule.id == Lesson.module_id).join(Course).where(
            Lesson.id == lesson_id,
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await db.delete(lesson)
    remaining_result = await db.execute(
        select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position.asc())
    )
    for position, remaining in enumerate(remaining_result.scalars().all(), start=1):
        remaining.position = position
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="lesson.deleted", entity_type="lesson", entity_id=str(lesson_id),
        metadata={"module_id": str(module_id)},
    )
    await db.commit()
    return {"id": str(lesson_id), "deleted": True}

@router.get("/{course_id}/modules/{module_id}/lessons/{lesson_id}/versions", response_model=list[ContentVersionOut])
async def list_lesson_versions(
    course_id: UUID,
    module_id: UUID,
    lesson_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    lesson = await db.scalar(
        select(Lesson).join(CourseModule, CourseModule.id == Lesson.module_id).join(Course).where(
            Lesson.id == lesson_id,
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    result = await db.execute(select(CourseContentVersion).where(
        CourseContentVersion.lesson_id == lesson.id,
        CourseContentVersion.tenant_id == user.tenant_id,
    ).order_by(CourseContentVersion.version_number.desc()))
    return list(result.scalars().all())


@router.post("/{course_id}/modules/{module_id}/lessons/{lesson_id}/versions/{version_number}/restore", response_model=dict)
async def restore_lesson_version(
    course_id: UUID,
    module_id: UUID,
    lesson_id: UUID,
    version_number: int,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    lesson = await db.scalar(
        select(Lesson).join(CourseModule, CourseModule.id == Lesson.module_id).join(Course).where(
            Lesson.id == lesson_id,
            CourseModule.id == module_id,
            Course.id == course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    version = await db.scalar(select(CourseContentVersion).where(
        CourseContentVersion.lesson_id == lesson_id,
        CourseContentVersion.tenant_id == user.tenant_id,
        CourseContentVersion.version_number == version_number,
    ))
    if lesson is None or version is None:
        raise HTTPException(status_code=404, detail="Content version not found")
    lesson.title = version.title
    lesson.content_type = version.content_type
    lesson.content = version.content
    await record_content_version(db, tenant_id=user.tenant_id, lesson=lesson, changed_by=user.id, change_note=f"Restored from version {version_number}")
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="lesson.version.restored", entity_type="lesson", entity_id=str(lesson.id), metadata={"restored_version": version_number})
    await db.commit()
    await db.refresh(lesson)
    return {"id": str(lesson.id), "title": lesson.title, "content_type": lesson.content_type, "content": lesson.content, "position": lesson.position}


@router.post("/{course_id}/publish", response_model=CourseOut)
async def publish_course(
    course_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    lesson_count = await db.scalar(
        select(func.count(Lesson.id))
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .where(CourseModule.course_id == course.id)
    )
    if not lesson_count:
        raise HTTPException(status_code=422, detail="Course must contain at least one lesson")
    result = await db.execute(select(Lesson).join(CourseModule, CourseModule.id == Lesson.module_id).where(
        CourseModule.course_id == course.id,
    ))
    for lesson in result.scalars().all():
        try:
            await validate_lesson_content(
                db,
                tenant_id=user.tenant_id,
                content_type=lesson.content_type,
                content=lesson.content or {},
            )
        except HTTPException as exc:
            raise HTTPException(status_code=422, detail=f"Complete the content for lesson '{lesson.title}': {exc.detail}") from exc
    course.status = "published"
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.published", entity_type="course", entity_id=str(course.id))
    await db.commit()
    await db.refresh(course)
    return course

@router.post("/{course_id}/enroll", response_model=EnrollmentOut)
async def enroll(
    course_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(
        select(Course)
        .where(Course.id == course_id, Course.tenant_id == user.tenant_id, Course.status == "published")
        .with_for_update()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Published course not found")
    if course.visibility == "private" or course.enrollment_policy == "assignment_only":
        raise HTTPException(status_code=404, detail="Course is not open for self-enrollment")
    if course.audience_org_units:
        if user.org_unit_id is None or str(user.org_unit_id) not in {str(item) for item in course.audience_org_units}:
            raise HTTPException(status_code=403, detail="You are outside this course audience")
    if course.prerequisites:
        completed_count = await db.scalar(select(func.count(func.distinct(Enrollment.course_id))).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.user_id == user.id,
            Enrollment.course_id.in_(course.prerequisites),
            Enrollment.status == "completed",
        ))
        if completed_count != len(course.prerequisites):
            raise HTTPException(status_code=422, detail="Complete all prerequisite courses before enrolling")
    existing = await db.scalar(select(Enrollment).where(
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.course_id == course.id,
        Enrollment.user_id == user.id,
    ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()))
    if existing and existing.status != "rejected":
        return existing

    enrollment_status = "pending_approval" if course.enrollment_policy == "approval" else "enrolled"
    if enrollment_status == "enrolled" and course.capacity:
        active_count = await db.scalar(select(func.count(Enrollment.id)).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_([ "enrolled", "in_progress" ]),
        )) or 0
        if active_count >= course.capacity:
            enrollment_status = "waitlisted"

    if existing and existing.status == "rejected":
        enrollment = existing
        enrollment.status = enrollment_status
        enrollment.completed_at = None
    else:
        enrollment = Enrollment(
            tenant_id=user.tenant_id,
            course_id=course.id,
            user_id=user.id,
            status=enrollment_status,
            source="self",
        )
        db.add(enrollment)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="enrollment.created",
        entity_type="enrollment",
        entity_id=str(enrollment.id),
        metadata={"source": "self", "status": enrollment_status},
    )
    title = {
        "pending_approval": "Enrollment request submitted",
        "waitlisted": "Course waitlist confirmed",
    }.get(enrollment_status, "Course enrollment confirmed")
    body = {
        "pending_approval": f"Your request for {course.title} is awaiting L&D approval.",
        "waitlisted": f"{course.title} is currently full. You have been added to the waitlist.",
    }.get(enrollment_status, f"You are enrolled in {course.title}.")
    await create_notification(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        notification_type="learning.enrollment",
        title=title,
        body=body,
    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment

@router.post("/{course_id}/enrollments/bulk", response_model=list[EnrollmentOut])
async def bulk_enroll(
    course_id: UUID,
    payload: BulkEnrollmentCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(
        select(Course)
        .where(Course.id == course_id, Course.tenant_id == user.tenant_id, Course.status == "published")
        .with_for_update()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Published course not found")

    requested_ids = list(dict.fromkeys(payload.user_ids))
    users_result = await db.execute(select(User).where(
        User.tenant_id == user.tenant_id,
        User.id.in_(requested_ids),
        User.is_active.is_(True),
    ))
    users = {item.id: item for item in users_result.scalars().all()}
    missing = [str(item) for item in requested_ids if item not in users]
    if missing:
        raise HTTPException(status_code=422, detail={"invalid_user_ids": missing})

    existing_result = await db.execute(select(Enrollment).where(
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.course_id == course.id,
        Enrollment.user_id.in_(requested_ids),
    ).order_by(Enrollment.created_at.asc(), Enrollment.id.asc()))
    existing = {item.user_id: item for item in existing_result.scalars().all()}
    active_count = 0
    if course.capacity:
        active_count = await db.scalar(select(func.count(Enrollment.id)).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_([ "enrolled", "in_progress" ]),
        )) or 0
    created: list[Enrollment] = []
    for user_id in requested_ids:
        enrollment = existing.get(user_id)
        if enrollment:
            if payload.due_at is not None:
                enrollment.due_at = payload.due_at
            continue
        enrollment_status = "enrolled"
        if course.capacity and active_count >= course.capacity:
            enrollment_status = "waitlisted"
        else:
            active_count += 1
        enrollment = Enrollment(
            tenant_id=user.tenant_id,
            course_id=course.id,
            user_id=user_id,
            status=enrollment_status,
            source="admin",
            due_at=payload.due_at,
        )
        db.add(enrollment)
        created.append(enrollment)
        await create_notification(
            db,
            tenant_id=user.tenant_id,
            user_id=user_id,
            notification_type="learning.enrollment",
            title="New course assignment",
            body=(
                f"You have been assigned {course.title}."
                if enrollment_status == "enrolled"
                else f"{course.title} is currently full. You have been added to the waitlist."
            ),
        )
    await db.flush()
    for enrollment in created:
        await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="enrollment.created",
                    entity_type="enrollment", entity_id=str(enrollment.id),
                    metadata={"source": "bulk", "course_id": str(course.id)})
    await db.commit()
    result = await db.execute(select(Enrollment).where(
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.course_id == course.id,
        Enrollment.user_id.in_(requested_ids),
    ).order_by(Enrollment.created_at.asc(), Enrollment.id.asc()))
    latest = {item.user_id: item for item in result.scalars().all()}
    return list(latest.values())


class ManagerEnrollmentCreate(BaseModel):
    user_id: UUID
    due_at: datetime | None = None


@router.post("/{course_id}/manager-assignment", response_model=EnrollmentOut)
async def manager_assignment(
    course_id: UUID,
    payload: ManagerEnrollmentCreate,
    manager: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(
        select(Course).where(
            Course.id == course_id,
            Course.tenant_id == manager.tenant_id,
            Course.status == "published",
        ).with_for_update()
    )
    learner = await db.scalar(select(User).where(
        User.id == payload.user_id,
        User.tenant_id == manager.tenant_id,
        User.is_active.is_(True),
    ))
    if course is None or learner is None:
        raise HTTPException(status_code=404, detail="Published course or learner not found")
    if learner.manager_id != manager.id:
        raise HTTPException(status_code=403, detail="Manager scope does not include this learner")
    existing = await db.scalar(select(Enrollment).where(
        Enrollment.tenant_id == manager.tenant_id,
        Enrollment.course_id == course.id,
        Enrollment.user_id == learner.id,
    ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()))
    if existing and existing.status != "rejected":
        if payload.due_at is not None:
            existing.due_at = payload.due_at
            await db.commit()
            await db.refresh(existing)
        return existing

    active_count = 0
    if course.capacity:
        active_count = await db.scalar(select(func.count(Enrollment.id)).where(
            Enrollment.tenant_id == manager.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_(["enrolled", "in_progress"]),
        )) or 0
    enrollment_status = "waitlisted" if course.capacity and active_count >= course.capacity else "enrolled"
    enrollment = existing if existing and existing.status == "rejected" else Enrollment(
        tenant_id=manager.tenant_id,
        course_id=course.id,
        user_id=learner.id,
        status=enrollment_status,
        source="manager",
        due_at=payload.due_at,
    )
    if existing and existing.status == "rejected":
        enrollment.status = enrollment_status
        enrollment.due_at = payload.due_at
        enrollment.completed_at = None
    else:
        db.add(enrollment)
    await db.flush()
    await create_notification(
        db,
        tenant_id=manager.tenant_id,
        user_id=learner.id,
        notification_type="learning.enrollment",
        title="Manager course assignment",
        body=f"Your manager assigned you to {course.title}."
        if enrollment_status == "enrolled"
        else f"{course.title} is full. Your manager placed you on the waitlist.",
    )
    await audit(
        db,
        tenant_id=manager.tenant_id,
        actor_id=manager.id,
        action="enrollment.created",
        entity_type="enrollment",
        entity_id=str(enrollment.id),
        metadata={"source": "manager", "course_id": str(course.id), "learner_id": str(learner.id)},
    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("/operations/enrollment-queue")
async def operations_enrollment_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: str = Query(default="all", alias="status", pattern=r"^(all|pending_approval|waitlisted)$"),
    q: str = Query(default="", max_length=100),
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    statuses = ("pending_approval", "waitlisted")
    counts_result = await db.execute(
        select(Enrollment.status, func.count(Enrollment.id))
        .where(Enrollment.tenant_id == user.tenant_id, Enrollment.status.in_(statuses))
        .group_by(Enrollment.status)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}
    filters = [
        Enrollment.tenant_id == user.tenant_id,
        Course.tenant_id == user.tenant_id,
        User.tenant_id == user.tenant_id,
        Enrollment.status.in_(statuses),
    ]
    if status_filter != "all":
        filters.append(Enrollment.status == status_filter)
    if q.strip():
        term = f"%{q.strip()}%"
        filters.append(or_(Course.title.ilike(term), User.email.ilike(term),
                           User.first_name.ilike(term), User.last_name.ilike(term)))
    base = select(Enrollment).join(Course, Course.id == Enrollment.course_id).join(User, User.id == Enrollment.user_id).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    result = await db.execute(
        select(Enrollment, Course, User)
        .join(Course, Course.id == Enrollment.course_id)
        .join(User, User.id == Enrollment.user_id)
        .where(*filters)
        .order_by(Enrollment.created_at.asc(), Enrollment.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "pending_approval": counts.get("pending_approval", 0),
        "waitlisted": counts.get("waitlisted", 0),
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(enrollment.id),
                "course_id": str(course.id),
                "course_title": course.title,
                "learner_id": str(learner.id),
                "learner_name": f"{learner.first_name} {learner.last_name}",
                "learner_email": learner.email,
                "status": enrollment.status,
                "requested_at": enrollment.created_at,
                "source": enrollment.source,
            }
            for enrollment, course, learner in result.all()
        ],
    }

@router.get("/{course_id}/enrollments/queue", response_model=list[EnrollmentOut])
async def enrollment_queue(
    course_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    result = await db.execute(
        select(Enrollment)
        .where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_([ "pending_approval", "waitlisted" ]),
        )
        .order_by(Enrollment.created_at.asc())
    )
    return list(result.scalars().all())


@router.post("/{course_id}/enrollments/{enrollment_id}/approve", response_model=EnrollmentOut)
async def approve_enrollment(
    course_id: UUID,
    enrollment_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(
        select(Course)
        .where(Course.id == course_id, Course.tenant_id == user.tenant_id)
        .with_for_update()
    )
    enrollment = await db.scalar(select(Enrollment).where(
        Enrollment.id == enrollment_id,
        Enrollment.course_id == course_id,
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.status.in_([ "pending_approval", "waitlisted" ]),
    ))
    if course is None or enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment queue item not found")
    if course.capacity:
        active_count = await db.scalar(select(func.count(Enrollment.id)).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_([ "enrolled", "in_progress" ]),
        )) or 0
        if active_count >= course.capacity:
            enrollment.status = "waitlisted"
            await db.commit()
            await db.refresh(enrollment)
            return enrollment
    enrollment.status = "enrolled"
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="enrollment.approved",
                entity_type="enrollment", entity_id=str(enrollment.id))
    await create_notification(
        db,
        tenant_id=user.tenant_id,
        user_id=enrollment.user_id,
        notification_type="learning.enrollment",
        title="Enrollment approved",
        body=f"Your enrollment in {course.title} has been approved.",
    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.post("/{course_id}/enrollments/{enrollment_id}/reject", response_model=EnrollmentOut)
async def reject_enrollment(
    course_id: UUID,
    enrollment_id: UUID,
    payload: EnrollmentDecision | None = None,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    enrollment = await db.scalar(select(Enrollment).join(Course, Course.id == Enrollment.course_id).where(
        Enrollment.id == enrollment_id,
        Enrollment.course_id == course_id,
        Enrollment.tenant_id == user.tenant_id,
        Course.tenant_id == user.tenant_id,
        Enrollment.status.in_([ "pending_approval", "waitlisted" ]),
    ))
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment queue item not found")
    enrollment.status = "rejected"
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    reason = payload.reason.strip() if payload and payload.reason else None
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="enrollment.rejected",
                entity_type="enrollment", entity_id=str(enrollment.id), metadata={"reason": reason})
    await create_notification(
        db, tenant_id=user.tenant_id, user_id=enrollment.user_id,
        notification_type="learning.enrollment", title="Enrollment request declined",
        body=f"Your request for {course.title if course else 'a course'} was declined." + (f" Reason: {reason}" if reason else ""),
    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("/my/enrollments", response_model=list[EnrollmentOut])
async def my_enrollments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Enrollment)
        .where(Enrollment.tenant_id == user.tenant_id, Enrollment.user_id == user.id)
        .order_by(Enrollment.created_at.desc())
    )
    return list(result.scalars().all())
@router.post("/my/enrollments/{enrollment_id}/lessons/{lesson_id}/complete", response_model=EnrollmentOut)
async def complete_lesson(
    enrollment_id: UUID,
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enrollment = await db.scalar(select(Enrollment).where(
        Enrollment.id == enrollment_id,
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.user_id == user.id,
    ).with_for_update())
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.status not in {"enrolled", "in_progress", "completed"}:
        raise HTTPException(status_code=409, detail=f"Learning access is not active while enrollment is {enrollment.status}")
    lesson = await db.scalar(
        select(Lesson)
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .join(Course, Course.id == CourseModule.course_id)
        .where(Lesson.id == lesson_id, Course.id == enrollment.course_id, Course.tenant_id == user.tenant_id)
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if enrollment.status == "completed":
        return enrollment
    progress = await db.scalar(select(LessonProgress).where(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.lesson_id == lesson.id,
    ))
    if progress is None:
        progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id, status="completed", progress_percent=100, completed_at=datetime.now(timezone.utc))
        db.add(progress)
    else:
        progress.status = "completed"
        progress.progress_percent = 100
        progress.completed_at = datetime.now(timezone.utc)
    total = await db.scalar(
        select(func.count(Lesson.id))
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .where(CourseModule.course_id == enrollment.course_id)
    )
    completed = await db.scalar(select(func.count(LessonProgress.id)).where(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.status == "completed",
    ))
    course_completed = bool(total and completed and completed >= total)
    if course_completed:
        enrollment.status = "completed"
        enrollment.completed_at = datetime.now(timezone.utc)
        obligations = (await db.scalars(select(ComplianceAssignment).where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.user_id == user.id,
            ComplianceAssignment.course_id == enrollment.course_id,
            ComplianceAssignment.status.in_(["assigned", "due_soon", "overdue", "evidence_submitted"]),
        ))).all()
        for obligation in obligations:
            obligation.status = "completed"
            await audit(
                db, tenant_id=user.tenant_id, actor_id=user.id,
                action="compliance.assignment.completed_by_course",
                entity_type="compliance_assignment", entity_id=str(obligation.id),
                metadata={"course_id": str(enrollment.course_id)},
            )

        course = await db.scalar(
            select(Course).where(
                Course.id == enrollment.course_id,
                Course.tenant_id == user.tenant_id,
            )
        )
        mappings = await db.execute(
            select(CourseSkill).where(CourseSkill.course_id == enrollment.course_id)
        )
        for mapping in mappings.scalars().all():
            skill = await db.scalar(
                select(UserSkill).where(
                    UserSkill.user_id == user.id,
                    UserSkill.skill_id == mapping.skill_id,
                )
            )
            evidence = f"course_completion:{enrollment.course_id}"
            if skill is None:
                skill = UserSkill(
                    user_id=user.id,
                    skill_id=mapping.skill_id,
                    proficiency=mapping.target_proficiency,
                    evidence_source=evidence,
                )
                db.add(skill)
                await db.flush()
            else:
                if skill.proficiency < mapping.target_proficiency:
                    skill.proficiency = mapping.target_proficiency
                skill.evidence_source = evidence
            await audit(
                db,
                tenant_id=user.tenant_id,
                actor_id=user.id,
                action="skill.evidence.derived_from_course_completion",
                entity_type="user_skill",
                entity_id=str(skill.id),
                metadata={
                    "course_id": str(enrollment.course_id),
                    "skill_id": str(mapping.skill_id),
                    "target_proficiency": mapping.target_proficiency,
                },
            )
    else:
        enrollment.status = "in_progress"

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="lesson.completed",
        entity_type="lesson",
        entity_id=str(lesson.id),
    )
    if course_completed:
        course = course or await db.scalar(select(Course).where(Course.id == enrollment.course_id))
        await create_notification(
            db,
            tenant_id=user.tenant_id,
            user_id=user.id,
            notification_type="learning.course_completed",
            title="Course completed",
            body=f"You completed {course.title if course else 'your course'}.",
        )
        if course and course.capacity:
            active_count = await db.scalar(select(func.count(Enrollment.id)).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.course_id == course.id,
                Enrollment.status.in_([ "enrolled", "in_progress" ]),
            )) or 0
            if active_count < course.capacity:
                next_waitlisted = await db.scalar(
                    select(Enrollment)
                    .where(
                        Enrollment.tenant_id == user.tenant_id,
                        Enrollment.course_id == course.id,
                        Enrollment.status == "waitlisted",
                    )
                    .order_by(Enrollment.created_at.asc())
                )
                if next_waitlisted is not None:
                    next_waitlisted.status = "enrolled"
                    await audit(
                        db,
                        tenant_id=user.tenant_id,
                        actor_id=user.id,
                        action="enrollment.waitlist.promoted",
                        entity_type="enrollment",
                        entity_id=str(next_waitlisted.id),
                    )
                    await create_notification(
                        db,
                        tenant_id=user.tenant_id,
                        user_id=next_waitlisted.user_id,
                        notification_type="learning.enrollment",
                        title="A course seat is now available",
                        body=f"You have been promoted from the waitlist for {course.title}.",
                    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment
