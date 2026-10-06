from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import Assessment, AssessmentAttempt, AssessmentCompetency, Capability, CapabilityEvidence, Competency, Skill, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

TARGET_TYPES = {"capability", "competency", "skill"}
SOURCE_TYPES = {"assessment", "manual_observation", "work_product", "course_completion", "credential", "external"}
EVIDENCE_TYPES = {"demonstration", "assessment_result", "observation", "artifact", "completion", "credential"}
STATUSES = {"pending", "verified", "rejected"}


@router.get("/page")
async def page_evidence(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    q: str = Query(default="", max_length=160),
    target_type: str | None = None,
    target_id: UUID | None = None,
    user_id: UUID | None = None,
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bounded evidence queue for operational screens; all filters remain tenant-scoped."""
    if user_id is None and not await user_has_permission(user, db, "evidence.read"):
        raise HTTPException(403, "Evidence listing requires evidence.read permission or a self-scoped user filter")
    if user_id is not None and user_id != user.id and not await user_has_permission(user, db, "evidence.read"):
        raise HTTPException(403, "You may only view your own evidence")
    if target_type and target_type not in TARGET_TYPES:
        raise HTTPException(422, "Invalid target type")
    if status and status not in STATUSES:
        raise HTTPException(422, "Invalid evidence status")
    conditions = [CapabilityEvidence.tenant_id == user.tenant_id]
    if target_type:
        conditions.append(CapabilityEvidence.target_type == target_type)
    if target_id:
        conditions.append(CapabilityEvidence.target_id == target_id)
    if user_id:
        target_user = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == user.tenant_id))
        if target_user is None:
            raise HTTPException(404, "User not found")
        conditions.append(CapabilityEvidence.user_id == user_id)
    if status:
        conditions.append(CapabilityEvidence.status == status)
    term = q.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        match = f"%{escaped}%"
        conditions.append(or_(CapabilityEvidence.notes.ilike(match, escape="\\"), CapabilityEvidence.source_id.ilike(match, escape="\\")))
    total = int(await db.scalar(select(func.count()).select_from(CapabilityEvidence).where(*conditions)) or 0)
    rows = await db.execute(select(CapabilityEvidence, User.first_name, User.last_name, User.email)
        .join(User, User.id == CapabilityEvidence.user_id)
        .where(*conditions, User.tenant_id == user.tenant_id)
        .order_by(CapabilityEvidence.observed_at.desc(), CapabilityEvidence.id.desc())
        .offset((page - 1) * page_size).limit(page_size))
    items = [
        {**_json(item), "user_name": " ".join(part for part in (first_name, last_name) if part).strip() or email, "user_email": email}
        for item, first_name, last_name, email in rows.all()
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _assessment_score_to_level(score: int) -> int:
    """Convert a 0-100 assessment score to the canonical five-level scale."""
    if score < 50:
        return 1
    if score < 70:
        return 2
    if score < 80:
        return 3
    if score < 90:
        return 4
    return 5


class EvidenceCreate(BaseModel):
    user_id: UUID
    target_type: str = Field(pattern="^(capability|competency|skill)$")
    target_id: UUID
    evidence_type: str = Field(min_length=3, max_length=40)
    source_type: str = Field(min_length=3, max_length=40)
    source_id: str | None = Field(default=None, max_length=160)
    demonstrated_level: Decimal = Field(ge=1, le=5)
    confidence: int = Field(default=100, ge=0, le=100)
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    assessor_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    metadata: dict = Field(default_factory=dict)


class EvidenceDecision(BaseModel):
    decision: str = Field(pattern="^(verified|rejected)$")
    reason: str | None = Field(default=None, max_length=2000)


async def _target(db: AsyncSession, tenant_id: UUID, target_type: str, target_id: UUID):
    model: Any = {"capability": Capability, "competency": Competency, "skill": Skill}[target_type]
    return await db.scalar(select(model).where(model.id == target_id, model.tenant_id == tenant_id))


def _json(item: CapabilityEvidence) -> dict:
    return {
        "id": str(item.id), "user_id": str(item.user_id), "target_type": item.target_type,
        "target_id": str(item.target_id), "evidence_type": item.evidence_type,
        "source_type": item.source_type, "source_id": item.source_id,
        "demonstrated_level": float(item.demonstrated_level), "confidence": item.confidence,
        "status": item.status, "observed_at": item.observed_at, "expires_at": item.expires_at,
        "assessor_id": str(item.assessor_id) if item.assessor_id else None,
        "notes": item.notes, "metadata": item.record_metadata,
        "verified_by": str(item.verified_by) if item.verified_by else None,
        "verified_at": item.verified_at, "rejection_reason": item.rejection_reason,
    }


@router.get("")
async def list_evidence(
    target_type: str | None = None,
    target_id: UUID | None = None,
    user_id: UUID | None = None,
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id is None and not await user_has_permission(user, db, "evidence.read"):
        raise HTTPException(403, "Evidence listing requires evidence.read permission or a self-scoped user filter")
    if user_id is not None and user_id != user.id and not await user_has_permission(user, db, "evidence.read"):
        raise HTTPException(403, "You may only view your own evidence")

    if target_type and target_type not in TARGET_TYPES:
        raise HTTPException(422, "Invalid target type")
    if status and status not in STATUSES:
        raise HTTPException(422, "Invalid evidence status")
    conditions = [CapabilityEvidence.tenant_id == user.tenant_id]
    if target_type:
        conditions.append(CapabilityEvidence.target_type == target_type)
    if target_id:
        conditions.append(CapabilityEvidence.target_id == target_id)
    if user_id:
        target_user = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == user.tenant_id))
        if target_user is None:
            raise HTTPException(404, "User not found")
        conditions.append(CapabilityEvidence.user_id == user_id)
    if status:
        conditions.append(CapabilityEvidence.status == status)
    result = await db.execute(select(CapabilityEvidence).where(*conditions).order_by(CapabilityEvidence.observed_at.desc()))
    return [_json(item) for item in result.scalars().all()]


@router.post("", status_code=201)
async def create_evidence(
    payload: EvidenceCreate,
    user: User = Depends(require_permission("evidence.manage")),
    db: AsyncSession = Depends(get_db),
):
    if payload.source_type not in SOURCE_TYPES or payload.evidence_type not in EVIDENCE_TYPES:
        raise HTTPException(422, "Unsupported evidence or source type")
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if learner is None:
        raise HTTPException(404, "User not found")
    target = await _target(db, user.tenant_id, payload.target_type, payload.target_id)
    if target is None:
        raise HTTPException(404, "Evidence target not found")
    assessor_id = payload.assessor_id or user.id
    assessor = await db.scalar(select(User).where(User.id == assessor_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if assessor is None:
        raise HTTPException(422, "Assessor not found")
    if payload.expires_at and payload.observed_at and payload.expires_at <= payload.observed_at:
        raise HTTPException(422, "Evidence expiry must be after observation time")
    if payload.source_id:
        duplicate = await db.scalar(select(CapabilityEvidence.id).where(
            CapabilityEvidence.tenant_id == user.tenant_id,
            CapabilityEvidence.user_id == learner.id,
            CapabilityEvidence.target_type == payload.target_type,
            CapabilityEvidence.target_id == payload.target_id,
            CapabilityEvidence.source_type == payload.source_type,
            CapabilityEvidence.source_id == payload.source_id,
        ))
        if duplicate:
            raise HTTPException(409, "Evidence with the same source provenance already exists for this target")
    item = CapabilityEvidence(
        tenant_id=user.tenant_id, user_id=learner.id, target_type=payload.target_type,
        target_id=payload.target_id, evidence_type=payload.evidence_type,
        source_type=payload.source_type, source_id=payload.source_id,
        demonstrated_level=payload.demonstrated_level, confidence=payload.confidence,
        observed_at=payload.observed_at or datetime.now(timezone.utc), expires_at=payload.expires_at,
        assessor_id=assessor.id, notes=payload.notes, record_metadata=payload.metadata,
    )
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability.evidence.created", entity_type="capability_evidence", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return {**_json(item), "user_name": " ".join(part for part in (learner.first_name, learner.last_name) if part).strip() or learner.email, "user_email": learner.email}


@router.post("/{evidence_id}/decision")
async def decide_evidence(
    evidence_id: UUID,
    payload: EvidenceDecision,
    user: User = Depends(require_permission("evidence.verify")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(CapabilityEvidence).where(CapabilityEvidence.id == evidence_id, CapabilityEvidence.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(404, "Evidence not found")
    if item.status == payload.decision:
        return _json(item)
    if item.status != "pending":
        raise HTTPException(409, "Only pending evidence can be decided; use a new evidence record for a changed finding")
    item.status = payload.decision
    item.verified_by = user.id if payload.decision == "verified" else None
    item.verified_at = datetime.now(timezone.utc) if payload.decision == "verified" else None
    item.rejection_reason = payload.reason if payload.decision == "rejected" else None
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action=f"capability.evidence.{payload.decision}", entity_type="capability_evidence", entity_id=str(item.id), metadata={"reason": payload.reason} if payload.reason else None)
    # Keep the materialized gap snapshot in the same transaction as the evidence
    # decision. Dynamic gap reads already see the decision; persisted reports must too.
    from app.api.routes.capability_gap import _recalculate_user_internal

    await _recalculate_user_internal(db, user.tenant_id, item.user_id, actor_id=user.id)
    await db.commit()
    return _json(item)


@router.get("/users/{user_id}/summary")
async def evidence_summary(
    user_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.id != user_id and not await user_has_permission(user, db, "evidence.read"):
        raise HTTPException(403, "You may only view your own evidence")

    learner = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if learner is None:
        raise HTTPException(404, "User not found")
    result = await db.execute(select(CapabilityEvidence).where(
        CapabilityEvidence.tenant_id == user.tenant_id,
        CapabilityEvidence.user_id == user_id,
        CapabilityEvidence.status == "verified",
    ))
    now = datetime.now(timezone.utc)
    current = [item for item in result.scalars().all() if item.expires_at is None or item.expires_at > now]
    grouped: dict[str, dict[str, Any]] = {}
    for item in current:
        key = f"{item.target_type}:{item.target_id}"
        existing = grouped.setdefault(key, {"target_type": item.target_type, "target_id": str(item.target_id), "level": 0, "confidence": 0, "evidence_count": 0})
        existing["level"] = max(existing["level"], item.demonstrated_level)
        existing["confidence"] = max(existing["confidence"], item.confidence)
        existing["evidence_count"] += 1
    return {"user_id": str(user_id), "verified_current_evidence": list(grouped.values())}


class AssessmentCompetencyPayload(BaseModel):
    competency_id: UUID
    target_level: int = Field(default=3, ge=1, le=5)
    weight: int = Field(default=1, ge=1, le=100)


@router.get("/assessments/{assessment_id}/competencies")
async def list_assessment_competencies(
    assessment_id: UUID,
    user: User = Depends(require_permission("evidence.read")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    rows = await db.execute(
        select(AssessmentCompetency, Competency)
        .join(Competency, Competency.id == AssessmentCompetency.competency_id)
        .where(AssessmentCompetency.assessment_id == assessment.id, Competency.tenant_id == user.tenant_id)
        .order_by(Competency.name)
    )
    return [{"competency_id": str(link.competency_id), "competency": competency.name, "target_level": link.target_level, "weight": link.weight} for link, competency in rows.all()]


@router.post("/assessments/{assessment_id}/competencies", status_code=201)
async def map_assessment_competency(
    assessment_id: UUID,
    payload: AssessmentCompetencyPayload,
    user: User = Depends(require_permission("evidence.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    competency = await db.scalar(select(Competency).where(Competency.id == payload.competency_id, Competency.tenant_id == user.tenant_id))
    if assessment is None or competency is None:
        raise HTTPException(404, "Assessment or competency not found")
    item = await db.scalar(select(AssessmentCompetency).where(
        AssessmentCompetency.assessment_id == assessment.id,
        AssessmentCompetency.competency_id == competency.id,
    ))
    if item is None:
        item = AssessmentCompetency(
            assessment_id=assessment.id, competency_id=competency.id,
            target_level=payload.target_level, weight=payload.weight,
        )
        db.add(item)
    else:
        item.target_level = payload.target_level
        item.weight = payload.weight
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.competency_mapping.saved", entity_type="assessment_competency", entity_id=str(assessment.id), metadata={"competency_id": str(competency.id)})
    await db.commit()
    return {"assessment_id": str(assessment.id), "competency_id": str(competency.id), "target_level": item.target_level, "weight": item.weight}


@router.delete("/assessments/{assessment_id}/competencies/{competency_id}", status_code=204)
async def unmap_assessment_competency(
    assessment_id: UUID,
    competency_id: UUID,
    user: User = Depends(require_permission("evidence.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(AssessmentCompetency).join(Assessment, Assessment.id == AssessmentCompetency.assessment_id).where(
        AssessmentCompetency.assessment_id == assessment_id,
        AssessmentCompetency.competency_id == competency_id,
        Assessment.tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(404, "Assessment competency mapping not found")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.competency_mapping.deleted", entity_type="assessment_competency", entity_id=str(assessment_id), metadata={"competency_id": str(competency_id)})
    await db.commit()


@router.post("/from-assessment/{attempt_id}", status_code=201)
async def create_assessment_evidence(
    attempt_id: UUID,
    user: User = Depends(require_permission("evidence.manage")),
    db: AsyncSession = Depends(get_db),
):
    attempt = await db.scalar(
        select(AssessmentAttempt)
        .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
        .where(
            AssessmentAttempt.id == attempt_id,
            Assessment.tenant_id == user.tenant_id,
        )
    )
    if attempt is None:
        raise HTTPException(404, "Assessment attempt not found")
    if not attempt.submitted_at or attempt.score is None or attempt.passed is None:
        raise HTTPException(422, "Assessment attempt is not submitted or graded")
    mappings = await db.execute(select(AssessmentCompetency).where(AssessmentCompetency.assessment_id == attempt.assessment_id))
    rows = mappings.scalars().all()
    if not rows:
        raise HTTPException(422, "Assessment has no competency mappings")
    created = []
    for mapping in rows:
        existing = await db.scalar(select(CapabilityEvidence).where(
            CapabilityEvidence.tenant_id == user.tenant_id,
            CapabilityEvidence.user_id == attempt.user_id,
            CapabilityEvidence.target_type == "competency",
            CapabilityEvidence.target_id == mapping.competency_id,
            CapabilityEvidence.source_type == "assessment",
            CapabilityEvidence.source_id == str(attempt.id),
        ))
        if existing is not None:
            created.append(existing)
            continue
        level = Decimal(_assessment_score_to_level(attempt.score))
        item = CapabilityEvidence(
            tenant_id=user.tenant_id, user_id=attempt.user_id, target_type="competency", target_id=mapping.competency_id,
            evidence_type="assessment_result", source_type="assessment", source_id=str(attempt.id),
            demonstrated_level=level, confidence=min(100, max(0, attempt.score)),
            status="verified", observed_at=attempt.submitted_at, assessor_id=user.id,
            notes=f"Assessment score: {attempt.score}; passed: {attempt.passed}",
            record_metadata={"assessment_id": str(attempt.assessment_id), "attempt_number": attempt.attempt_number},
            verified_by=user.id, verified_at=datetime.now(timezone.utc),
        )
        db.add(item)
        created.append(item)
    await db.flush()
    for item in created:
        await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="capability.evidence.created_from_assessment", entity_type="capability_evidence", entity_id=str(item.id))
    await db.commit()
    return [_json(item) for item in created]

