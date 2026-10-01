from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import (
    Assessment, AssessmentAttempt, AssessmentCycle, AssessmentOutcome,
    AssessmentReviewerAssignment, AssessmentTarget, Capability, CapabilityEvidence,
    Competency, Skill, User,
)
from app.db.session import get_db
from app.services.audit import audit
from app.api.routes.capability_gap import _recalculate_user_internal

router = APIRouter()
TARGET_MODELS = {"capability": Capability, "competency": Competency, "skill": Skill}
ASSESSMENT_TYPES = {"self", "manager", "assessor", "360", "knowledge_test", "practical", "evidence_review"}
REVIEWER_TYPES = {"self", "manager", "assessor", "peer"}


def _level_from_score(score: int) -> Decimal:
    # Continuous governed conversion: 0 -> 1.00 and 100 -> 5.00.
    value = Decimal("1") + (Decimal(score) / Decimal("100")) * Decimal("4")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


async def _target(db: AsyncSession, tenant_id: UUID, target_type: str, target_id: UUID):
    model = TARGET_MODELS[target_type]
    return await db.scalar(select(model).where(model.id == target_id, model.tenant_id == tenant_id))  # type: ignore[attr-defined]


async def _assessment(db: AsyncSession, tenant_id: UUID, assessment_id: UUID) -> Assessment:
    item = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == tenant_id))
    if item is None:
        raise HTTPException(404, "Assessment not found")
    if not item.active:
        raise HTTPException(409, "Assessment is inactive")
    return item


async def _cycle(db: AsyncSession, tenant_id: UUID, cycle_id: UUID) -> AssessmentCycle:
    item = await db.scalar(select(AssessmentCycle).where(AssessmentCycle.id == cycle_id, AssessmentCycle.tenant_id == tenant_id))
    if item is None:
        raise HTTPException(404, "Assessment cycle not found")
    return item


async def _can_read_cycle(user: User, cycle: AssessmentCycle, db: AsyncSession) -> bool:
    if await user_has_permission(user, db, "capability_assessments.manage"):
        return True
    if not await user_has_permission(user, db, "capability_assessments.read"):
        return False
    if user.id == cycle.user_id:
        return True
    learner = await db.scalar(select(User).where(User.id == cycle.user_id, User.tenant_id == user.tenant_id))
    return learner is not None and learner.manager_id == user.id


async def _can_execute(user: User, cycle: AssessmentCycle, db: AsyncSession, assessment: Assessment) -> str:
    if await user_has_permission(user, db, "capability_assessments.manage"):
        return "manager"
    if not await user_has_permission(user, db, "capability_assessments.execute"):
        raise HTTPException(403, "Capability assessment execution is not permitted")
    if assessment.assessment_type == "self":
        if user.id != cycle.user_id:
            raise HTTPException(403, "Self assessment must be completed by the assessed person")
        return "self"
    if user.id == cycle.user_id:
        return "self"
    learner = await db.scalar(select(User).where(User.id == cycle.user_id, User.tenant_id == user.tenant_id))
    if assessment.assessment_type == "manager":
        if learner is None or learner.manager_id != user.id:
            raise HTTPException(403, "Only the person's manager may complete this assessment")
        return "manager"
    if assessment.assessment_type == "360":
        assigned = await db.scalar(select(AssessmentReviewerAssignment).where(
            AssessmentReviewerAssignment.cycle_id == cycle.id,
            AssessmentReviewerAssignment.reviewer_id == user.id,
            AssessmentReviewerAssignment.tenant_id == user.tenant_id,
        ))
        if assigned is None:
            raise HTTPException(403, "You are not assigned as a 360 reviewer")
        return assigned.reviewer_type
    return "assessor"


class TargetPayload(BaseModel):
    target_type: str = Field(pattern="^(capability|competency|skill)$")
    target_id: UUID
    target_level: Decimal = Field(ge=1, le=5)
    weight: int = Field(default=1, ge=1, le=100)


class CycleCreate(BaseModel):
    user_id: UUID
    target_type: str = Field(pattern="^(capability|competency|skill)$")
    target_id: UUID
    required_level: Decimal = Field(ge=1, le=5)
    development_plan_id: UUID | None = None


class ReviewerPayload(BaseModel):
    reviewer_id: UUID
    reviewer_type: str = Field(pattern="^(self|manager|assessor|peer)$")


class OutcomePayload(BaseModel):
    target_type: str = Field(pattern="^(capability|competency|skill)$")
    target_id: UUID
    demonstrated_level: Decimal | None = Field(default=None, ge=1, le=5)
    score: int | None = Field(default=None, ge=0, le=100)
    confidence: int = Field(default=100, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=4000)
    reference: str | None = Field(default=None, max_length=1000)
def _target_json(item: AssessmentTarget, target_name: str | None) -> dict:
    return {
        "id": str(item.id), "assessment_id": str(item.assessment_id),
        "target_type": item.target_type, "target_id": str(item.target_id),
        "target_name": target_name, "target_level": _decimal(item.target_level),
        "weight": item.weight,
    }


async def _serialize_target(db: AsyncSession, item: AssessmentTarget) -> dict:
    target = await _target(db, item.tenant_id, item.target_type, item.target_id)
    return _target_json(item, getattr(target, "name", None))


def _cycle_json(cycle: AssessmentCycle, assessment: Assessment) -> dict:
    improvement = None
    if cycle.baseline_level is not None and cycle.current_level is not None:
        improvement = (cycle.current_level - cycle.baseline_level).quantize(Decimal("0.01"))
    gap = None
    if cycle.current_level is not None:
        gap = (cycle.required_level - cycle.current_level).quantize(Decimal("0.01"))
    return {
        "id": str(cycle.id), "assessment_id": str(cycle.assessment_id),
        "assessment_title": assessment.title, "assessment_type": assessment.assessment_type,
        "user_id": str(cycle.user_id), "target_type": cycle.target_type,
        "target_id": str(cycle.target_id), "required_level": _decimal(cycle.required_level),
        "baseline_level": _decimal(cycle.baseline_level), "current_level": _decimal(cycle.current_level),
        "gap": _decimal(gap), "improvement": _decimal(improvement), "status": cycle.status,
        "baseline_attempt_id": str(cycle.baseline_attempt_id) if cycle.baseline_attempt_id else None,
        "latest_attempt_id": str(cycle.latest_attempt_id) if cycle.latest_attempt_id else None,
        "next_reassessment_due_at": cycle.next_reassessment_due_at,
        "development_plan_id": str(cycle.development_plan_id) if cycle.development_plan_id else None,
    }


@router.get("/assessments/{assessment_id}/targets")
async def list_targets(
    assessment_id: UUID,
    user: User = Depends(require_permission("capability_assessments.read")),
    db: AsyncSession = Depends(get_db),
):
    await _assessment(db, user.tenant_id, assessment_id)
    rows = await db.execute(select(AssessmentTarget).where(
        AssessmentTarget.tenant_id == user.tenant_id,
        AssessmentTarget.assessment_id == assessment_id,
    ).order_by(AssessmentTarget.target_type, AssessmentTarget.target_id))
    return [await _serialize_target(db, row) for row in rows.scalars()]


