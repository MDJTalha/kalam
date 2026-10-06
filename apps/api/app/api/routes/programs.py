from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import Cohort, CohortMember, Course, Enrollment, LearningPath, LearningPathItem, Program, ProgramCourse, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class ProgramCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    is_required: bool = False

class ProgramUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = None
    is_required: bool | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|published)$")

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

class PathUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|published)$")

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
    statement = select(Program).where(Program.tenant_id == user.tenant_id)
    if not await user_has_permission(user, db, "courses.manage"):
        statement = statement.where(Program.status == "published")
    result = await db.execute(statement.order_by(Program.title))
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

@router.patch("/{program_id}")
async def update_program(
    program_id: UUID,
    payload: ProgramUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    program = await db.scalar(select(Program).where(
        Program.id == program_id, Program.tenant_id == user.tenant_id,
    ))
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if len(changes["title"]) < 3:
            raise HTTPException(status_code=422, detail="Program title is too short")
    if changes.get("status") == "draft":
        launched = await db.scalar(select(Cohort.id).where(
            Cohort.tenant_id == user.tenant_id, Cohort.program_id == program.id,
            Cohort.status == "active",
        ))
        if launched:
            raise HTTPException(status_code=409, detail="Active cohorts require this program to remain published")
    if changes.get("status") == "published":
        rows = await db.execute(select(Course.status).join(
            ProgramCourse, ProgramCourse.course_id == Course.id,
        ).where(ProgramCourse.program_id == program.id))
        course_statuses = list(rows.scalars().all())
        if not course_statuses or any(value != "published" for value in course_statuses):
            raise HTTPException(status_code=422, detail="Add published courses before publishing the program")
    for field, value in changes.items():
        setattr(program, field, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="program.updated", entity_type="program", entity_id=str(program.id),
                metadata={"fields": sorted(changes)})
    await db.commit()
    return {"id": str(program.id), "status": program.status, "title": program.title, "description": program.description, "is_required": program.is_required}

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
    if program.status == "published" and course.status != "published":
        raise HTTPException(status_code=422, detail="Published programs can contain only published courses")
    launched = await db.scalar(select(Cohort.id).where(
        Cohort.tenant_id == user.tenant_id, Cohort.program_id == program.id,
        Cohort.status == "active",
    ))
    if launched:
        raise HTTPException(status_code=409, detail="Active cohort delivery prevents changing program courses")
    occupied = await db.scalar(select(ProgramCourse.course_id).where(
        ProgramCourse.program_id == program.id, ProgramCourse.position == payload.position,
    ))
    if occupied:
        raise HTTPException(status_code=409, detail="This course position is already used")

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

@router.delete("/{program_id}/courses/{course_id}")
async def remove_program_course(
    program_id: UUID,
    course_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    program = await db.scalar(select(Program).where(
        Program.id == program_id, Program.tenant_id == user.tenant_id,
    ))
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    item = await db.scalar(select(ProgramCourse).where(
        ProgramCourse.program_id == program_id, ProgramCourse.course_id == course_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Program course not found")
    launched = await db.scalar(select(Cohort.id).where(
        Cohort.tenant_id == user.tenant_id, Cohort.program_id == program_id,
        Cohort.status == "active",
    ))
    if launched:
        raise HTTPException(status_code=409, detail="Active cohort delivery prevents changing program courses")
    if program.status == "published":
        count = await db.scalar(select(func.count()).select_from(ProgramCourse).where(
            ProgramCourse.program_id == program_id,
        ))
        if count == 1:
            raise HTTPException(status_code=409, detail="Return the program to draft before removing its last course")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="program.course.removed", entity_type="program_course",
                entity_id=str(program_id), metadata={"course_id": str(course_id)})
    await db.commit()
    return {"status": "removed"}

@router.get("/cohorts")
async def list_cohorts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Cohort).where(Cohort.tenant_id == user.tenant_id)
    if not await user_has_permission(user, db, "courses.manage"):
        statement = statement.where(
            Cohort.status == "active",
            Cohort.id.in_(select(CohortMember.cohort_id).where(CohortMember.user_id == user.id)),
        )
    result = await db.execute(statement.order_by(Cohort.starts_at.nulls_last(), Cohort.name))
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
    if cohort.status != "planned":
        raise HTTPException(status_code=409, detail="Learners can be added while the cohort is planned")

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
    return {
        "status": "added", "cohort_id": str(cohort.id), "user_id": str(learner.id),
        "name": f"{learner.first_name} {learner.last_name}".strip() or learner.email,
        "email": learner.email,
    }


@router.delete("/cohorts/{cohort_id}/members/{user_id}")
async def remove_cohort_member(
    cohort_id: UUID,
    user_id: UUID,
    user: User = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    cohort = await db.scalar(select(Cohort).where(
        Cohort.id == cohort_id, Cohort.tenant_id == user.tenant_id,
    ))
    if cohort is None:
        raise HTTPException(status_code=404, detail="Cohort not found")
    if cohort.status != "planned":
        raise HTTPException(status_code=409, detail="Launched cohort membership cannot be removed here")
    member = await db.scalar(select(CohortMember).where(
        CohortMember.cohort_id == cohort_id, CohortMember.user_id == user_id,
    ))
    if member is None:
        raise HTTPException(status_code=404, detail="Cohort member not found")
    await db.delete(member)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="cohort.member.removed", entity_type="cohort_member",
                entity_id=str(user_id), metadata={"cohort_id": str(cohort_id)})
    await db.commit()
    return {"status": "removed"}

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
    if cohort.status != "planned":
        raise HTTPException(status_code=409, detail="Only planned cohorts can be launched")
    program = await db.scalar(select(Program).where(
        Program.id == cohort.program_id, Program.tenant_id == user.tenant_id,
    ))
    if program is None or program.status != "published":
        raise HTTPException(status_code=422, detail="Publish the program before launching its cohort")

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
    if not members or not courses:
        raise HTTPException(status_code=422, detail="Add at least one learner and course before launch")

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
    can_manage = await user_has_permission(user, db, "courses.manage")
    if not can_manage:
        member = await db.scalar(select(CohortMember).where(
            CohortMember.cohort_id == cohort.id, CohortMember.user_id == user.id,
        ))
        if cohort.status != "active" or member is None:
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
            if can_manage or person.id == user.id
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
    if program is None or (program.status != "published" and not await user_has_permission(user, db, "courses.manage")):
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
    statement = select(LearningPath).where(LearningPath.tenant_id == user.tenant_id)
    if not await user_has_permission(user, db, "courses.manage"):
        statement = statement.where(LearningPath.status == "published")
    result = await db.execute(statement.order_by(LearningPath.title))
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

@router.patch("/paths/{path_id}")
async def update_learning_path(
    path_id: UUID,
    payload: PathUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    path = await db.scalar(select(LearningPath).where(
        LearningPath.id == path_id, LearningPath.tenant_id == user.tenant_id,
    ))
    if path is None:
        raise HTTPException(status_code=404, detail="Learning path not found")
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if len(changes["title"]) < 3:
            raise HTTPException(status_code=422, detail="Path title is too short")
    if changes.get("status") == "published":
        count = await db.scalar(select(func.count()).select_from(LearningPathItem).where(
            LearningPathItem.path_id == path.id,
        ))
        if not count:
            raise HTTPException(status_code=422, detail="Add a course before publishing the path")
        unpublished = await db.scalar(select(Course.id).join(
            LearningPathItem, LearningPathItem.course_id == Course.id,
        ).where(LearningPathItem.path_id == path.id, Course.status != "published"))
        if unpublished:
            raise HTTPException(status_code=422, detail="Publish all path courses first")
    for field, value in changes.items():
        setattr(path, field, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="learning_path.updated", entity_type="learning_path",
                entity_id=str(path.id), metadata={"fields": sorted(changes)})
    await db.commit()
    return {"id": str(path.id), "title": path.title, "description": path.description, "status": path.status}

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
    if path.status == "published" and course.status != "published":
        raise HTTPException(status_code=422, detail="Published paths can contain only published courses")
    occupied = await db.scalar(select(LearningPathItem).where(
        LearningPathItem.path_id == path.id, LearningPathItem.position == payload.position,
    ))
    if occupied:
        raise HTTPException(status_code=409, detail="This sequence position is already used")
    if payload.prerequisite_item_id:
        prerequisite = await db.scalar(select(LearningPathItem).where(
            LearningPathItem.path_id == path.id,
            LearningPathItem.course_id == payload.prerequisite_item_id,
        ))
        if prerequisite is None or prerequisite.position >= payload.position:
            raise HTTPException(status_code=422, detail="Prerequisite must be an earlier course in this path")

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


class PathPositionUpdate(BaseModel):
    position: int = Field(ge=1, le=1000)

@router.patch("/paths/{path_id}/courses/{course_id}/position")
async def move_learning_path_item(
    path_id: UUID,
    course_id: UUID,
    payload: PathPositionUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    path = await db.scalar(select(LearningPath).where(
        LearningPath.id == path_id,
        LearningPath.tenant_id == user.tenant_id,
    ))
    if path is None:
        raise HTTPException(status_code=404, detail="Learning path not found")
    result = await db.execute(select(LearningPathItem).where(
        LearningPathItem.path_id == path.id,
    ).order_by(LearningPathItem.position.asc()))
    items = list(result.scalars().all())
    moving = next((item for item in items if item.course_id == course_id), None)
    if moving is None:
        raise HTTPException(status_code=404, detail="Path course not found")
    target_index = payload.position - 1
    if target_index >= len(items):
        raise HTTPException(status_code=422, detail="Target position exceeds path length")
    ordered = [item for item in items if item.course_id != course_id]
    ordered.insert(target_index, moving)
    for position, item in enumerate(ordered, start=1):
        item.position = position
    for item in ordered:
        if item.prerequisite_item_id:
            prerequisite = next((candidate for candidate in ordered if candidate.course_id == item.prerequisite_item_id), None)
            if prerequisite is None or prerequisite.position >= item.position:
                raise HTTPException(status_code=422, detail="Reordering would place a prerequisite after its dependent course")
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="learning_path.course.reordered", entity_type="learning_path_item",
        entity_id=str(path.id), metadata={"course_id": str(course_id), "position": payload.position},
    )
    await db.commit()
    return {"status": "reordered", "course_id": str(course_id), "position": payload.position}

@router.delete("/paths/{path_id}/courses/{course_id}")
async def remove_learning_path_item(
    path_id: UUID,
    course_id: UUID,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    path = await db.scalar(select(LearningPath).where(
        LearningPath.id == path_id, LearningPath.tenant_id == user.tenant_id,
    ))
    if path is None:
        raise HTTPException(status_code=404, detail="Learning path not found")
    item = await db.scalar(select(LearningPathItem).where(
        LearningPathItem.path_id == path_id, LearningPathItem.course_id == course_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Path course not found")
    if path.status == "published":
        count = await db.scalar(select(func.count()).select_from(LearningPathItem).where(
            LearningPathItem.path_id == path_id,
        ))
        if count == 1:
            raise HTTPException(status_code=409, detail="Return the path to draft before removing its last course")
    dependent = await db.scalar(select(LearningPathItem.course_id).where(
        LearningPathItem.path_id == path_id,
        LearningPathItem.prerequisite_item_id == course_id,
    ))
    if dependent:
        raise HTTPException(status_code=409, detail="Remove courses that depend on this prerequisite first")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="learning_path.course.removed", entity_type="learning_path_item",
                entity_id=str(path_id), metadata={"course_id": str(course_id)})
    await db.commit()
    return {"status": "removed"}

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
    if path is None or (path.status != "published" and not await user_has_permission(user, db, "courses.manage")):
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
