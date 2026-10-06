from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import (
    CapabilityEvidence, CapabilityGap, DevelopmentEvidence, DevelopmentInteraction,
    DevelopmentIntervention, DevelopmentPlan, DevelopmentRecommendation, User,
)
from app.db.session import get_db
from app.services.audit import audit
from app.api.routes.capability_gap import _recalculate_user_internal

router = APIRouter()
INTERVENTION_TYPES = {"learning", "coaching", "mentoring", "experiential", "evidence_building"}
STATUSES = {"planned", "in_progress", "completed", "cancelled"}

class InterventionCreate(BaseModel):
    user_id: UUID | None = None
    recommendation_id: UUID | None = None
    plan_id: UUID | None = None
    intervention_type: str = Field(pattern=r"^(learning|coaching|mentoring|experiential|evidence_building)$")
    title: str = Field(min_length=3, max_length=240)
    objective: str = Field(min_length=3, max_length=5000)
    assignee_id: UUID | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    metadata_json: dict = Field(default_factory=dict)

class InterventionUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(planned|in_progress|completed|cancelled)$")
    assignee_id: UUID | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    objective: str | None = Field(default=None, min_length=3, max_length=5000)

class InteractionCreate(BaseModel):
    interaction_type: str = Field(pattern=r"^(coaching_session|mentoring_session|review|practice_review)$")
    occurred_at: datetime
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    summary: str = Field(min_length=3, max_length=10000)
    action_items: list[dict] = Field(default_factory=list)

class EvidenceCreate(BaseModel):
    evidence_type: str = Field(pattern=r"^(work_output|practical_demonstration|manager_observation|reflection|assessment|certification)$")
    description: str = Field(min_length=3, max_length=10000)
    observed_at: datetime
    demonstrated_level: float | None = Field(default=None, ge=1, le=5)
    metadata_json: dict = Field(default_factory=dict)

