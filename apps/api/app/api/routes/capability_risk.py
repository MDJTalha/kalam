from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import (
    Capability,
    CapabilityGap,
    RoleRequirement,
    User,
    Role,
    StrategicObjectiveCapability,
    DevelopmentPlan,
    Certificate,
    CapabilityRisk,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()
VERSION = "phase5.v1"
BANDS = ((75, "critical"), (50, "high"), (25, "moderate"), (0, "low"))
WEIGHTS = {
    "gap_severity": 20,
    "criticality": 15,
    "strategic_importance": 15,
    "people_exposure": 10,
    "critical_roles": 10,
    "evidence_confidence": 8,
    "assessment_age": 6,
    "development_inactivity": 5,
    "certification_expiry": 3,
    "concentration": 5,
    "compliance_impact": 2,
    "trend": 1,
}


def _score(value):
    return max(Decimal("0"), min(Decimal("100"), Decimal(str(value)))).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def _band(score):
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "low"


def _criticality(v):
    return {"low": 25, "medium": 50, "high": 75, "critical": 100}.get(
        (v or "medium").lower(), 50
    )


def _severity(v):
    return {
        "minor_gap": 25,
        "moderate_gap": 50,
        "major_gap": 75,
        "critical_gap": 100,
        "insufficient_evidence": 70,
        "met": 0,
        "not_required": 0,
    }.get(v, 0)


def _reason(dim, score):
    labels = {
        "gap_severity": "gap severity",
        "criticality": "requirement criticality",
        "strategic_importance": "strategic importance",
        "people_exposure": "people exposure",
        "critical_roles": "critical-role exposure",
        "evidence_confidence": "evidence confidence",
        "assessment_age": "assessment age",
        "development_inactivity": "development inactivity",
        "certification_expiry": "certificate expiry",
        "concentration": "concentration",
        "compliance_impact": "compliance impact",
        "trend": "trend",
    }
    return f"{labels[dim].capitalize()} contributes {score:.0f}/100 risk."


async def _authorized(user, db):
    if await user_has_permission(user, db, "capability_risk.manage"):
        return None
    if not await user_has_permission(user, db, "capability_risk.read"):
        raise HTTPException(403, "Capability risk access is not permitted")
    reports = (
        (
            await db.execute(
                select(User.id).where(
                    User.tenant_id == user.tenant_id,
                    User.manager_id == user.id,
                    User.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    return {user.id, *reports}


async def _calculate(user, db):
    allowed = await _authorized(user, db)
    gaps_stmt = (
        select(CapabilityGap, RoleRequirement, Role)
        .join(RoleRequirement, RoleRequirement.id == CapabilityGap.role_requirement_id)
        .join(Role, Role.id == RoleRequirement.role_id)
        .where(CapabilityGap.tenant_id == user.tenant_id)
    )
    if allowed is not None:
        gaps_stmt = gaps_stmt.where(CapabilityGap.user_id.in_(allowed))
    rows = (await db.execute(gaps_stmt)).all()
    caps = (
        (
            await db.execute(
                select(Capability).where(Capability.tenant_id == user.tenant_id)
            )
        )
        .scalars()
        .all()
    )
    capmap = {c.id: c for c in caps}
    user_stmt = select(User.id, User.org_unit_id).where(
        User.tenant_id == user.tenant_id,
        User.is_active.is_(True),
    )
    if allowed is not None:
        user_stmt = user_stmt.where(User.id.in_(allowed))
    users = (await db.execute(user_stmt)).all()
    active_ids = {x.id for x in users}
    total_people = max(1, len(active_ids))
    objectives = (
        await db.execute(
            select(
                StrategicObjectiveCapability, StrategicObjectiveCapability.capability_id
            )
        )
    ).all()
    strategic = {}
    for link, _ in objectives:
        strategic[link.capability_id] = max(
            strategic.get(link.capability_id, 0),
            min(100, link.required_level * 20 * link.weight / 100),
        )
    certs = (
        (
            await db.execute(
                select(Certificate.user_id).where(
                    Certificate.tenant_id == user.tenant_id,
                    Certificate.user_id.in_(allowed) if allowed is not None else True,
                    Certificate.expires_at.is_not(None),
                    Certificate.expires_at
                    <= datetime.now(timezone.utc)
                    + __import__("datetime").timedelta(days=90),
                    Certificate.revoked_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    certset = set(certs)
    plans = (
        (
            await db.execute(
                select(DevelopmentPlan.user_id).where(
                    DevelopmentPlan.tenant_id == user.tenant_id,
                    DevelopmentPlan.user_id.in_(allowed) if allowed is not None else True,
                    DevelopmentPlan.status.in_(["active", "in_progress"]),
                )
            )
        )
        .scalars()
        .all()
    )
    active_plan_users = set(plans)
    grouped = {}
    for gap, req, role in rows:
        if req.capability_id is None:
            continue
        grouped.setdefault(req.capability_id, []).append((gap, req, role))
    return grouped, capmap, total_people, active_plan_users, certset, allowed


async def _build(user, db):
    (
        grouped,
        capmap,
        total_people,
        active_plan_users,
        certset,
        allowed,
    ) = await _calculate(user, db)
    now = datetime.now(timezone.utc)
    out = []
    for cid, items in grouped.items():
        cap = capmap.get(cid)
        if not cap:
            continue
        material = [x for x in items if x[0].severity not in {"met", "not_required"}]
        affected = {x[0].user_id for x in material}
        roles = {x[2].id for x in material}
        critical_roles = {
            x[2].id
            for x in material
            if (x[1].criticality or "").lower() in {"high", "critical"}
        }
        severity = max((_severity(x[0].severity) for x in material), default=0)
        avg_gap = sum(float(x[0].gap_value or 0) for x in material) / max(
            1, len(material)
        )
        gap_score = min(100, avg_gap / 4 * 100)
        crit = max(
            (_criticality(x[1].criticality) for x in material),
            default=_criticality(cap.criticality),
        )
        strategic = max(
            strategic_score
            for strategic_score in [
                0,
                min(
                    100,
                    cap.governance.get("strategic_importance", 0)
                    if isinstance(cap.governance, dict)
                    else 0,
                ),
            ]
        )
        obj = (
            (
                await db.execute(
                    select(StrategicObjectiveCapability).where(
                        StrategicObjectiveCapability.capability_id == cid
                    )
                )
            )
            .scalars()
            .all()
        )
        strategic = max(
            strategic,
            max(
                (min(100, x.required_level * 20) * x.weight / 100 for x in obj),
                default=0,
            ),
        )
        confidence = 100 - (
            sum(x[0].evidence_confidence for x in material) / max(1, len(material))
        )
        ages = [
            (now - x[0].evidence_observed_at).days
            for x in material
            if x[0].evidence_observed_at
        ]
        age = min(100, (sum(ages) / max(1, len(ages))) / 180 * 100) if ages else 100
        inactive = (
            100
            if material and not (affected & active_plan_users)
            else (
                50
                if material and len(affected & active_plan_users) < len(affected)
                else 0
            )
        )
        expiring = len(affected & certset)
        certscore = min(100, expiring / max(1, len(affected)) * 100)
        concentration = min(100, len(affected) / total_people * 100)
        people = min(100, len(affected) / max(1, total_people) * 100)
        critical = min(100, len(critical_roles) / max(1, len(roles)) * 100)
        compliance = (
            100
            if (cap.criticality or "").lower() == "critical"
            else 50
            if (cap.criticality or "").lower() == "high"
            else 0
        )
        # Historical risk records are tenant-wide snapshots. They must not
        # influence a manager's direct-report-only risk calculation.
        previous = None
        if allowed is None:
            previous = await db.scalar(
                select(CapabilityRisk).where(
                    CapabilityRisk.tenant_id == user.tenant_id,
                    CapabilityRisk.capability_id == cid,
                )
            )
        trend = (
            50 if previous is None else (100 if float(previous.risk_score) < 0 else 0)
        )
        scores = {
            "gap_severity": _score(max(severity, gap_score)),
            "criticality": _score(crit),
            "strategic_importance": _score(strategic),
            "people_exposure": _score(people),
            "critical_roles": _score(critical),
            "evidence_confidence": _score(confidence),
            "assessment_age": _score(age),
            "development_inactivity": _score(inactive),
            "certification_expiry": _score(certscore),
            "concentration": _score(concentration),
            "compliance_impact": _score(compliance),
            "trend": _score(trend),
        }
        risk = _score(
            sum(scores[k] * Decimal(str(v)) / 100 for k, v in WEIGHTS.items())
            / Decimal("1")
        )
        reasons = [_reason(k, scores[k]) for k in scores if scores[k] >= 50]
        explanation = {
            "formula": "weighted governed dimensions; each dimension is normalized 0-100",
            "weights": WEIGHTS,
            "reasons": reasons,
            "impact": f"{len(affected)} people and {len(critical_roles)} critical/high-criticality roles affected.",
            "action": "Review affected roles, evidence freshness and active development; prioritize critical exposure.",
        }
        out.append(
            (
                cid,
                cap,
                scores,
                risk,
                _band(risk),
                len(affected),
                len(roles),
                len(critical_roles),
                sum(x[0].evidence_count for x in material),
                len(affected & active_plan_users),
                None,
                expiring,
                explanation,
                previous,
            )
        )
    return out


@router.get("")
async def list_risks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    risk_level: str | None = None,
    q: str | None = Query(None, max_length=100),
):
    if not await user_has_permission(
        user, db, "capability_risk.read"
    ) and not await user_has_permission(user, db, "capability_risk.manage"):
        raise HTTPException(403, "Capability risk access is not permitted")
    rows = await _build(user, db)
    out = []
    for (
        cid,
        cap,
        scores,
        risk,
        band,
        people,
        roles,
        critical_roles,
        evidence,
        plans,
        age,
        expiring,
        explanation,
        _,
    ) in rows:
        if risk_level and band != risk_level:
            continue
        if (
            q
            and q.lower() not in cap.name.lower()
            and q.lower() not in cap.code.lower()
        ):
            continue
        out.append(
            {
                "capability_id": str(cid),
                "capability": cap.name,
                "risk_score": float(risk),
                "risk_level": band,
                "affected_people": people,
                "affected_roles": roles,
                "critical_roles_affected": critical_roles,
                "evidence_count": evidence,
                "development_active_count": plans,
                "certification_expiring_count": expiring,
                "dimensions": {k: float(v) for k, v in scores.items()},
                "explanation": explanation,
                "calculation_version": VERSION,
            }
        )
    return sorted(out, key=lambda x: x["risk_score"], reverse=True)[:250]


@router.get("/{capability_id}")
async def risk_detail(
    capability_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await user_has_permission(
        user, db, "capability_risk.read"
    ) and not await user_has_permission(user, db, "capability_risk.manage"):
        raise HTTPException(403, "Capability risk access is not permitted")
    rows = await _build(user, db)
    item = next((x for x in rows if x[0] == capability_id), None)
    if not item:
        raise HTTPException(404, "Capability risk not found")
    (
        cid,
        cap,
        scores,
        risk,
        band,
        people,
        roles,
        critical_roles,
        evidence,
        plans,
        age,
        expiring,
        explanation,
        _,
    ) = item
    allowed = await _authorized(user, db)
    stmt = (
        select(CapabilityGap, RoleRequirement, Role, User)
        .join(RoleRequirement, RoleRequirement.id == CapabilityGap.role_requirement_id)
        .join(Role, Role.id == RoleRequirement.role_id)
        .join(User, User.id == CapabilityGap.user_id)
        .where(
            CapabilityGap.tenant_id == user.tenant_id,
            CapabilityGap.target_type == "capability",
            CapabilityGap.target_id == cid,
        )
    )
    if allowed is not None:
        stmt = stmt.where(CapabilityGap.user_id.in_(allowed))
    details = []
    for gap, req, role, u in (await db.execute(stmt)).all():
        details.append(
            {
                "person_id": str(u.id),
                "person": f"{u.first_name} {u.last_name}".strip() or u.email,
                "role": role.name,
                "required_level": float(req.required_level),
                "demonstrated_level": float(gap.demonstrated_level)
                if gap.demonstrated_level is not None
                else None,
                "gap": float(gap.gap_value) if gap.gap_value is not None else None,
                "severity": gap.severity,
                "evidence_confidence": gap.evidence_confidence,
                "evidence_observed_at": gap.evidence_observed_at,
            }
        )
    return {
        "capability_id": str(cid),
        "capability": cap.name,
        "risk_score": float(risk),
        "risk_level": band,
        "dimensions": {k: float(v) for k, v in scores.items()},
        "explanation": explanation,
        "affected_people": people,
        "affected_roles": roles,
        "critical_roles_affected": critical_roles,
        "development_active_count": plans,
        "certification_expiring_count": expiring,
        "details": details,
        "calculation_version": VERSION,
    }


@router.post("/recalculate")
async def recalculate(
    user: User = Depends(require_permission("capability_risk.manage")),
    db: AsyncSession = Depends(get_db),
):
    rows = await _build(user, db)
    now = datetime.now(timezone.utc)
    count = 0
    for (
        cid,
        cap,
        scores,
        risk,
        band,
        people,
        roles,
        critical_roles,
        evidence,
        plans,
        age,
        expiring,
        explanation,
        previous,
    ) in rows:
        obj = await db.scalar(
            select(CapabilityRisk).where(
                CapabilityRisk.tenant_id == user.tenant_id,
                CapabilityRisk.capability_id == cid,
            )
        )
        if obj is None:
            obj = CapabilityRisk(tenant_id=user.tenant_id, capability_id=cid)
            db.add(obj)
        for key, value in scores.items():
            setattr(obj, f"{key}_score", value)
        obj.risk_score = risk
        obj.risk_level = band
        obj.affected_people = people
        obj.affected_roles = roles
        obj.critical_roles_affected = critical_roles
        obj.evidence_count = evidence
        obj.development_active_count = plans
        obj.certification_expiring_count = expiring
        obj.explanation = explanation
        obj.calculation_version = VERSION
        obj.computed_at = now
        count += 1
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.risk.recalculated",
        entity_type="capability_risk",
        entity_id=str(user.tenant_id),
        metadata={"records": count, "version": VERSION},
    )
    await db.commit()
    return {
        "status": "recalculated",
        "records": count,
        "calculation_version": VERSION,
        "computed_at": now,
    }
