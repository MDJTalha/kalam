from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import Course, CourseModule, Enrollment, Lesson, LessonProgress, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()

class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)

class ModuleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    description: str | None = None
    position: int = Field(ge=1)

class LessonCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    content_type: str = "rich_text"
    content: dict = Field(default_factory=dict)
    position: int = Field(ge=1)

class CourseOut(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str | None
    status: str
    estimated_minutes: int | None
    model_config = {"from_attributes": True}

class EnrollmentOut(BaseModel):
    id: UUID
    course_id: UUID
    user_id: UUID
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    model_config = {"from_attributes": True}

@router.get("", response_model=list[CourseOut])
async def list_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Course)
        .where(Course.tenant_id == user.tenant_id)
        .where(Course.status == "published")
        .order_by(Course.title.asc())
    )
    return list(result.scalars().all())

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
            Course.status == "published",
        )
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    modules_result = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course.id)
        .order_by(CourseModule.position.asc())
    )
    modules = list(modules_result.scalars().all())
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
                        "content": lesson.content,
                        "position": lesson.position,
                    }
                    for lesson in lessons_result.scalars().all()
                ],
            }
        )
    enrollment = await db.scalar(
        select(Enrollment).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.course_id == course.id,
            Enrollment.user_id == user.id,
        )
    )
    return {
        "id": str(course.id),
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "status": course.status,
        "estimated_minutes": course.estimated_minutes,
        "modules": payload,
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
    course = Course(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(course)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="course.created", entity_type="course", entity_id=str(course.id))
    await db.commit()
    await db.refresh(course)
    return course

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
    lesson = Lesson(module_id=module.id, **payload.model_dump())
    db.add(lesson)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="lesson.created", entity_type="lesson", entity_id=str(lesson.id))
    await db.commit()
    return {"id": str(lesson.id), "title": lesson.title, "position": lesson.position}
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
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id, Course.status == "published"))
    if course is None:
        raise HTTPException(status_code=404, detail="Published course not found")
    existing = await db.scalar(select(Enrollment).where(
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.course_id == course.id,
        Enrollment.user_id == user.id,
    ))
    if existing:
        return existing
    enrollment = Enrollment(
        tenant_id=user.tenant_id,
        course_id=course.id,
        user_id=user.id,
        status="enrolled",
        source="self",
    )
    db.add(enrollment)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="enrollment.created", entity_type="enrollment", entity_id=str(enrollment.id))
    await create_notification(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        notification_type="learning.enrollment",
        title="Course enrollment confirmed",
        body=f"You are enrolled in {course.title}.",
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
    ))
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    lesson = await db.scalar(
        select(Lesson)
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .join(Course, Course.id == CourseModule.course_id)
        .where(Lesson.id == lesson_id, Course.id == enrollment.course_id, Course.tenant_id == user.tenant_id)
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
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
        course = await db.scalar(select(Course).where(Course.id == enrollment.course_id))
        await create_notification(
            db,
            tenant_id=user.tenant_id,
            user_id=user.id,
            notification_type="learning.course_completed",
            title="Course completed",
            body=f"You completed {course.title if course else 'your course'}.",
        )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment
