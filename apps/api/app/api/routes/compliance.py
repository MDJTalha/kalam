from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import ComplianceAssignment, ComplianceEvidence, ComplianceException, ComplianceRequirement, Course, Enrollment, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class RequirementCreate(BaseModel):
    name: str = Field(min_length=3, max_length=240)
    description: str | None = None
    recurrence_days: int | None = Field(default=None, ge=1)
    due_days: int | None = Field(default=30, ge=1)
    active: bool = True

class AssignmentCreate(BaseModel):
    user_id: UUID
    course_id: UUID | None = None

class EvidenceCreate(BaseModel):
    evidence_type: str = Field(min_length=2, max_length=50)
    reference: str = Field(min_length=1, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)

class ExceptionCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)
    expires_at: datetime | None = None

@router.get("")
async def list_requirements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ComplianceRequirement).where(ComplianceRequirement.tenant_id == user.tenant_id).order_by(ComplianceRequirement.name))
    return list(result.scalars().all())

@router.post("", status_code=201)
async def create_requirement(payload: RequirementCreate, user: User = Depends(require_permission("compliance.manage")), db: AsyncSession = Depends(get_db)):
    item = ComplianceRequirement(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="compliance.requirement.created", entity_type="compliance_requirement", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "name": item.name}

@router.post("/{requirement_id}/assign", status_code=201)
async def assign_requirement(requirement_id: UUID, payload: AssignmentCreate, user: User = Depends(require_permission("compliance.manage")), db: AsyncSession = Depends(get_db)):
    req = await db.scalar(select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id, ComplianceRequirement.tenant_id == user.tenant_id))
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if req is None or learner is None:
        raise HTTPException(status_code=404, detail="Requirement or user not found")
    if payload.course_id:
        course = await db.scalar(select(Course).where(Course.id == payload.course_id, Course.tenant_id == user.tenant_id))
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
    due = datetime.now(timezone.utc).replace(microsecond=0)
    if req.due_days:
        from datetime import timedelta
        due += timedelta(days=req.due_days)
    item = ComplianceAssignment(tenant_id=user.tenant_id, requirement_id=req.id, user_id=learner.id, course_id=payload.course_id, due_at=due, status="assigned")
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="compliance.assignment.created", entity_type="compliance_assignment", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "status": item.status, "due_at": item.due_at}

@router.get("/my")
async def my_compliance(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceAssignment.user_id == user.id,
        )
        .order_by(ComplianceAssignment.due_at.asc().nulls_last())
    )
    return [
        {
            "id": str(item.id),
            "requirement": req.name,
            "status": item.status,
            "due_at": item.due_at,
            "course_id": str(item.course_id) if item.course_id else None,
        }
        for item, req in result.all()
    ]


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
        )
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Compliance assignment not found")

    evidence = ComplianceEvidence(
        tenant_id=user.tenant_id,
        assignment_id=assignment.id,
        user_id=user.id,
        **payload.model_dump(),
    )
    db.add(evidence)
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
        }
        for item in result.scalars().all()
    ]


@router.post("/{assignment_id}/exceptions", status_code=201)
async def request_compliance_exception(
    assignment_id: UUID,
    payload: ExceptionCreate,
    user: User = Depends(require_permission("compliance.manage")),
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
    if payload.expires_at and payload.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Exception expiry must be in the future")

    item = ComplianceException(
        tenant_id=user.tenant_id,
        assignment_id=assignment.id,
        reason=payload.reason,
        expires_at=payload.expires_at,
        status="approved",
        approved_by=user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(item)
    assignment.status = "excepted"
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="compliance.exception.approved",
        entity_type="compliance_exception",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status, "assignment_status": assignment.status}


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
        )
    )
    if evidence is None:
        raise HTTPException(status_code=404, detail="Compliance evidence not found")

    evidence.verified_by = user.id
    evidence.verified_at = datetime.now(timezone.utc)
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == evidence.assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        )
    )
    if assignment and assignment.course_id is None:
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
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance exception not found")
    if item.expires_at and item.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Exception has expired")
    item.status = "approved"
    item.approved_by = user.id
    item.approved_at = datetime.now(timezone.utc)
    assignment = await db.scalar(
        select(ComplianceAssignment).where(
            ComplianceAssignment.id == item.assignment_id,
            ComplianceAssignment.tenant_id == user.tenant_id,
        )
    )
    if assignment:
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

    if item.course_id:
        enrollment = await db.scalar(
            select(Enrollment).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.user_id == user.id,
                Enrollment.course_id == item.course_id,
                Enrollment.status == "completed",
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
