import csv
from io import StringIO
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import ComplianceAssignment, ComplianceEvidence, ComplianceException, ComplianceRequirement, ComplianceRequirementVersion, Course, Enrollment, FileObject, Role, User, UserRole
from app.db.session import get_db
from app.api.routes.files import ALLOWED_MIME_TYPES
from app.services.file_scanner import FileScanError, scan_file
from app.services.storage import get_storage
from app.services.audit import audit
from app.services.compliance_operations import run_compliance_operations_for_tenant

router = APIRouter()

OPEN_ASSIGNMENT_STATUSES = ("assigned", "due_soon", "overdue", "evidence_submitted", "exception_requested")
CLOSED_ASSIGNMENT_STATUSES = {"completed", "excepted"}


def requirement_snapshot(item: ComplianceRequirement) -> dict:
    return {"name": item.name, "description": item.description, "due_days": item.due_days,
            "recurrence_days": item.recurrence_days, "active": item.active, "rules": item.rules or {}}


async def requirement_applies_to_user(
    requirement: ComplianceRequirement,
    user: User,
    db: AsyncSession,
) -> bool:
    """Evaluate the controlled Phase 5 audience rules against one learner."""
    rules = requirement.rules or {}
    role_names = {str(value).strip().lower() for value in rules.get("role_names", []) if str(value).strip()}
    org_unit_ids = {str(value) for value in rules.get("org_unit_ids", [])}
    job_titles = {str(value).strip().lower() for value in rules.get("job_titles", []) if str(value).strip()}
    exclude_user_ids = {str(value) for value in rules.get("exclude_user_ids", [])}
    if str(user.id) in exclude_user_ids:
        return False
    include_rules = bool(role_names or org_unit_ids or job_titles)
    if not include_rules:
        return True
    if org_unit_ids and str(user.org_unit_id) in org_unit_ids:
        return True
    if job_titles and (user.job_title or "").strip().lower() in job_titles:
        return True
    if role_names:
        result = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, Role.tenant_id == user.tenant_id)
        )
        if any((name or "").strip().lower() in role_names for (name,) in result.all()):
            return True
    return False


class RequirementCreate(BaseModel):
    name: str = Field(min_length=3, max_length=240)
    description: str | None = None
    recurrence_days: int | None = Field(default=None, ge=1)
    due_days: int | None = Field(default=30, ge=1)
    active: bool = True
    rules: dict = Field(default_factory=dict)

    @field_validator("rules")
    @classmethod
    def validate_rules(cls, rules: dict) -> dict:
        allowed = {"role_names", "job_titles", "org_unit_ids", "exclude_user_ids", "escalation_days"}
        if set(rules) - allowed:
            raise ValueError("Unsupported applicability rule")
        for key in allowed - {"escalation_days"}:
            values = rules.get(key, [])
            if not isinstance(values, list) or len(values) > 100 or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{key} must be a list of nonempty strings (up to 100)")
            if key in {"org_unit_ids", "exclude_user_ids"}:
                try:
                    for value in values:
                        UUID(value)
                except ValueError as exc:
                    raise ValueError(f"{key} must contain valid identifiers") from exc
        days = rules.get("escalation_days", 7)
        if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 365:
            raise ValueError("escalation_days must be between 1 and 365")
        return rules


class RequirementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = None
    recurrence_days: int | None = Field(default=None, ge=1)
    due_days: int | None = Field(default=None, ge=1)
    active: bool | None = None
    rules: dict | None = None

    @field_validator("rules")
    @classmethod
    def validate_optional_rules(cls, rules: dict | None) -> dict | None:
        return RequirementCreate.validate_rules(rules) if rules is not None else None


class AssignmentCreate(BaseModel):
    user_id: UUID
    course_id: UUID | None = None

class BulkAssignmentCreate(BaseModel):
    course_id: UUID | None = None


class EvidenceCreate(BaseModel):
    evidence_type: str = Field(min_length=2, max_length=50)
    reference: str = Field(min_length=1, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)

class EvidenceRejection(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class ExceptionCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)
    expires_at: datetime


async def ensure_compliance_enrollment(db: AsyncSession, *, tenant_id: UUID, learner_id: UUID,
                                       course: Course, due_at: datetime, actor_id: UUID) -> None:
    existing = await db.scalar(select(Enrollment).where(
        Enrollment.tenant_id == tenant_id, Enrollment.user_id == learner_id,
        Enrollment.course_id == course.id,
    ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()))
    if existing and existing.status in {"enrolled", "in_progress", "waitlisted", "pending_approval"}:
        return
    active = await db.scalar(select(func.count(Enrollment.id)).where(
        Enrollment.tenant_id == tenant_id, Enrollment.course_id == course.id,
        Enrollment.status.in_(["enrolled", "in_progress"]),
    )) or 0
    next_status = "waitlisted" if course.capacity and active >= course.capacity else "enrolled"
    if existing and existing.status == "rejected":
        existing.status = next_status
        existing.due_at = due_at
        existing.source = "compliance"
    else:
        db.add(Enrollment(tenant_id=tenant_id, user_id=learner_id, course_id=course.id,
                          due_at=due_at, status=next_status, source="compliance"))
    await audit(db, tenant_id=tenant_id, actor_id=actor_id,
                action="compliance.learning.enrolled", entity_type="course", entity_id=str(course.id),
                metadata={"learner_id": str(learner_id), "status": next_status})



@router.post("/operations/run")
async def run_compliance_operations(
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    return await run_compliance_operations_for_tenant(db, user.tenant_id, user.id)


@router.get("/operations/summary")
async def compliance_operations_summary(
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    open_assignments = list(
        (
            await db.scalars(
                select(ComplianceAssignment).where(
                    ComplianceAssignment.tenant_id == user.tenant_id,
                    ComplianceAssignment.status.in_(OPEN_ASSIGNMENT_STATUSES),
                )
            )
        ).all()
    )
    expiring_exceptions = (
        await db.scalar(
            select(func.count(ComplianceException.id)).where(
                ComplianceException.tenant_id == user.tenant_id,
                ComplianceException.status == "approved",
                ComplianceException.expires_at.is_not(None),
                ComplianceException.expires_at <= now + timedelta(days=7),
            )
        )
        or 0
    )
    return {
        "generated_at": now,
        "open_assignments": len(open_assignments),
        "overdue": sum(
            1
            for item in open_assignments
            if item.due_at and item.due_at < now
        ),
        "evidence_review": sum(
            1 for item in open_assignments if item.status == "evidence_submitted"
        ),
        "exception_review": sum(
            1 for item in open_assignments if item.status == "exception_requested"
        ),
        "expiring_exceptions_7d": expiring_exceptions,
    }


@router.get("")
async def list_requirements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.tenant_id == user.tenant_id).order_by(ComplianceRequirement.name).limit(100)
    )
    requirements = list(result.scalars().all())
    if await user_has_permission(user, db, "compliance.manage"):
        return requirements
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "description": item.description,
            "recurrence_days": item.recurrence_days,
            "due_days": item.due_days,
            "active": item.active,
        }
        for item in requirements
        if item.active and await requirement_applies_to_user(item, user, db)
    ]

@router.get("/page")
async def page_requirements(
    q: str | None = Query(default=None, max_length=240),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [ComplianceRequirement.tenant_id == user.tenant_id]
    if q and q.strip():
        filters.append(ComplianceRequirement.name.ilike(f"%{q.strip()}%"))
    total = int(await db.scalar(select(func.count(ComplianceRequirement.id)).where(*filters)) or 0)
    result = await db.execute(
        select(ComplianceRequirement).where(*filters).order_by(ComplianceRequirement.name).offset((page - 1) * page_size).limit(page_size)
    )
    items = list(result.scalars().all())
    if await user_has_permission(user, db, "compliance.manage"):
        output_items: list[ComplianceRequirement | dict[str, object]] = items
    else:
        output_items = [
            {
                "id": str(item.id), "name": item.name, "description": item.description,
                "recurrence_days": item.recurrence_days, "due_days": item.due_days, "active": item.active,
            }
            for item in items if item.active and await requirement_applies_to_user(item, user, db)
        ]
    return {"items": output_items, "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201)
async def create_requirement(payload: RequirementCreate, user: User = Depends(require_permission("compliance.manage")), db: AsyncSession = Depends(get_db)):
    item = ComplianceRequirement(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    db.add(ComplianceRequirementVersion(requirement_id=item.id, version=item.version,
                                        tenant_id=user.tenant_id, snapshot=requirement_snapshot(item),
                                        changed_by=user.id))
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="compliance.requirement.created", entity_type="compliance_requirement", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "name": item.name}

@router.patch("/{requirement_id}")
async def update_requirement(requirement_id: UUID, payload: RequirementUpdate,
                             user: User = Depends(require_permission("compliance.manage")),
                             db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(ComplianceRequirement).where(
        ComplianceRequirement.id == requirement_id,
        ComplianceRequirement.tenant_id == user.tenant_id,
    ).with_for_update())
    if item is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=422, detail="Requirement name is required")
    if "rules" in changes and changes["rules"] is None:
        raise HTTPException(status_code=422, detail="Applicability rules must be an object")
    if "active" in changes and changes["active"] is None:
        raise HTTPException(status_code=422, detail="Active must be a boolean")
    if "due_days" in changes and changes["due_days"] is None:
        raise HTTPException(status_code=422, detail="Due days must be at least one")
    changes = {key: value for key, value in changes.items() if getattr(item, key) != value}
    if not changes:
        return {"id": str(item.id), "active": item.active, "version": item.version}
    for key, value in changes.items():
        setattr(item, key, value)
    item.version += 1
    db.add(ComplianceRequirementVersion(requirement_id=item.id, version=item.version,
                                        tenant_id=user.tenant_id, snapshot=requirement_snapshot(item),
                                        changed_by=user.id))
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="compliance.requirement.updated", entity_type="compliance_requirement",
                entity_id=str(item.id), metadata={"fields": list(changes)})
    await db.commit()
    return {"id": str(item.id), "active": item.active}


@router.get("/{requirement_id}/versions")
async def list_requirement_versions(
    requirement_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    requirement = await db.scalar(select(ComplianceRequirement.id).where(
        ComplianceRequirement.id == requirement_id,
        ComplianceRequirement.tenant_id == user.tenant_id,
    ))
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    result = await db.scalars(select(ComplianceRequirementVersion).where(
        ComplianceRequirementVersion.requirement_id == requirement_id,
        ComplianceRequirementVersion.tenant_id == user.tenant_id,
    ).order_by(ComplianceRequirementVersion.version.desc()))
    return [{"version": item.version, "snapshot": item.snapshot,
             "changed_by": str(item.changed_by) if item.changed_by else None,
             "created_at": item.created_at} for item in result.all()]


@router.get("/courses")
async def list_compliance_courses(
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    courses = (await db.scalars(select(Course).where(
        Course.tenant_id == user.tenant_id, Course.status == "published",
    ).order_by(Course.title).limit(100))).all()
    return [{"id": str(course.id), "title": course.title} for course in courses]


@router.get("/courses/page")
async def page_compliance_courses(
    q: str | None = Query(default=None, max_length=240),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    filters = [Course.tenant_id == user.tenant_id, Course.status == "published"]
    if q and q.strip():
        filters.append(Course.title.ilike(f"%{q.strip()}%"))
    total = int(await db.scalar(select(func.count(Course.id)).where(*filters)) or 0)
    result = await db.execute(
        select(Course.id, Course.title).where(*filters).order_by(Course.title).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "items": [{"id": str(course_id), "title": title} for course_id, title in result.all()],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{requirement_id}/preview")
async def preview_compliance_audience(
    requirement_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    requirement = await db.scalar(select(ComplianceRequirement).where(
        ComplianceRequirement.id == requirement_id,
        ComplianceRequirement.tenant_id == user.tenant_id,
    ))
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    learners = (await db.scalars(select(User).where(
        User.tenant_id == user.tenant_id, User.is_active.is_(True),
    ))).all()
    matching = 0
    already_open = 0
    for learner in learners:
        if not await requirement_applies_to_user(requirement, learner, db):
            continue
        matching += 1
        open_item = await db.scalar(select(ComplianceAssignment.id).where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.requirement_id == requirement.id,
            ComplianceAssignment.user_id == learner.id,
            ComplianceAssignment.status.in_(OPEN_ASSIGNMENT_STATUSES),
        ))
        if open_item:
            already_open += 1
    return {"active_learners": len(learners), "matching": matching,
            "already_open": already_open, "eligible": matching - already_open}


@router.post("/{requirement_id}/assign", status_code=201)
async def assign_requirement(requirement_id: UUID, payload: AssignmentCreate, user: User = Depends(require_permission("compliance.manage")), db: AsyncSession = Depends(get_db)):
    req = await db.scalar(select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id, ComplianceRequirement.tenant_id == user.tenant_id).with_for_update())
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if req is None or learner is None:
        raise HTTPException(status_code=404, detail="Requirement or user not found")
    if not req.active:
        raise HTTPException(status_code=409, detail="Inactive requirements cannot be assigned")
    if not await requirement_applies_to_user(req, learner, db):
        raise HTTPException(status_code=422, detail="Learner is outside the requirement applicability rules")
    existing = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.requirement_id == req.id,
            ComplianceAssignment.user_id == learner.id,
            ComplianceAssignment.status.in_(OPEN_ASSIGNMENT_STATUSES),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="This learner already has an open assignment for the requirement")
    if payload.course_id:
        course = await db.scalar(select(Course).where(Course.id == payload.course_id, Course.tenant_id == user.tenant_id,
                                                Course.status == "published").with_for_update())
        if course is None:
            raise HTTPException(status_code=404, detail="Published course not found")
    due = datetime.now(timezone.utc).replace(microsecond=0)
    if req.due_days:
        from datetime import timedelta
        due += timedelta(days=req.due_days)
    item = ComplianceAssignment(tenant_id=user.tenant_id, requirement_id=req.id, requirement_version=req.version, user_id=learner.id, course_id=payload.course_id, due_at=due, status="assigned")
    db.add(item)
    await db.flush()
    if payload.course_id and course is not None:
        await ensure_compliance_enrollment(db, tenant_id=user.tenant_id, learner_id=learner.id,
                                           course=course, due_at=due, actor_id=user.id)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="compliance.assignment.created", entity_type="compliance_assignment", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "status": item.status, "due_at": item.due_at}


@router.post("/{requirement_id}/assign-applicable", status_code=201)
async def assign_requirement_to_applicable_users(
    requirement_id: UUID,
    payload: BulkAssignmentCreate,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Create idempotent assignments for every active learner matching the rule set."""
    req = await db.scalar(
        select(ComplianceRequirement).where(
            ComplianceRequirement.id == requirement_id,
            ComplianceRequirement.tenant_id == user.tenant_id,
            ComplianceRequirement.active.is_(True),
        ).with_for_update()
    )
    if req is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    course_id = payload.course_id
    if course_id:
        course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id,
                                                Course.status == "published").with_for_update())
        if course is None:
            raise HTTPException(status_code=404, detail="Published course not found")
    learners = await db.scalars(
        select(User).where(User.tenant_id == user.tenant_id, User.is_active.is_(True)).order_by(User.email)
    )
    created = 0
    skipped = 0
    from datetime import timedelta
    due = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=req.due_days or 30)
    for learner in learners.all():
        if not await requirement_applies_to_user(req, learner, db):
            skipped += 1
            continue
        existing = await db.scalar(
            select(ComplianceAssignment.id).where(
                ComplianceAssignment.tenant_id == user.tenant_id,
                ComplianceAssignment.requirement_id == req.id,
                ComplianceAssignment.user_id == learner.id,
                ComplianceAssignment.status.in_(OPEN_ASSIGNMENT_STATUSES),
            )
        )
        if existing:
            skipped += 1
            continue
        db.add(ComplianceAssignment(
            tenant_id=user.tenant_id,
            requirement_id=req.id,
            requirement_version=req.version,
            user_id=learner.id,
            course_id=course_id,
            due_at=due,
            status="assigned",
        ))
        if course_id and course is not None:
            await ensure_compliance_enrollment(db, tenant_id=user.tenant_id, learner_id=learner.id,
                                               course=course, due_at=due, actor_id=user.id)
        created += 1
    await audit(
        db, tenant_id=user.tenant_id, actor_id=user.id,
        action="compliance.assignment.bulk_applicable",
        entity_type="compliance_requirement", entity_id=str(req.id),
        metadata={"created": created, "skipped": skipped},
    )
    await db.commit()
    return {"requirement_id": str(req.id), "created": created, "skipped": skipped}


@router.get("/reports/export")
async def export_compliance_assignments(
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement, ComplianceRequirementVersion, User, Course)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .outerjoin(ComplianceRequirementVersion, and_(
            ComplianceRequirementVersion.requirement_id == ComplianceAssignment.requirement_id,
            ComplianceRequirementVersion.version == ComplianceAssignment.requirement_version,
        ))
        .join(User, User.id == ComplianceAssignment.user_id)
        .outerjoin(Course, Course.id == ComplianceAssignment.course_id)
        .where(ComplianceAssignment.tenant_id == user.tenant_id)
        .order_by(ComplianceAssignment.due_at.asc().nulls_last(), User.email.asc())
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Assignment ID", "Requirement", "Policy version", "Learner", "Email", "Course",
                     "Status", "Due at (UTC)", "Assigned at (UTC)"])
    def safe(value: object) -> str:
        text = str(value or "")
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
    for assignment, requirement, version, learner, course in result.all():
        writer.writerow([safe(assignment.id), safe(version.snapshot.get("name") if version else requirement.name),
                         assignment.requirement_version,
                         safe(f"{learner.first_name} {learner.last_name}".strip()),
                         safe(learner.email), safe(course.title if course else ""),
                         safe(assignment.status), safe(assignment.due_at),
                         safe(assignment.created_at)])
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="compliance-assignments.csv"'})


@router.get("/reports")
async def compliance_report(
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Return an audit-ready tenant compliance snapshot from persisted records."""
    requirements = (await db.scalars(
        select(ComplianceRequirement).where(ComplianceRequirement.tenant_id == user.tenant_id)
    )).all()
    assignments = (await db.scalars(
        select(ComplianceAssignment).where(ComplianceAssignment.tenant_id == user.tenant_id)
    )).all()
    exceptions = (await db.scalars(
        select(ComplianceException).where(ComplianceException.tenant_id == user.tenant_id)
    )).all()
    by_status: dict[str, int] = {}
    for assignment in assignments:
        by_status[assignment.status] = by_status.get(assignment.status, 0) + 1
    now = datetime.now(timezone.utc)
    pending_evidence = await db.scalar(
        select(func.count(func.distinct(ComplianceEvidence.assignment_id))).where(
            ComplianceEvidence.tenant_id == user.tenant_id,
            ComplianceEvidence.verified_at.is_(None),
            ComplianceEvidence.rejected_at.is_(None),
            ComplianceAssignment.status == "evidence_submitted",
        ).join(ComplianceAssignment, ComplianceAssignment.id == ComplianceEvidence.assignment_id)
    ) or 0
    terminal_statuses = {"completed", "excepted"}
    return {
        "generated_at": datetime.now(timezone.utc),
        "requirements": len(requirements),
        "active_requirements": sum(1 for item in requirements if item.active),
        "assignments": len(assignments),
        "assignments_by_status": by_status,
        "overdue": sum(1 for item in assignments if item.status == "overdue" or (item.due_at and item.due_at < now and item.status not in terminal_statuses)),
        "completed": sum(1 for item in assignments if item.status == "completed"),
        "exceptions": len(exceptions),
        "approved_exceptions": sum(1 for item in exceptions if item.status == "approved"),
        "requested_exceptions": sum(1 for item in exceptions if item.status == "requested"),
        "pending_evidence": pending_evidence,
    }


@router.get("/my")
async def my_compliance(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement, ComplianceRequirementVersion, Course)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .outerjoin(ComplianceRequirementVersion, and_(
            ComplianceRequirementVersion.requirement_id == ComplianceAssignment.requirement_id,
            ComplianceRequirementVersion.version == ComplianceAssignment.requirement_version,
        ))
        .outerjoin(Course, Course.id == ComplianceAssignment.course_id)
        .where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.user_id == user.id,
        )
        .order_by(ComplianceAssignment.due_at.asc().nulls_last())
    )
    rejections = (await db.scalars(select(ComplianceEvidence).where(
        ComplianceEvidence.tenant_id == user.tenant_id,
        ComplianceEvidence.user_id == user.id,
        ComplianceEvidence.rejected_at.is_not(None),
    ).order_by(ComplianceEvidence.rejected_at.desc()))).all()
    latest_rejection = {item.assignment_id: item.rejection_reason for item in reversed(rejections)}
    return [
        {
            "id": str(item.id),
            "requirement": (version.snapshot.get("name") if version else req.name),
            "requirement_version": item.requirement_version,
            "status": item.status,
            "rejection_reason": latest_rejection.get(item.id),
            "due_state": "overdue" if item.due_at and item.due_at < datetime.now(timezone.utc) and item.status not in {"completed", "excepted"} else item.status,
            "due_at": item.due_at,
            "course_id": str(item.course_id) if item.course_id else None,
            "course_title": course.title if course else None,
            "description": (version.snapshot.get("description") if version else req.description),
        }
        for item, req, version, course in result.all()
    ]


@router.get("/assignments")
async def list_compliance_assignments(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    filters = [ComplianceAssignment.tenant_id == user.tenant_id]
    if status:
        filters.append(ComplianceAssignment.status == status)
    total = await db.scalar(select(func.count(ComplianceAssignment.id)).where(*filters))
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement, ComplianceRequirementVersion, User)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .outerjoin(ComplianceRequirementVersion, and_(
            ComplianceRequirementVersion.requirement_id == ComplianceAssignment.requirement_id,
            ComplianceRequirementVersion.version == ComplianceAssignment.requirement_version,
        ))
        .join(User, User.id == ComplianceAssignment.user_id)
        .where(*filters)
        .order_by(ComplianceAssignment.due_at.asc().nulls_last(), User.email.asc())
        .offset(offset)
        .limit(limit)
    )
    return {
        "total": total or 0,
        "items": [
            {
                "id": str(item.id),
                "requirement": version.snapshot.get("name") if version else req.name,
                "requirement_version": item.requirement_version,
                "user_id": str(learner.id),
                "user_name": f"{learner.first_name} {learner.last_name}".strip() or learner.email,
                "user_email": learner.email,
                "status": item.status,
                "due_at": item.due_at,
                "due_state": "overdue" if item.due_at and item.due_at < datetime.now(timezone.utc) and item.status not in {"completed", "excepted"} else item.status,
                "course_id": str(item.course_id) if item.course_id else None,
            }
            for item, req, version, learner in result.all()
        ],
    }


