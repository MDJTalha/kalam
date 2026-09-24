from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import Cohort, CohortMember, Course, Enrollment, LearningPath, LearningPathItem, Program, ProgramCourse, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class ProgramCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    is_required: bool = False

class CourseItemCreate(BaseModel):
    course_id: UUID
    position: int = Field(ge=1)
    is_required: bool = True

class PathCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None

class PathItemCreate(BaseModel):
    course_id: UUID
    position: int = Field(ge=1)
    prerequisite_item_id: UUID | None = None

class CohortCreate(BaseModel):
    name: str = Field(min_length=3, max_length=240)
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    status: str = Field(default="planned", pattern=r"^(planned|active|completed|cancelled)$")

class CohortMemberCreate(BaseModel):
    user_id: UUID

@router.get("")
async def list_programs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Program)
        .where(Program.tenant_id == user.tenant_id)
        .order_by(Program.title)
    )
    return list(result.scalars().all())

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_program(
    payload: ProgramCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    duplicate = await db.scalar(
        select(Program).where(
            Program.tenant_id == user.tenant_id,
            Program.slug == payload.slug,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Program slug already exists")
    program = Program(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(program)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="program.created",
        entity_type="program",
        entity_id=str(program.id),
    )
    await db.commit()
    return {"id": str(program.id), "title": program.title, "slug": program.slug}

@router.post("/{program_id}/courses", status_code=status.HTTP_201_CREATED)
async def add_program_course(
    program_id: UUID,
    payload: CourseItemCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    program = await db.scalar(
        select(Program).where(
            Program.id == program_id,
            Program.tenant_id == user.tenant_id,
        )
    )
    course = await db.scalar(
        select(Course).where(
            Course.id == payload.course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if program is None or course is None:
        raise HTTPException(status_code=404, detail="Program or course not found")

    duplicate = await db.scalar(
        select(ProgramCourse).where(
            ProgramCourse.program_id == program.id,
            ProgramCourse.course_id == course.id,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Course is already in this program")

    row = ProgramCourse(program_id=program.id, **payload.model_dump())
    db.add(row)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="program.course.added",
        entity_type="program_course",
        entity_id=str(program.id),
        metadata={"course_id": str(course.id)},
    )
    await db.commit()
    return {"status": "added", "program_id": str(program.id), "course_id": str(course.id)}

@router.get("/cohorts")
async def list_cohorts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Cohort)
        .where(Cohort.tenant_id == user.tenant_id)
        .order_by(Cohort.starts_at.nulls_last(), Cohort.name)
    )
    return [
        {
            "id": str(item.id),
            "program_id": str(item.program_id),
            "name": item.name,
            "code": item.code,
            "starts_at": item.starts_at,
            "ends_at": item.ends_at,
            "capacity": item.capacity,
            "status": item.status,
        }
        for item in result.scalars().all()
    ]


@router.post("/{program_id}/cohorts", status_code=status.HTTP_201_CREATED)
async def create_cohort(
    program_id: UUID,
    payload: CohortCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    program = await db.scalar(
        select(Program).where(
            Program.id == program_id,
            Program.tenant_id == user.tenant_id,
        )
    )
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    if payload.ends_at and payload.starts_at and payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="Cohort end must be after start")

    duplicate = await db.scalar(
        select(Cohort).where(
            Cohort.tenant_id == user.tenant_id,
            Cohort.code == payload.code,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Cohort code already exists")

    cohort = Cohort(
        tenant_id=user.tenant_id,
        program_id=program.id,
        **payload.model_dump(),
    )
    db.add(cohort)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="cohort.created",
        entity_type="cohort",
        entity_id=str(cohort.id),
    )
    await db.commit()
    return {"id": str(cohort.id), "program_id": str(program.id), "code": cohort.code}


@router.post("/cohorts/{cohort_id}/members", status_code=status.HTTP_201_CREATED)
async def add_cohort_member(
    cohort_id: UUID,
    payload: CohortMemberCreate,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    cohort = await db.scalar(
        select(Cohort).where(
            Cohort.id == cohort_id,
            Cohort.tenant_id == user.tenant_id,
        )
    )
    learner = await db.scalar(
        select(User).where(
            User.id == payload.user_id,
            User.tenant_id == user.tenant_id,
            User.is_active.is_(True),
        )
    )
    if cohort is None or learner is None:
        raise HTTPException(status_code=404, detail="Cohort or learner not found")

    existing = await db.scalar(
        select(CohortMember).where(
            CohortMember.cohort_id == cohort.id,
            CohortMember.user_id == learner.id,
        )
    )
    if existing:
        return {"status": "already_member"}

    if cohort.capacity is not None:
        member_count = await db.scalar(
            select(func.count()).select_from(CohortMember).where(
                CohortMember.cohort_id == cohort.id,
                CohortMember.status == "active",
            )
        )
        if (member_count or 0) >= cohort.capacity:
            raise HTTPException(status_code=409, detail="Cohort capacity reached")

    db.add(CohortMember(cohort_id=cohort.id, user_id=learner.id))
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="cohort.member.added",
        entity_type="cohort_member",
        entity_id=str(learner.id),
        metadata={"cohort_id": str(cohort.id)},
    )
    await db.commit()
    return {"status": "added", "cohort_id": str(cohort.id), "user_id": str(learner.id)}


@router.post("/cohorts/{cohort_id}/launch")
async def launch_cohort(
    cohort_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    cohort = await db.scalar(
        select(Cohort).where(
            Cohort.id == cohort_id,
            Cohort.tenant_id == user.tenant_id,
        )
    )
    if cohort is None:
        raise HTTPException(status_code=404, detail="Cohort not found")

    members_result = await db.execute(
        select(CohortMember).where(
            CohortMember.cohort_id == cohort.id,
            CohortMember.status == "active",
        )
    )
    courses_result = await db.execute(
        select(ProgramCourse).where(ProgramCourse.program_id == cohort.program_id)
    )
    members = list(members_result.scalars().all())
    courses = list(courses_result.scalars().all())

    created = 0
    for member in members:
        for item in courses:
            existing = await db.scalar(
                select(Enrollment).where(
                    Enrollment.tenant_id == user.tenant_id,
                    Enrollment.user_id == member.user_id,
                    Enrollment.course_id == item.course_id,
                )
            )
            if existing is None:
                db.add(
                    Enrollment(
                        tenant_id=user.tenant_id,
                        user_id=member.user_id,
                        course_id=item.course_id,
                        status="enrolled",
                        source="cohort",
                    )
                )
                created += 1

    cohort.status = "active"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="cohort.launched",
        entity_type="cohort",
        entity_id=str(cohort.id),
        metadata={"members": len(members), "courses": len(courses), "enrollments_created": created},
    )
    await db.commit()
    return {
        "status": "active",
        "cohort_id": str(cohort.id),
        "members": len(members),
        "courses": len(courses),
        "enrollments_created": created,
    }


@router.get("/cohorts/{cohort_id}")
async def get_cohort(
    cohort_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cohort = await db.scalar(
        select(Cohort).where(
            Cohort.id == cohort_id,
            Cohort.tenant_id == user.tenant_id,
        )
    )
    if cohort is None:
        raise HTTPException(status_code=404, detail="Cohort not found")

    result = await db.execute(
        select(CohortMember, User)
        .join(User, User.id == CohortMember.user_id)
        .where(CohortMember.cohort_id == cohort.id)
        .order_by(User.last_name, User.first_name)
    )
    return {
        "id": str(cohort.id),
        "program_id": str(cohort.program_id),
        "name": cohort.name,
        "code": cohort.code,
        "status": cohort.status,
        "starts_at": cohort.starts_at,
        "ends_at": cohort.ends_at,
        "capacity": cohort.capacity,
        "members": [
            {
                "user_id": str(member.user_id),
                "name": f"{person.first_name} {person.last_name}",
                "email": person.email,
                "status": member.status,
            }
            for member, person in result.all()
        ],
    }


@router.get("/{program_id}")
async def get_program(
    program_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    program = await db.scalar(
        select(Program).where(
            Program.id == program_id,
            Program.tenant_id == user.tenant_id,
        )
    )
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")

    result = await db.execute(
        select(ProgramCourse, Course)
        .join(Course, Course.id == ProgramCourse.course_id)
        .where(ProgramCourse.program_id == program.id)
        .order_by(ProgramCourse.position)
    )
    return {
        "id": str(program.id),
        "title": program.title,
        "slug": program.slug,
        "description": program.description,
        "status": program.status,
        "is_required": program.is_required,
        "courses": [
            {
                "course_id": str(item.course_id),
                "title": course.title,
                "position": item.position,
                "is_required": item.is_required,
            }
            for item, course in result.all()
        ],
    }

@router.get("/paths/all")
async def list_learning_paths(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningPath)
        .where(LearningPath.tenant_id == user.tenant_id)
        .order_by(LearningPath.title)
    )
    return list(result.scalars().all())

@router.post("/paths", status_code=status.HTTP_201_CREATED)
async def create_learning_path(
    payload: PathCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    duplicate = await db.scalar(
        select(LearningPath).where(
            LearningPath.tenant_id == user.tenant_id,
            LearningPath.slug == payload.slug,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Learning path slug already exists")
    path = LearningPath(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(path)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="learning_path.created",
        entity_type="learning_path",
        entity_id=str(path.id),
    )
    await db.commit()
    return {"id": str(path.id), "title": path.title, "slug": path.slug}

@router.post("/paths/{path_id}/courses", status_code=status.HTTP_201_CREATED)
async def add_learning_path_item(
    path_id: UUID,
    payload: PathItemCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    path = await db.scalar(
        select(LearningPath).where(
            LearningPath.id == path_id,
            LearningPath.tenant_id == user.tenant_id,
        )
    )
    course = await db.scalar(
        select(Course).where(
            Course.id == payload.course_id,
            Course.tenant_id == user.tenant_id,
        )
    )
    if path is None or course is None:
        raise HTTPException(status_code=404, detail="Learning path or course not found")

    duplicate = await db.scalar(
        select(LearningPathItem).where(
            LearningPathItem.path_id == path.id,
            LearningPathItem.course_id == course.id,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Course is already in this learning path")

    row = LearningPathItem(path_id=path.id, **payload.model_dump())
    db.add(row)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="learning_path.course.added",
        entity_type="learning_path_item",
        entity_id=str(path.id),
        metadata={"course_id": str(course.id)},
    )
    await db.commit()
    return {"status": "added", "path_id": str(path.id), "course_id": str(course.id)}

@router.get("/paths/{path_id}")
async def get_learning_path(
    path_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    path = await db.scalar(
        select(LearningPath).where(
            LearningPath.id == path_id,
            LearningPath.tenant_id == user.tenant_id,
        )
    )
    if path is None:
        raise HTTPException(status_code=404, detail="Learning path not found")

    result = await db.execute(
        select(LearningPathItem, Course)
        .join(Course, Course.id == LearningPathItem.course_id)
        .where(LearningPathItem.path_id == path.id)
        .order_by(LearningPathItem.position)
    )
    return {
        "id": str(path.id),
        "title": path.title,
        "slug": path.slug,
        "description": path.description,
        "status": path.status,
        "items": [
            {
                "course_id": str(item.course_id),
                "title": course.title,
                "position": item.position,
                "prerequisite_item_id": str(item.prerequisite_item_id) if item.prerequisite_item_id else None,
            }
            for item, course in result.all()
        ],
    }