@router.post("/assessments/{assessment_id}/targets", status_code=status.HTTP_201_CREATED)
async def add_target(
    assessment_id: UUID,
    payload: TargetPayload,
    user: User = Depends(require_permission("capability_assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await _assessment(db, user.tenant_id, assessment_id)
    target = await _target(db, user.tenant_id, payload.target_type, payload.target_id)
    if target is None:
        raise HTTPException(404, "Assessment target not found")
    duplicate = await db.scalar(select(AssessmentTarget.id).where(
        AssessmentTarget.assessment_id == assessment.id,
        AssessmentTarget.target_type == payload.target_type,
        AssessmentTarget.target_id == payload.target_id,
    ))
    if duplicate:
        raise HTTPException(409, "This assessment target is already mapped")
    item = AssessmentTarget(
        id=uuid4(), tenant_id=user.tenant_id, assessment_id=assessment.id,
        target_type=payload.target_type, target_id=payload.target_id,
        target_level=payload.target_level.quantize(Decimal("0.01")), weight=payload.weight,
    )
    db.add(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.target_added",
                entity_type="assessment_target", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return await _serialize_target(db, item)


@router.delete("/assessments/{assessment_id}/targets/{target_id}", status_code=204)
async def remove_target(
    assessment_id: UUID,
    target_id: UUID,
    user: User = Depends(require_permission("capability_assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await _assessment(db, user.tenant_id, assessment_id)
    item = await db.scalar(select(AssessmentTarget).where(
        AssessmentTarget.tenant_id == user.tenant_id,
        AssessmentTarget.assessment_id == assessment.id,
        AssessmentTarget.id == target_id,
    ))
    if item is None:
        raise HTTPException(404, "Assessment target mapping not found")
    attempts = await db.scalar(select(func.count(AssessmentAttempt.id)).where(AssessmentAttempt.assessment_id == assessment.id))
    if attempts:
        raise HTTPException(409, "Assessment targets are locked after the first attempt")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.target_removed",
                entity_type="assessment_target", entity_id=str(item.id))
    await db.commit()


@router.post("/assessments/{assessment_id}/cycles", status_code=status.HTTP_201_CREATED)
async def create_cycle(
    assessment_id: UUID,
    payload: CycleCreate,
    user: User = Depends(require_permission("capability_assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await _assessment(db, user.tenant_id, assessment_id)
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if learner is None:
        raise HTTPException(404, "Person not found")
    target = await _target(db, user.tenant_id, payload.target_type, payload.target_id)
    if target is None:
        raise HTTPException(404, "Cycle target not found")
    mapping = await db.scalar(select(AssessmentTarget).where(
        AssessmentTarget.assessment_id == assessment.id,
        AssessmentTarget.target_type == payload.target_type,
        AssessmentTarget.target_id == payload.target_id,
        AssessmentTarget.tenant_id == user.tenant_id,
    ))
    if mapping is None:
        raise HTTPException(422, "Map the target to the assessment before creating a cycle")
    existing = await db.scalar(select(AssessmentCycle.id).where(
        AssessmentCycle.tenant_id == user.tenant_id,
        AssessmentCycle.assessment_id == assessment.id,
        AssessmentCycle.user_id == learner.id,
        AssessmentCycle.target_type == payload.target_type,
        AssessmentCycle.target_id == payload.target_id,
    ))
    if existing:
        raise HTTPException(409, "An assessment cycle already exists for this person and target")
    cycle = AssessmentCycle(
        id=uuid4(), tenant_id=user.tenant_id, assessment_id=assessment.id, user_id=learner.id,
        target_type=payload.target_type, target_id=payload.target_id,
        required_level=payload.required_level.quantize(Decimal("0.01")),
        status="baseline_due", development_plan_id=payload.development_plan_id, created_by=user.id,
    )
    db.add(cycle)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.cycle_created",
                entity_type="assessment_cycle", entity_id=str(cycle.id),
                metadata={"user_id": str(learner.id), "target_id": str(payload.target_id)})
    await db.commit()
    await db.refresh(cycle)
    return _cycle_json(cycle, assessment)


@router.get("/cycles")
async def list_cycles(
    user_id: UUID | None = None,
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [AssessmentCycle.tenant_id == user.tenant_id]
    requested_user = user_id or user.id
    if requested_user != user.id:
        allowed = await user_has_permission(user, db, "capability_assessments.read")
        if allowed:
            learner = await db.scalar(select(User).where(User.id == requested_user, User.tenant_id == user.tenant_id))
            allowed = learner is not None and (learner.manager_id == user.id or await user_has_permission(user, db, "capability_assessments.manage"))
        if not allowed:
            raise HTTPException(403, "You may only view your own capability assessment cycles")
    conditions.append(AssessmentCycle.user_id == requested_user)
    if status_filter:
        conditions.append(AssessmentCycle.status == status_filter)
    rows = await db.execute(select(AssessmentCycle, Assessment).join(
        Assessment, Assessment.id == AssessmentCycle.assessment_id
    ).where(*conditions).order_by(AssessmentCycle.updated_at.desc()).limit(250))
    return [_cycle_json(cycle, assessment) for cycle, assessment in rows.all()]


@router.get("/cycles/{cycle_id}")
async def get_cycle(
    cycle_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cycle = await _cycle(db, user.tenant_id, cycle_id)
    if not await _can_read_cycle(user, cycle, db):
        raise HTTPException(403, "You do not have access to this assessment cycle")
    assessment = await _assessment(db, user.tenant_id, cycle.assessment_id)
    payload = _cycle_json(cycle, assessment)
    attempts = await db.execute(select(AssessmentAttempt).where(
        AssessmentAttempt.cycle_id == cycle.id
    ).order_by(AssessmentAttempt.started_at.asc()))
    attempt_items = []
    for attempt in attempts.scalars().all():
        outcomes = await db.execute(select(AssessmentOutcome).where(AssessmentOutcome.attempt_id == attempt.id))
        attempt_items.append({
            "id": str(attempt.id), "stage": attempt.stage, "attempt_number": attempt.attempt_number,
            "assessor_id": str(attempt.assessor_id) if attempt.assessor_id else None,
            "score": attempt.score, "demonstrated_level": _decimal(attempt.demonstrated_level),
            "confidence": attempt.confidence, "submitted_at": attempt.submitted_at,
            "valid_until": attempt.valid_until,
            "outcomes": [{
                "target_id": str(row.target_id), "demonstrated_level": _decimal(row.demonstrated_level),
                "confidence": row.confidence, "score": row.score, "notes": row.evidence_notes,
            } for row in outcomes.scalars().all()],
        })
    payload["attempts"] = attempt_items
    reviewers = await db.execute(select(AssessmentReviewerAssignment).where(AssessmentReviewerAssignment.cycle_id == cycle.id))
    payload["reviewers"] = [{
        "id": str(row.id), "reviewer_id": str(row.reviewer_id), "reviewer_type": row.reviewer_type,
        "status": row.status, "completed_at": row.completed_at,
    } for row in reviewers.scalars().all()]
    return payload
@router.post("/cycles/{cycle_id}/reviewers", status_code=status.HTTP_201_CREATED)
async def add_reviewer(
    cycle_id: UUID,
    payload: ReviewerPayload,
    user: User = Depends(require_permission("capability_assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    cycle = await _cycle(db, user.tenant_id, cycle_id)
    assessment = await _assessment(db, user.tenant_id, cycle.assessment_id)
    if assessment.assessment_type != "360":
        raise HTTPException(422, "Reviewer assignments are only used for 360 assessments")
    reviewer = await db.scalar(select(User).where(User.id == payload.reviewer_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if reviewer is None:
        raise HTTPException(404, "Reviewer not found")
    if reviewer.id == cycle.user_id and payload.reviewer_type != "self":
        raise HTTPException(422, "The assessed person may only be assigned the self reviewer type")
    existing = await db.scalar(select(AssessmentReviewerAssignment.id).where(
        AssessmentReviewerAssignment.cycle_id == cycle.id,
        AssessmentReviewerAssignment.reviewer_id == reviewer.id,
    ))
    if existing:
        raise HTTPException(409, "Reviewer is already assigned")
    row = AssessmentReviewerAssignment(
        id=uuid4(), tenant_id=user.tenant_id, cycle_id=cycle.id,
        reviewer_id=reviewer.id, reviewer_type=payload.reviewer_type, status="assigned",
    )
    db.add(row)
    cycle.status = "baseline_in_progress"
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.reviewer_assigned",
                entity_type="assessment_reviewer_assignment", entity_id=str(row.id))
    await db.commit()
    return {"id": str(row.id), "reviewer_id": str(row.reviewer_id), "reviewer_type": row.reviewer_type, "status": row.status}


async def _start_attempt(db: AsyncSession, user: User, cycle: AssessmentCycle, assessment: Assessment, stage: str) -> AssessmentAttempt:
    if stage == "baseline" and cycle.baseline_level is not None:
        raise HTTPException(409, "Baseline assessment has already been completed")
    if stage == "reassessment" and cycle.status not in {"reassessment_due", "development_in_progress", "completed"}:
        raise HTTPException(409, "This cycle is not ready for reassessment")
    reviewer_type = await _can_execute(user, cycle, db, assessment)
    latest_in_stage = await db.scalar(select(AssessmentAttempt.id).where(
        AssessmentAttempt.cycle_id == cycle.id,
        AssessmentAttempt.stage == stage,
        AssessmentAttempt.assessor_id == user.id,
        AssessmentAttempt.submitted_at.is_(None),
    ))
    if latest_in_stage:
        raise HTTPException(409, "You already have an open attempt for this cycle")
    number = int(await db.scalar(select(func.count(AssessmentAttempt.id)).where(AssessmentAttempt.assessment_id == assessment.id, AssessmentAttempt.user_id == cycle.user_id)) or 0) + 1
    attempt = AssessmentAttempt(
        id=uuid4(), assessment_id=assessment.id, user_id=cycle.user_id, cycle_id=cycle.id,
        attempt_number=number, stage=stage, assessment_method=assessment.measurement_method,
        assessor_id=user.id,
    )
    db.add(attempt)
    if stage == "reassessment":
        cycle.status = "reassessment_in_progress"
    elif assessment.assessment_type == "360":
        cycle.status = "baseline_in_progress"
    else:
        cycle.status = "baseline_in_progress"
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.attempt_started",
                entity_type="assessment_attempt", entity_id=str(attempt.id),
                metadata={"cycle_id": str(cycle.id), "stage": stage, "reviewer_type": reviewer_type})
    return attempt


@router.post("/cycles/{cycle_id}/attempts", status_code=status.HTTP_201_CREATED)
async def start_attempt(
    cycle_id: UUID,
    stage: str = "baseline",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if stage not in {"baseline", "reassessment"}:
        raise HTTPException(422, "Invalid assessment stage")
    cycle = await _cycle(db, user.tenant_id, cycle_id)
    assessment = await _assessment(db, user.tenant_id, cycle.assessment_id)
    attempt = await _start_attempt(db, user, cycle, assessment, stage)
    await db.commit()
    return {"id": str(attempt.id), "cycle_id": str(cycle.id), "stage": attempt.stage, "assessment_id": str(attempt.assessment_id)}
@router.post("/attempts/{attempt_id}/outcomes")
async def save_outcome(
    attempt_id: UUID,
    payload: OutcomePayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = await db.scalar(select(AssessmentAttempt).where(
        AssessmentAttempt.id == attempt_id
    ))
    if attempt is None or attempt.cycle_id is None:
        raise HTTPException(404, "Capability assessment attempt not found")
    assessment = await _assessment(db, user.tenant_id, attempt.assessment_id)
    if attempt.assessor_id != user.id and attempt.user_id != user.id and not await user_has_permission(user, db, "capability_assessments.manage"):
        raise HTTPException(403, "You do not own this assessment attempt")
    if attempt.submitted_at is not None:
        raise HTTPException(409, "Assessment attempt is already completed")
    target = await _target(db, user.tenant_id, payload.target_type, payload.target_id)
    if target is None:
        raise HTTPException(404, "Assessment outcome target not found")
    mapping = await db.scalar(select(AssessmentTarget).where(
        AssessmentTarget.assessment_id == assessment.id,
        AssessmentTarget.target_type == payload.target_type,
        AssessmentTarget.target_id == payload.target_id,
        AssessmentTarget.tenant_id == user.tenant_id,
    ))
    if mapping is None:
        raise HTTPException(422, "Outcome target is not mapped to this assessment")
    level = payload.demonstrated_level
    if level is None:
        if payload.score is None:
            raise HTTPException(422, "Provide a demonstrated level or assessment score")
        level = _level_from_score(payload.score)
    row = await db.scalar(select(AssessmentOutcome).where(
        AssessmentOutcome.attempt_id == attempt.id,
        AssessmentOutcome.target_id == payload.target_id,
        AssessmentOutcome.target_type == mapping.target_type,
    ))
    if row is None:
        row = AssessmentOutcome(
            id=uuid4(), tenant_id=user.tenant_id, attempt_id=attempt.id,
            target_type=mapping.target_type, target_id=payload.target_id,
        )
        db.add(row)
    row.score = payload.score
    row.demonstrated_level = level.quantize(Decimal("0.01"))
    row.confidence = payload.confidence
    row.evidence_notes = payload.notes
    row.evidence_reference = payload.reference
    row.assessor_id = user.id
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.outcome_saved",
                entity_type="assessment_outcome", entity_id=str(row.id))
    await db.commit()
    return {
        "id": str(row.id), "target_type": row.target_type, "target_id": str(row.target_id),
        "demonstrated_level": _decimal(row.demonstrated_level), "confidence": row.confidence,
        "score": row.score,
    }


@router.post("/attempts/{attempt_id}/complete")
async def complete_attempt(
    attempt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = await db.scalar(select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id))
    if attempt is None or attempt.cycle_id is None:
        raise HTTPException(404, "Capability assessment attempt not found")
    cycle = await _cycle(db, user.tenant_id, attempt.cycle_id)
    assessment = await _assessment(db, user.tenant_id, attempt.assessment_id)
    if attempt.assessor_id != user.id and attempt.user_id != user.id and not await user_has_permission(user, db, "capability_assessments.manage"):
        raise HTTPException(403, "You do not own this assessment attempt")
    if attempt.submitted_at is not None:
        raise HTTPException(409, "Assessment attempt is already completed")
    targets = list((await db.execute(select(AssessmentTarget).where(
        AssessmentTarget.assessment_id == assessment.id,
        AssessmentTarget.tenant_id == user.tenant_id,
    ))).scalars())
    outcomes = list((await db.execute(select(AssessmentOutcome).where(
        AssessmentOutcome.attempt_id == attempt.id,
        AssessmentOutcome.tenant_id == user.tenant_id,
    ))).scalars())
    if not targets:
        raise HTTPException(422, "Map at least one assessment target before completing the attempt")
    outcome_keys = {(item.target_type, item.target_id) for item in outcomes}
    required_keys = {(item.target_type, item.target_id) for item in targets}
    if outcome_keys != required_keys:
        raise HTTPException(422, "Every mapped assessment target must have an outcome before completion")
    weight_map = {(item.target_type, item.target_id): item.weight for item in targets}
    total_weight = sum(weight_map.values())
    level = sum((row.demonstrated_level * weight_map[(row.target_type, row.target_id)] for row in outcomes), Decimal("0")) / Decimal(total_weight)
    confidence = sum((Decimal(row.confidence) * weight_map[(row.target_type, row.target_id)] for row in outcomes), Decimal("0")) / Decimal(total_weight)
    scores = [row.score for row in outcomes if row.score is not None]
    score = round(sum(scores) / len(scores)) if scores else None
    now = datetime.now(timezone.utc)
    attempt.demonstrated_level = level.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    attempt.confidence = int(confidence.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    attempt.score = score
    attempt.passed = None if score is None else score >= assessment.passing_score
    attempt.submitted_at = now
    attempt.valid_until = now + timedelta(days=assessment.validity_days) if assessment.validity_days else None

    for row in outcomes:
        evidence = await db.scalar(select(CapabilityEvidence).where(
            CapabilityEvidence.tenant_id == user.tenant_id,
            CapabilityEvidence.user_id == cycle.user_id,
            CapabilityEvidence.target_type == row.target_type,
            CapabilityEvidence.target_id == row.target_id,
            CapabilityEvidence.source_type == "assessment",
            CapabilityEvidence.source_id == str(attempt.id),
        ))
        if evidence is None:
            evidence = CapabilityEvidence(
                id=uuid4(), tenant_id=user.tenant_id, user_id=cycle.user_id,
                target_type=row.target_type, target_id=row.target_id,
                evidence_type="assessment_result", source_type="assessment",
                source_id=str(attempt.id), demonstrated_level=row.demonstrated_level,
                confidence=row.confidence, status="verified", observed_at=now,
                expires_at=attempt.valid_until, assessor_id=row.assessor_id or user.id,
                notes=row.evidence_notes, record_metadata={
                    "assessment_id": str(attempt.assessment_id), "cycle_id": str(cycle.id),
                    "stage": attempt.stage, "assessment_type": assessment.assessment_type,
                },
                verified_by=user.id, verified_at=now,
            )
            db.add(evidence)
    assignment = await db.scalar(select(AssessmentReviewerAssignment).where(
        AssessmentReviewerAssignment.cycle_id == cycle.id,
        AssessmentReviewerAssignment.reviewer_id == attempt.assessor_id,
        AssessmentReviewerAssignment.tenant_id == user.tenant_id,
    )) if attempt.assessor_id else None
    if assignment is not None:
        assignment.status = "completed"
        assignment.completed_at = now
    if assessment.assessment_type == "360":
        cycle_attempts = list((await db.execute(select(AssessmentAttempt).where(
            AssessmentAttempt.cycle_id == cycle.id,
            AssessmentAttempt.stage == attempt.stage,
            AssessmentAttempt.submitted_at.is_not(None),
        ))).scalars())
        aggregate_levels = [Decimal(str(item.demonstrated_level)) for item in cycle_attempts if item.demonstrated_level is not None]
        aggregate_level = None
        if aggregate_levels:
            aggregate_level = (sum(aggregate_levels, Decimal("0")) / Decimal(len(aggregate_levels))).quantize(Decimal("0.01"))
        all_reviewers = list((await db.execute(select(AssessmentReviewerAssignment).where(
            AssessmentReviewerAssignment.cycle_id == cycle.id
        ))).scalars())
        all_complete = bool(all_reviewers) and all(row.status == "completed" for row in all_reviewers)
        if attempt.stage == "baseline":
            cycle.current_level = aggregate_level
            if all_complete or not all_reviewers:
                cycle.baseline_level = aggregate_level
                cycle.baseline_attempt_id = attempt.id
                cycle.status = "reassessment_due" if assessment.reassessment_interval_days else "completed"
            else:
                cycle.status = "baseline_in_progress"
        else:
            cycle.current_level = aggregate_level
            if all_complete or not all_reviewers:
                cycle.latest_attempt_id = attempt.id
                cycle.status = "completed"
    elif attempt.stage == "baseline":
        cycle.baseline_level = attempt.demonstrated_level
        cycle.current_level = attempt.demonstrated_level
        cycle.baseline_attempt_id = attempt.id
        cycle.latest_attempt_id = attempt.id
        cycle.status = "development_in_progress" if cycle.development_plan_id else ("reassessment_due" if assessment.reassessment_interval_days else "completed")
    else:
        cycle.current_level = attempt.demonstrated_level
        cycle.latest_attempt_id = attempt.id
        cycle.status = "completed"

    if attempt.stage == "baseline" and assessment.reassessment_interval_days:
        cycle.next_reassessment_due_at = now + timedelta(days=assessment.reassessment_interval_days)
    elif attempt.stage == "reassessment" and assessment.reassessment_interval_days:
        cycle.next_reassessment_due_at = now + timedelta(days=assessment.reassessment_interval_days)
    if attempt.assessment_method == "review_based":
        cycle.next_reassessment_due_at = cycle.next_reassessment_due_at

    await _recalculate_user_internal(db, user.tenant_id, cycle.user_id, user.id)

    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.attempt_completed",
                entity_type="assessment_attempt", entity_id=str(attempt.id),
                metadata={"stage": attempt.stage, "demonstrated_level": str(attempt.demonstrated_level),
                          "confidence": attempt.confidence})
    await db.commit()
    await db.refresh(cycle)
    return {
        "attempt_id": str(attempt.id), "cycle": _cycle_json(cycle, assessment),
        "valid_until": attempt.valid_until, "score": attempt.score,
        "demonstrated_level": _decimal(attempt.demonstrated_level),
        "confidence": attempt.confidence,
    }


@router.post("/cycles/{cycle_id}/mark-reassessment-due")
async def mark_reassessment_due(
    cycle_id: UUID,
    user: User = Depends(require_permission("reassessment.manage")),
    db: AsyncSession = Depends(get_db),
):
    cycle = await _cycle(db, user.tenant_id, cycle_id)
    assessment = await _assessment(db, user.tenant_id, cycle.assessment_id)
    if cycle.baseline_level is None:
        raise HTTPException(422, "Baseline assessment must be completed before reassessment")
    if cycle.status in {"reassessment_in_progress"}:
        raise HTTPException(409, "A reassessment is already in progress")
    cycle.status = "reassessment_due"
    cycle.next_reassessment_due_at = datetime.now(timezone.utc)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability_assessment.reassessment_due",
                entity_type="assessment_cycle", entity_id=str(cycle.id))
    await db.commit()
    return _cycle_json(cycle, assessment)


@router.post("/cycles/{cycle_id}/reassessment", status_code=status.HTTP_201_CREATED)
async def start_reassessment(
    cycle_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cycle = await _cycle(db, user.tenant_id, cycle_id)
    assessment = await _assessment(db, user.tenant_id, cycle.assessment_id)
    if cycle.status not in {"reassessment_due", "completed", "development_in_progress"}:
        raise HTTPException(409, "Cycle is not ready for reassessment")
    attempt = await _start_attempt(db, user, cycle, assessment, "reassessment")
    await db.commit()
    return {"id": str(attempt.id), "cycle_id": str(cycle.id), "stage": "reassessment", "assessment_id": str(assessment.id)}
@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = await db.scalar(select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id))
    if attempt is None or attempt.cycle_id is None:
        raise HTTPException(404, "Capability assessment attempt not found")
    cycle = await _cycle(db, user.tenant_id, attempt.cycle_id)
    if not await _can_read_cycle(user, cycle, db) and attempt.assessor_id != user.id:
        raise HTTPException(403, "You do not have access to this assessment attempt")
    assessment = await _assessment(db, user.tenant_id, attempt.assessment_id)
    rows = await db.execute(select(AssessmentOutcome).where(AssessmentOutcome.attempt_id == attempt.id))
    return {
        "id": str(attempt.id), "cycle_id": str(cycle.id), "stage": attempt.stage,
        "assessment_id": str(attempt.assessment_id), "assessment_title": assessment.title,
        "assessment_type": assessment.assessment_type, "score": attempt.score,
        "passed": attempt.passed, "demonstrated_level": _decimal(attempt.demonstrated_level),
        "confidence": attempt.confidence, "assessor_id": str(attempt.assessor_id) if attempt.assessor_id else None,
        "started_at": attempt.started_at, "submitted_at": attempt.submitted_at,
        "valid_until": attempt.valid_until,
        "outcomes": [{
            "target_type": row.target_type, "target_id": str(row.target_id),
            "score": row.score, "demonstrated_level": _decimal(row.demonstrated_level),
            "confidence": row.confidence, "notes": row.evidence_notes, "reference": row.evidence_reference,
        } for row in rows.scalars().all()],
    }