@router.get("/exceptions")
async def list_compliance_exceptions(
    status: str | None = None,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    filters = [ComplianceException.tenant_id == user.tenant_id]
    if status:
        filters.append(ComplianceException.status == status)
    result = await db.execute(
        select(ComplianceException, ComplianceAssignment, ComplianceRequirement, ComplianceRequirementVersion, User)
        .join(ComplianceAssignment, ComplianceAssignment.id == ComplianceException.assignment_id)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .outerjoin(ComplianceRequirementVersion, and_(
            ComplianceRequirementVersion.requirement_id == ComplianceAssignment.requirement_id,
            ComplianceRequirementVersion.version == ComplianceAssignment.requirement_version,
        ))
        .join(User, User.id == ComplianceAssignment.user_id)
        .where(*filters)
        .order_by(ComplianceException.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "assignment_id": str(assignment.id),
            "requirement": version.snapshot.get("name") if version else req.name,
            "user_name": f"{learner.first_name} {learner.last_name}".strip() or learner.email,
            "user_email": learner.email,
            "reason": item.reason,
            "status": item.status,
            "expires_at": item.expires_at,
            "created_at": item.created_at,
        }
        for item, assignment, req, version, learner in result.all()
    ]


@router.post("/my/{assignment_id}/upload", status_code=201)
async def upload_my_compliance_evidence(
    assignment_id: UUID,
    upload: UploadFile = File(...),
    notes: str | None = Form(default=None, max_length=2000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.scalar(select(ComplianceAssignment).where(
        ComplianceAssignment.id == assignment_id,
        ComplianceAssignment.tenant_id == user.tenant_id,
        ComplianceAssignment.user_id == user.id,
    ).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if assignment.status in CLOSED_ASSIGNMENT_STATUSES or assignment.status == "exception_requested" or assignment.course_id:
        raise HTTPException(status_code=409, detail="Complete the assigned course or resolve the exception")
    pending = await db.scalar(select(ComplianceEvidence.id).where(
        ComplianceEvidence.assignment_id == assignment.id,
        ComplianceEvidence.verified_at.is_(None),
        ComplianceEvidence.rejected_at.is_(None),
    ))
    if pending:
        raise HTTPException(status_code=409, detail="Evidence is already awaiting review")
    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    if not upload.filename:
        raise HTTPException(status_code=422, detail="Filename is required")
    storage = get_storage()
    try:
        object_key, size_bytes = await storage.save_upload(user.tenant_id, upload)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    try:
        clean, scanner = await scan_file(storage.path_for(object_key))
    except FileScanError as exc:
        storage.delete(object_key)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not clean:
        storage.delete(object_key)
        raise HTTPException(status_code=422, detail="File rejected by malware scanner")
    file_item = FileObject(
        tenant_id=user.tenant_id, uploaded_by=user.id, object_key=object_key,
        original_name=upload.filename[:255], mime_type=upload.content_type,
        size_bytes=size_bytes, status="available" if scanner != "not_configured" else "pending_scan",
        record_metadata={"scanner": scanner, "compliance_assignment_id": str(assignment.id)},
    )
    db.add(file_item)
    await db.flush()
    evidence = ComplianceEvidence(
        tenant_id=user.tenant_id, assignment_id=assignment.id, user_id=user.id,
        evidence_type="document", reference=f"file:{file_item.id}", notes=notes,
    )
    db.add(evidence)
    assignment.status = "evidence_submitted"
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="compliance.evidence.file_uploaded", entity_type="compliance_evidence",
                entity_id=str(evidence.id), metadata={"file_id": str(file_item.id), "scan_status": file_item.status})
    await db.commit()
    return {"id": str(evidence.id), "status": "submitted", "scan_status": file_item.status}


@router.post("/my/{assignment_id}/evidence", status_code=201)
async def add_my_compliance_evidence(
    assignment_id: UUID,
    payload: EvidenceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.user_id == user.id,
        ).with_for_update()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if assignment.status in CLOSED_ASSIGNMENT_STATUSES or assignment.status == "exception_requested" or assignment.course_id:
        raise HTTPException(status_code=409, detail="Complete the assigned course or resolve the exception")

    pending = await db.scalar(select(ComplianceEvidence.id).where(
        ComplianceEvidence.assignment_id == assignment.id,
        ComplianceEvidence.tenant_id == user.tenant_id,
        ComplianceEvidence.verified_at.is_(None),
        ComplianceEvidence.rejected_at.is_(None),
    ))
    if pending:
        raise HTTPException(status_code=409, detail="Evidence is already awaiting review")
    if payload.evidence_type == "document":
        raise HTTPException(status_code=422, detail="Upload a document through the evidence upload action")
    if payload.evidence_type == "url" and not payload.reference.startswith(("https://", "http://")):
        raise HTTPException(status_code=422, detail="A URL evidence reference must use HTTP or HTTPS")
    evidence = ComplianceEvidence(
        tenant_id=user.tenant_id,
        assignment_id=assignment.id,
        user_id=user.id,
        **payload.model_dump(),
    )
    db.add(evidence)
    if assignment.status not in {"completed", "excepted"}:
        assignment.status = "evidence_submitted"
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.evidence.submitted",
        entity_type="compliance_evidence",
        entity_id=str(evidence.id),
    )
    await db.commit()
    return {"id": str(evidence.id), "status": "submitted"}


@router.get("/evidence")
async def list_compliance_evidence_for_review(
    verified: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    filters = (
        ComplianceEvidence.tenant_id == user.tenant_id,
        ComplianceEvidence.verified_at.is_not(None) if verified else ComplianceEvidence.verified_at.is_(None),
        ComplianceAssignment.status == "evidence_submitted" if not verified else ComplianceAssignment.status.in_(["completed", "evidence_submitted"]),
        ComplianceEvidence.rejected_at.is_(None),
    )
    total = await db.scalar(
        select(func.count(ComplianceEvidence.id))
        .join(ComplianceAssignment, ComplianceAssignment.id == ComplianceEvidence.assignment_id)
        .where(*filters)
    ) or 0
    result = await db.execute(
        select(ComplianceEvidence, ComplianceAssignment, ComplianceRequirement, ComplianceRequirementVersion, User)
        .join(ComplianceAssignment, ComplianceAssignment.id == ComplianceEvidence.assignment_id)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .outerjoin(ComplianceRequirementVersion, and_(
            ComplianceRequirementVersion.requirement_id == ComplianceAssignment.requirement_id,
            ComplianceRequirementVersion.version == ComplianceAssignment.requirement_version,
        ))
        .join(User, User.id == ComplianceEvidence.user_id)
        .where(*filters)
        .order_by(ComplianceEvidence.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    file_ids = []
    for evidence, _, _, _, _ in rows:
        if evidence.reference.startswith("file:"):
            try:
                file_ids.append(UUID(evidence.reference.removeprefix("file:")))
            except ValueError:
                pass
    files = (await db.scalars(select(FileObject).where(
        FileObject.tenant_id == user.tenant_id, FileObject.id.in_(file_ids),
    ))).all() if file_ids else []
    file_status = {str(item.id): item.status for item in files}
    items = [
        {
            "id": str(item.id),
            "assignment_id": str(assignment.id),
            "requirement": version.snapshot.get("name") if version else req.name,
            "user_name": f"{learner.first_name} {learner.last_name}".strip() or learner.email,
            "user_email": learner.email,
            "user_id": str(learner.id),
            "evidence_type": item.evidence_type,
            "reference": item.reference,
            "attachment_status": file_status.get(item.reference.removeprefix("file:")) if item.reference.startswith("file:") else None,
            "notes": item.notes,
            "verified": item.verified_at is not None,
            "created_at": item.created_at,
        }
        for item, assignment, req, version, learner in rows
    ]
    return {"total": total, "items": items}


@router.get("/{assignment_id}/evidence")
async def list_compliance_evidence(
    assignment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        )
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if assignment.user_id != user.id and not await user_has_permission(user, db, "compliance.manage"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        select(ComplianceEvidence)
        .where(
            ComplianceEvidence.tenant_id == user.tenant_id,
            ComplianceEvidence.assignment_id == assignment.id,
        )
        .order_by(ComplianceEvidence.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "evidence_type": item.evidence_type,
            "reference": item.reference,
            "notes": item.notes,
            "verified": item.verified_at is not None,
            "verified_at": item.verified_at,
            "rejected_at": item.rejected_at,
            "rejection_reason": item.rejection_reason,
        }
        for item in result.scalars().all()
    ]


@router.post("/{assignment_id}/exceptions", status_code=201)
async def request_compliance_exception(
    assignment_id: UUID,
    payload: ExceptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if assignment.user_id != user.id and not await user_has_permission(user, db, "compliance.manage"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if assignment.status in CLOSED_ASSIGNMENT_STATUSES or assignment.status == "evidence_submitted":
        raise HTTPException(status_code=409, detail="Resolve pending evidence before requesting an exception")
    if payload.expires_at.tzinfo is None or payload.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="A future, time-zone-aware expiry is required")

    existing = await db.scalar(
        select(ComplianceException).where(
            ComplianceException.assignment_id == assignment.id,
            ComplianceException.status == "requested",
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="An exception request is already under review")
    item = ComplianceException(
        tenant_id=user.tenant_id,
        assignment_id=assignment.id,
        reason=payload.reason,
        expires_at=payload.expires_at,
        status="requested",
    )
    db.add(item)
    assignment.status = "exception_requested"
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.exception.requested",
        entity_type="compliance_exception",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status, "assignment_status": assignment.status}


@router.get("/evidence/{evidence_id}/download")
async def download_compliance_evidence(
    evidence_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    evidence = await db.scalar(select(ComplianceEvidence).where(
        ComplianceEvidence.id == evidence_id,
        ComplianceEvidence.tenant_id == user.tenant_id,
    ))
    if evidence is None or not evidence.reference.startswith("file:"):
        raise HTTPException(status_code=404, detail="Evidence attachment not found")
    if evidence.user_id != user.id and not await user_has_permission(user, db, "compliance.manage"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        file_id = UUID(evidence.reference.removeprefix("file:"))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Evidence attachment not found") from exc
    file_item = await db.scalar(select(FileObject).where(
        FileObject.id == file_id, FileObject.tenant_id == user.tenant_id,
        FileObject.status == "available",
    ))
    if file_item is None:
        raise HTTPException(status_code=404, detail="Attachment is awaiting clearance or unavailable")
    path = get_storage().path_for(file_item.object_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment content not found")
    return FileResponse(path, media_type=file_item.mime_type, filename=file_item.original_name)


@router.post("/evidence/{evidence_id}/reject")
async def reject_compliance_evidence(
    evidence_id: UUID,
    payload: EvidenceRejection,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    evidence = await db.scalar(select(ComplianceEvidence).where(
        ComplianceEvidence.id == evidence_id,
        ComplianceEvidence.tenant_id == user.tenant_id,
    ).with_for_update())
    if evidence is None:
        raise HTTPException(status_code=404, detail="Compliance evidence not found")
    if evidence.verified_at is not None or evidence.rejected_at is not None:
        raise HTTPException(status_code=409, detail="Evidence has already been reviewed")
    if evidence.user_id == user.id:
        raise HTTPException(status_code=403, detail="A different reviewer must review your evidence")
    assignment = await db.scalar(select(ComplianceAssignment).where(
        ComplianceAssignment.id == evidence.assignment_id,
        ComplianceAssignment.tenant_id == user.tenant_id,
    ).with_for_update())
    if assignment is None or assignment.status != "evidence_submitted":
        raise HTTPException(status_code=409, detail="The obligation is no longer awaiting evidence review")
    evidence.rejected_by = user.id
    evidence.rejected_at = datetime.now(timezone.utc)
    evidence.rejection_reason = payload.reason
    assignment.status = "overdue" if assignment.due_at and assignment.due_at < datetime.now(timezone.utc) else "assigned"
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="compliance.evidence.rejected", entity_type="compliance_evidence",
                entity_id=str(evidence.id), metadata={"reason": payload.reason})
    await db.commit()
    return {"status": "rejected", "evidence_id": str(evidence.id)}


@router.post("/evidence/{evidence_id}/verify")
async def verify_compliance_evidence(
    evidence_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    evidence = await db.scalar(
        select(ComplianceEvidence).where(
            ComplianceEvidence.id == evidence_id,
            ComplianceEvidence.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if evidence is None:
        raise HTTPException(status_code=404, detail="Compliance evidence not found")
    if evidence.verified_at is not None or evidence.rejected_at is not None:
        raise HTTPException(status_code=409, detail="Evidence has already been reviewed")
    if evidence.user_id == user.id:
        raise HTTPException(status_code=403, detail="A different reviewer must verify your evidence")
    assignment = await db.scalar(select(ComplianceAssignment).where(
        ComplianceAssignment.id == evidence.assignment_id,
        ComplianceAssignment.tenant_id == user.tenant_id,
    ).with_for_update())
    if assignment is None or assignment.status in CLOSED_ASSIGNMENT_STATUSES or assignment.status == "exception_requested":
        raise HTTPException(status_code=409, detail="The obligation is not awaiting evidence review")

    if evidence.reference.startswith("file:"):
        try:
            file_id = UUID(evidence.reference.removeprefix("file:"))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="Invalid evidence attachment") from exc
        cleared = await db.scalar(select(FileObject.id).where(
            FileObject.id == file_id, FileObject.tenant_id == user.tenant_id,
            FileObject.status == "available",
        ))
        if cleared is None:
            raise HTTPException(status_code=409, detail="The attachment must clear its security scan before verification")
    evidence.verified_by = user.id
    evidence.verified_at = datetime.now(timezone.utc)
    if assignment.course_id is None:
        assignment.status = "completed"

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.evidence.verified",
        entity_type="compliance_evidence",
        entity_id=str(evidence.id),
    )
    await db.commit()
    return {"status": "verified", "evidence_id": str(evidence.id)}


@router.post("/exceptions/{exception_id}/approve")
async def approve_compliance_exception(
    exception_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(ComplianceException).where(
            ComplianceException.id == exception_id,
            ComplianceException.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance exception not found")
    if item.status == "approved":
        return {"status": "already_approved", "exception_id": str(item.id)}
    if item.status != "requested":
        raise HTTPException(status_code=409, detail="Only requested exceptions can be approved")
    if item.expires_at is None or item.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="A future expiry is required before approval")
    item.status = "approved"
    item.approved_by = user.id
    item.approved_at = datetime.now(timezone.utc)
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == item.assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if assignment is None or assignment.status != "exception_requested":
        raise HTTPException(status_code=409, detail="The obligation is no longer awaiting exception review")
    assignment.status = "excepted"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.exception.approved",
        entity_type="compliance_exception",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"status": "approved", "exception_id": str(item.id)}


@router.post("/exceptions/{exception_id}/reject")
async def reject_compliance_exception(
    exception_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(ComplianceException).where(
            ComplianceException.id == exception_id,
            ComplianceException.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance exception not found")
    if item.status != "requested":
        raise HTTPException(status_code=409, detail="Only requested exceptions can be rejected")
    item.status = "rejected"
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == item.assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        ).with_for_update()
    )
    if assignment and assignment.status == "exception_requested":
        assignment.status = "overdue" if assignment.due_at and assignment.due_at < datetime.now(timezone.utc) else "assigned"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.exception.rejected",
        entity_type="compliance_exception",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"status": "rejected", "exception_id": str(item.id)}


@router.post("/my/{assignment_id}/complete")
async def complete_my_compliance(
    assignment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if item.status == "completed":
        return {"status": "already_completed"}
    if item.status in {"excepted", "exception_requested"}:
        raise HTTPException(status_code=409, detail="Resolve the exception before completing this obligation")

    if item.course_id:
        enrollment = await db.scalar(
            select(Enrollment).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.user_id == user.id,
                Enrollment.course_id == item.course_id,
                Enrollment.status == "completed",
                Enrollment.completed_at >= item.created_at,
            )
        )
        if enrollment is None:
            raise HTTPException(
                status_code=409,
                detail="Complete the assigned learning course before closing this compliance requirement",
            )
    else:
        raise HTTPException(
            status_code=409,
            detail="This requirement requires an administrator or compliance evidence workflow",
        )

    item.status = "completed"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.assignment.completed",
        entity_type="compliance_assignment",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"status": "completed", "assignment_id": str(item.id)}


@router.post("/{assignment_id}/complete")
async def complete_compliance_admin(
    assignment_id: UUID,
    user: User = Depends(require_permission("compliance.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")
    if item.status == "completed":
        return {"status": "already_completed"}
    if item.status in {"excepted", "exception_requested"}:
        raise HTTPException(status_code=409, detail="Resolve the exception before completing this obligation")
    if item.course_id:
        enrollment = await db.scalar(
            select(Enrollment).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.user_id == item.user_id,
                Enrollment.course_id == item.course_id,
                Enrollment.status == "completed",
                Enrollment.completed_at >= item.created_at,
            )
        )
        if enrollment is None:
            raise HTTPException(status_code=409, detail="The assigned learning course is not completed")
    else:
        evidence = await db.scalar(
            select(ComplianceEvidence.id).where(
                ComplianceEvidence.assignment_id == item.id,
                ComplianceEvidence.tenant_id == user.tenant_id,
                ComplianceEvidence.verified_at.is_not(None),
            )
        )
        if evidence is None:
            raise HTTPException(status_code=409, detail="Verify compliance evidence before closing this requirement")
    item.status = "completed"
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.assignment.completed_by_admin",
        entity_type="compliance_assignment",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"status": "completed", "assignment_id": str(item.id)}