async def _target_scope(user, db, target_id):
    if target_id is None or target_id == user.id:
        return user.id
    if not await user_has_permission(user, db, "users.read"):
        raise HTTPException(403, "You cannot manage development for another user")
    target = await db.scalar(select(User).where(User.id == target_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if target is None:
        raise HTTPException(404, "User not found")
    if target.manager_id != user.id and not await user_has_permission(user, db, "development.recommendations.manage"):
        raise HTTPException(403, "Manager scope does not include this user")
    return target.id

async def _intervention_access(intervention_id, user, db, write=False):
    item = await db.scalar(select(DevelopmentIntervention).where(DevelopmentIntervention.id == intervention_id, DevelopmentIntervention.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(404, "Development intervention not found")
    allowed = item.user_id == user.id or item.assignee_id == user.id
    if not allowed and await user_has_permission(user, db, "users.read"):
        target = await db.scalar(select(User).where(User.id == item.user_id, User.tenant_id == user.tenant_id))
        allowed = bool(target and target.manager_id == user.id)
    if not allowed and await user_has_permission(user, db, "development.recommendations.manage"):
        allowed = True
    if not allowed:
        raise HTTPException(403, "Development intervention access is not permitted")
    return item

@router.get("")
async def list_interventions(
    user_id: UUID | None = None,
    status_filter: str | None = None,
    include_progress: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = await _target_scope(user, db, user_id)
    stmt = select(DevelopmentIntervention).where(DevelopmentIntervention.tenant_id == user.tenant_id, DevelopmentIntervention.user_id == uid).order_by(DevelopmentIntervention.due_at.asc().nulls_last(), DevelopmentIntervention.created_at.desc())
    if status_filter:
        if status_filter not in STATUSES:
            raise HTTPException(422, "Invalid intervention status")
        stmt = stmt.where(DevelopmentIntervention.status == status_filter)
    rows = (await db.execute(stmt.limit(250))).scalars().all()
    if not include_progress or not rows:
        return [_json_intervention(x) for x in rows]

    intervention_ids = [row.id for row in rows]
    interaction_counts = (
        select(
            DevelopmentInteraction.intervention_id.label("intervention_id"),
            func.count(DevelopmentInteraction.id).label("interactions"),
        )
        .where(
            DevelopmentInteraction.tenant_id == user.tenant_id,
            DevelopmentInteraction.intervention_id.in_(intervention_ids),
        )
        .group_by(DevelopmentInteraction.intervention_id)
        .subquery()
    )
    evidence_counts = (
        select(
            DevelopmentEvidence.intervention_id.label("intervention_id"),
            func.count(DevelopmentEvidence.id).label("evidence_count"),
            func.count(DevelopmentEvidence.id)
            .filter(DevelopmentEvidence.verification_status == "verified")
            .label("verified_evidence_count"),
        )
        .where(
            DevelopmentEvidence.tenant_id == user.tenant_id,
            DevelopmentEvidence.intervention_id.in_(intervention_ids),
        )
        .group_by(DevelopmentEvidence.intervention_id)
        .subquery()
    )
    progress_rows = (
        await db.execute(
            select(
                DevelopmentIntervention.id,
                func.coalesce(interaction_counts.c.interactions, 0).label("interactions"),
                func.coalesce(evidence_counts.c.evidence_count, 0).label("evidence_count"),
                func.coalesce(
                    evidence_counts.c.verified_evidence_count, 0
                ).label("verified_evidence_count"),
            )
            .select_from(DevelopmentIntervention)
            .outerjoin(
                interaction_counts,
                interaction_counts.c.intervention_id == DevelopmentIntervention.id,
            )
            .outerjoin(
                evidence_counts,
                evidence_counts.c.intervention_id == DevelopmentIntervention.id,
            )
            .where(
                DevelopmentIntervention.tenant_id == user.tenant_id,
                DevelopmentIntervention.id.in_(intervention_ids),
            )
        )
    ).all()
    progress = {}
    status_by_id = {str(row.id): row.status for row in rows}
    for intervention_id, interactions, evidence_count, verified_evidence_count in progress_rows:
        progress[str(intervention_id)] = {
            "status": status_by_id[str(intervention_id)],
            "interactions": int(interactions),
            "evidence_count": int(evidence_count),
            "verified_evidence_count": int(verified_evidence_count),
            "progress_signal": (
                "evidence_verified"
                if verified_evidence_count
                else "activity_recorded"
                if interactions or evidence_count
                else "not_started"
            ),
        }
    return [
        {
            **_json_intervention(row),
            "progress": progress.get(
                str(row.id),
                {
                    "status": row.status,
                    "interactions": 0,
                    "evidence_count": 0,
                    "verified_evidence_count": 0,
                    "progress_signal": "not_started",
                },
            ),
        }
        for row in rows
    ]

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_intervention(payload: InterventionCreate, user: User = Depends(require_permission("development.recommendations.manage")), db: AsyncSession = Depends(get_db)):
    uid = await _target_scope(user, db, payload.user_id)
    recommendation = None
    if payload.recommendation_id:
        recommendation = await db.scalar(select(DevelopmentRecommendation).where(DevelopmentRecommendation.id == payload.recommendation_id, DevelopmentRecommendation.tenant_id == user.tenant_id, DevelopmentRecommendation.user_id == uid))
        if recommendation is None:
            raise HTTPException(404, "Development recommendation not found")
        if recommendation.status not in {"accepted", "recommended"}:
            raise HTTPException(409, "Recommendation is no longer actionable")
    if payload.plan_id:
        plan = await db.scalar(select(DevelopmentPlan).where(DevelopmentPlan.id == payload.plan_id, DevelopmentPlan.tenant_id == user.tenant_id, DevelopmentPlan.user_id == uid))
        if plan is None:
            raise HTTPException(404, "Development plan not found")
    if payload.assignee_id:
        assignee = await db.scalar(select(User).where(User.id == payload.assignee_id, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
        if assignee is None:
            raise HTTPException(404, "Assignee not found")
    item = DevelopmentIntervention(tenant_id=user.tenant_id, user_id=uid, plan_id=payload.plan_id, recommendation_id=payload.recommendation_id, assignee_id=payload.assignee_id, intervention_type=payload.intervention_type, title=payload.title, objective=payload.objective, starts_at=payload.starts_at, due_at=payload.due_at, metadata_json=payload.metadata_json)
    db.add(item)
    if recommendation and recommendation.status == "recommended":
        recommendation.status = "accepted"
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="development.intervention.created", entity_type="development_intervention", entity_id=str(item.id), metadata={"type": item.intervention_type})
    await db.commit()
    await db.refresh(item)
    return _json_intervention(item)
@router.get("/{intervention_id}")
async def get_intervention(intervention_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await _intervention_access(intervention_id, user, db)
    interactions = (await db.execute(select(DevelopmentInteraction).where(DevelopmentInteraction.intervention_id == item.id, DevelopmentInteraction.tenant_id == user.tenant_id).order_by(DevelopmentInteraction.occurred_at.desc()))).scalars().all()
    evidence = (await db.execute(select(DevelopmentEvidence).where(DevelopmentEvidence.intervention_id == item.id, DevelopmentEvidence.tenant_id == user.tenant_id).order_by(DevelopmentEvidence.observed_at.desc()))).scalars().all()
    return {**_json_intervention(item), "interactions": [_json_interaction(x) for x in interactions], "evidence": [_json_evidence(x) for x in evidence]}

@router.patch("/{intervention_id}")
async def update_intervention(intervention_id: UUID, payload: InterventionUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await _intervention_access(intervention_id, user, db, write=True)
    values = payload.model_dump(exclude_unset=True)
    if "assignee_id" in values and values["assignee_id"] is not None:
        assignee = await db.scalar(select(User).where(User.id == values["assignee_id"], User.tenant_id == user.tenant_id, User.is_active.is_(True)))
        if assignee is None:
            raise HTTPException(404, "Assignee not found")
    for key in ("status", "assignee_id", "starts_at", "due_at", "objective"):
        if key in values:
            setattr(item, key, values[key])
    if item.status == "completed" and item.completed_at is None:
        item.completed_at = datetime.now(timezone.utc)
    elif item.status != "completed":
        item.completed_at = None
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="development.intervention.updated", entity_type="development_intervention", entity_id=str(item.id), metadata={"status": item.status})
    await db.commit()
    await db.refresh(item)
    return _json_intervention(item)

@router.post("/{intervention_id}/interactions", status_code=status.HTTP_201_CREATED)
async def add_interaction(intervention_id: UUID, payload: InteractionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await _intervention_access(intervention_id, user, db, write=True)
    if item.intervention_type not in {"coaching", "mentoring", "experiential"}:
        raise HTTPException(422, "Interactions are not enabled for this intervention type")
    interaction = DevelopmentInteraction(tenant_id=user.tenant_id, intervention_id=item.id, facilitator_id=user.id, interaction_type=payload.interaction_type, occurred_at=payload.occurred_at, duration_minutes=payload.duration_minutes, summary=payload.summary, action_items=payload.action_items)
    db.add(interaction)
    if item.status == "planned":
        item.status = "in_progress"
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="development.interaction.created", entity_type="development_interaction", entity_id=str(interaction.id))
    await db.commit()
    await db.refresh(interaction)
    await db.refresh(item)
    return _json_interaction(interaction)

@router.post("/{intervention_id}/evidence", status_code=status.HTTP_201_CREATED)
async def add_evidence(intervention_id: UUID, payload: EvidenceCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await _intervention_access(intervention_id, user, db, write=True)
    evidence = DevelopmentEvidence(tenant_id=user.tenant_id, intervention_id=item.id, submitted_by=user.id, evidence_type=payload.evidence_type, description=payload.description, observed_at=payload.observed_at, metadata_json={**payload.metadata_json, **({"demonstrated_level": payload.demonstrated_level} if payload.demonstrated_level is not None else {})})
    db.add(evidence)
    if item.status == "planned":
        item.status = "in_progress"
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="development.evidence.submitted", entity_type="development_evidence", entity_id=str(evidence.id))
    await db.commit()
    await db.refresh(evidence)
    return _json_evidence(evidence)

@router.post("/{intervention_id}/evidence/{evidence_id}/verify")
async def verify_evidence(intervention_id: UUID, evidence_id: UUID, user: User = Depends(require_permission("development.recommendations.manage")), db: AsyncSession = Depends(get_db)):
    item = await _intervention_access(intervention_id, user, db, write=True)
    evidence = await db.scalar(select(DevelopmentEvidence).where(DevelopmentEvidence.id == evidence_id, DevelopmentEvidence.intervention_id == item.id, DevelopmentEvidence.tenant_id == user.tenant_id))
    if evidence is None:
        raise HTTPException(404, "Development evidence not found")
    evidence.verification_status = "verified"
    evidence.verified_by = user.id
    evidence.verified_at = datetime.now(timezone.utc)
    recommendation = await db.scalar(select(DevelopmentRecommendation).where(DevelopmentRecommendation.id == item.recommendation_id, DevelopmentRecommendation.tenant_id == user.tenant_id)) if item.recommendation_id else None
    gap = await db.scalar(select(CapabilityGap).where(CapabilityGap.id == recommendation.capability_gap_id, CapabilityGap.tenant_id == user.tenant_id)) if recommendation else None
    level = evidence.metadata_json.get("demonstrated_level") if isinstance(evidence.metadata_json, dict) else None
    if gap is not None and level is not None:
        capability_evidence = await db.scalar(select(CapabilityEvidence).where(CapabilityEvidence.tenant_id == user.tenant_id, CapabilityEvidence.user_id == item.user_id, CapabilityEvidence.target_type == gap.target_type, CapabilityEvidence.target_id == gap.target_id, CapabilityEvidence.source_type == "development_intervention", CapabilityEvidence.source_id == str(evidence.id)))
        if capability_evidence is None:
            capability_evidence = CapabilityEvidence(tenant_id=user.tenant_id, user_id=item.user_id, target_type=gap.target_type, target_id=gap.target_id, evidence_type="development_intervention", source_type="development_intervention", source_id=str(evidence.id), demonstrated_level=level, confidence=100, status="verified", observed_at=evidence.observed_at, assessor_id=user.id, notes=evidence.description, record_metadata={"intervention_id": str(item.id), "recommendation_id": str(recommendation.id) if recommendation else None}, verified_by=user.id, verified_at=evidence.verified_at)
            db.add(capability_evidence)
            evidence.metadata_json = {**evidence.metadata_json, "capability_evidence_created": True}
        recalculation = await _recalculate_user_internal(db, user.tenant_id, item.user_id, user.id)
        evidence.metadata_json = {**evidence.metadata_json, "capability_gap_recalculated": True, "capability_gap_calculation_version": recalculation["calculation_version"]}
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="development.evidence.verified", entity_type="development_evidence", entity_id=str(evidence.id))
    await db.commit()
    await db.refresh(evidence)
    return _json_evidence(evidence)

@router.get("/{intervention_id}/progress")
async def intervention_progress(
    intervention_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _intervention_access(intervention_id, user, db)
    interactions_query = (
        select(func.count(DevelopmentInteraction.id))
        .where(
            DevelopmentInteraction.intervention_id == item.id,
            DevelopmentInteraction.tenant_id == user.tenant_id,
        )
        .scalar_subquery()
    )
    evidence_query = (
        select(func.count(DevelopmentEvidence.id))
        .where(
            DevelopmentEvidence.intervention_id == item.id,
            DevelopmentEvidence.tenant_id == user.tenant_id,
        )
        .scalar_subquery()
    )
    verified_query = (
        select(func.count(DevelopmentEvidence.id))
        .where(
            DevelopmentEvidence.intervention_id == item.id,
            DevelopmentEvidence.tenant_id == user.tenant_id,
            DevelopmentEvidence.verification_status == "verified",
        )
        .scalar_subquery()
    )
    counts = (
        await db.execute(
            select(
                interactions_query.label("interactions"),
                evidence_query.label("evidence_count"),
                verified_query.label("verified_evidence_count"),
            )
        )
    ).one()
    interaction_count = int(counts.interactions or 0)
    total_evidence = int(counts.evidence_count or 0)
    verified_count = int(counts.verified_evidence_count or 0)
    return {
        "intervention_id": str(item.id),
        "status": item.status,
        "interactions": interaction_count,
        "evidence_count": total_evidence,
        "verified_evidence_count": verified_count,
        "progress_signal": (
            "evidence_verified"
            if verified_count
            else "activity_recorded"
            if interaction_count or total_evidence
            else "not_started"
        ),
    }

def _json_intervention(x):
    return {"id": str(x.id), "user_id": str(x.user_id), "plan_id": str(x.plan_id) if x.plan_id else None, "recommendation_id": str(x.recommendation_id) if x.recommendation_id else None, "assignee_id": str(x.assignee_id) if x.assignee_id else None, "intervention_type": x.intervention_type, "title": x.title, "objective": x.objective, "status": x.status, "starts_at": x.starts_at, "due_at": x.due_at, "completed_at": x.completed_at, "metadata_json": x.metadata_json, "created_at": x.created_at, "updated_at": x.updated_at}

def _json_interaction(x):
    return {"id": str(x.id), "intervention_id": str(x.intervention_id), "facilitator_id": str(x.facilitator_id), "interaction_type": x.interaction_type, "occurred_at": x.occurred_at, "duration_minutes": x.duration_minutes, "summary": x.summary, "action_items": x.action_items}

def _json_evidence(x):
    return {"id": str(x.id), "intervention_id": str(x.intervention_id), "submitted_by": str(x.submitted_by), "evidence_type": x.evidence_type, "description": x.description, "observed_at": x.observed_at, "verification_status": x.verification_status, "verified_by": str(x.verified_by) if x.verified_by else None, "verified_at": x.verified_at, "metadata_json": x.metadata_json}
