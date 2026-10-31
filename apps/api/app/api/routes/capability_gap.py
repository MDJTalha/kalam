from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from types import SimpleNamespace
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import (
    Capability,
    CapabilityCompetency,
    CapabilityEvidence,
    CapabilityGap,
    Competency,
    OrgUnit,
    Role,
    RoleRequirement,
    Skill,
    User,
    UserRole,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()
SEVERITIES = {
    "not_required",
    "met",
    "minor_gap",
    "moderate_gap",
    "major_gap",
    "critical_gap",
    "insufficient_evidence",
}
FRESHNESS_DAYS = 180
VERSION = "phase4.v1"


def _severity(required, demonstrated):
    if demonstrated is None:
        return "insufficient_evidence"
    gap = max(Decimal("0"), required - demonstrated)
    if gap <= 0:
        return "met"
    if gap <= Decimal(".50"):
        return "minor_gap"
    if gap <= Decimal("1.50"):
        return "moderate_gap"
    if gap <= Decimal("2.50"):
        return "major_gap"
    return "critical_gap"


def _round(v):
    return v.quantize(Decimal(".01"), rounding=ROUND_HALF_UP) if v is not None else None


def _gap_json(g, role_name, target_name, evidence_freshness="unknown"):
    return {
        "id": str(g.id),
        "user_id": str(g.user_id),
        "role_requirement_id": str(g.role_requirement_id),
        "role": role_name,
        "target_type": g.target_type,
        "target_id": str(g.target_id),
        "target": target_name,
        "required_level": float(g.required_level),
        "demonstrated_level": float(g.demonstrated_level)
        if g.demonstrated_level is not None
        else None,
        "gap": float(g.gap_value) if g.gap_value is not None else None,
        "severity": g.severity,
        "criticality": g.criticality,
        "weight": g.weight,
        "evidence_confidence": g.evidence_confidence,
        "evidence_count": g.evidence_count,
        "evidence_observed_at": g.evidence_observed_at,
        "evidence_freshness": evidence_freshness,
        "calculation_version": g.calculation_version,
        "computed_at": g.computed_at,
    }


async def _authorized_user_ids(user, db):
    if await user_has_permission(user, db, "capability_gaps.manage"):
        return None
    if not await user_has_permission(user, db, "capability_gaps.read"):
        raise HTTPException(403, "Capability gap access is not permitted")
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


async def _evidence_map(db, tenant_id, user_ids):
    stmt = select(CapabilityEvidence).where(
        CapabilityEvidence.tenant_id == tenant_id,
        CapabilityEvidence.status == "verified",
    )
    if user_ids:
        stmt = stmt.where(CapabilityEvidence.user_id.in_(user_ids))
    rows = (await db.execute(stmt)).scalars().all()
    now = datetime.now(timezone.utc)
    out = {}
    for e in rows:
        if e.expires_at and e.expires_at <= now:
            continue
        if e.observed_at and e.observed_at < now - timedelta(days=FRESHNESS_DAYS):
            continue
        key = (e.user_id, e.target_type, e.target_id)
        old = out.get(key)
        if old is None or (e.observed_at or now) > (old.observed_at or now):
            out[key] = e
    return out


async def _competency_fallback(
    db,
    tenant_id,
    user_id,
    capability_id,
    evidence,
    links_by_capability=None,
):
    links = (
        links_by_capability.get(capability_id, [])
        if links_by_capability is not None
        else (
            await db.execute(
                select(CapabilityCompetency).where(
                    CapabilityCompetency.capability_id == capability_id
                )
            )
        )
        .scalars()
        .all()
    )
    vals = []
    for link in links:
        e = evidence.get((user_id, "competency", link.competency_id))
        if e:
            vals.append((e.demonstrated_level, link.weight, e))
    if not vals:
        return None, None, 0, None
    total = sum(Decimal(str(w)) for _, w, _ in vals)
    level = sum(level_value * Decimal(str(w)) for level_value, w, _ in vals) / total
    confidence = round(
        sum(Decimal(str(e.confidence)) * Decimal(str(w)) for _, w, e in vals) / total
    )
    newest = max(
        (e for _, _, e in vals),
        key=lambda x: x.observed_at or datetime.min.replace(tzinfo=timezone.utc),
    )
    return _round(level), confidence, len(vals), newest


async def _compute(
    db,
    user,
    only_user_id=None,
    role_id=None,
    bypass_authorization=False,
    forced_user_ids: set[UUID] | None = None,
):
    allowed = (
        forced_user_ids
        if forced_user_ids is not None
        else None if bypass_authorization else await _authorized_user_ids(user, db)
    )
    if only_user_id:
        if allowed is not None and only_user_id not in allowed:
            raise HTTPException(403, "You may only view your own capability gaps")
        allowed = {only_user_id}
    users = (
        (
            await db.execute(
                select(User).where(
                    User.tenant_id == user.tenant_id,
                    User.is_active.is_(True),
                    User.id.in_(allowed) if allowed else True,
                )
            )
        )
        .scalars()
        .all()
    )
    roles = (
        (await db.execute(select(Role).where(Role.tenant_id == user.tenant_id)))
        .scalars()
        .all()
    )
    if role_id:
        roles = [r for r in roles if r.id == role_id]
        if not roles:
            raise HTTPException(404, "Role not found")
    role_map = {r.id: r for r in roles}
    now = datetime.now(timezone.utc)
    assignments = (
        (
            await db.execute(
                select(UserRole).where(
                    UserRole.user_id.in_([u.id for u in users]),
                    UserRole.role_id.in_(list(role_map)),
                )
            )
        )
        .scalars()
        .all()
    )
    reqs = (
        (
            await db.execute(
                select(RoleRequirement).where(
                    RoleRequirement.tenant_id == user.tenant_id,
                    RoleRequirement.role_id.in_(list(role_map)),
                    RoleRequirement.effective_from.is_(None)
                    | (RoleRequirement.effective_from <= now),
                    RoleRequirement.effective_to.is_(None)
                    | (RoleRequirement.effective_to >= now),
                )
            )
        )
        .scalars()
        .all()
    )
    capability_ids = {r.capability_id for r in reqs if r.capability_id is not None}
    competency_ids = {r.competency_id for r in reqs if r.competency_id is not None}
    skill_ids = {r.skill_id for r in reqs if r.skill_id is not None}
    target_names = {}
    if capability_ids:
        capability_rows = (
            await db.execute(
                select(Capability.id, Capability.name).where(
                    Capability.tenant_id == user.tenant_id,
                    Capability.id.in_(capability_ids),
                )
            )
        ).all()
        target_names.update(
            {("capability", row.id): row.name for row in capability_rows}
        )
    if competency_ids:
        competency_rows = (
            await db.execute(
                select(Competency.id, Competency.name).where(
                    Competency.tenant_id == user.tenant_id,
                    Competency.id.in_(competency_ids),
                )
            )
        ).all()
        target_names.update(
            {("competency", row.id): row.name for row in competency_rows}
        )
    if skill_ids:
        skill_rows = (
            await db.execute(
                select(Skill.id, Skill.name).where(
                    Skill.tenant_id == user.tenant_id,
                    Skill.id.in_(skill_ids),
                )
            )
        ).all()
        target_names.update({("skill", row.id): row.name for row in skill_rows})
    links_by_capability = {}
    if capability_ids:
        capability_competency_rows = (
            (
                await db.execute(
                    select(CapabilityCompetency).where(
                        CapabilityCompetency.capability_id.in_(capability_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        for link in capability_competency_rows:
            links_by_capability.setdefault(link.capability_id, []).append(link)
    req_by_role = {}
    for r in reqs:
        req_by_role.setdefault(r.role_id, []).append(r)
    evidence = await _evidence_map(db, user.tenant_id, {u.id for u in users})
    result = []
    names = {
        (r.id, r.capability_id or r.competency_id or r.skill_id): target_names.get(
            (
                "capability"
                if r.capability_id
                else "competency"
                if r.competency_id
                else "skill",
                r.capability_id or r.competency_id or r.skill_id,
            )
        )
        for r in reqs
    }
    for a in assignments:
        for req in req_by_role.get(a.role_id, []):
            tid = req.capability_id or req.competency_id or req.skill_id
            typ = (
                "capability"
                if req.capability_id
                else "competency"
                if req.competency_id
                else "skill"
            )
            e = evidence.get((a.user_id, typ, tid))
            level = None
            confidence = 0
            count = 0
            observed = None
            if e:
                level = e.demonstrated_level
                confidence = e.confidence
                count = 1
                observed = e.observed_at
            elif typ == "capability":
                level, confidence, count, e = await _competency_fallback(
                    db,
                    user.tenant_id,
                    a.user_id,
                    tid,
                    evidence,
                    links_by_capability,
                )
                observed = e.observed_at if e else None
            sev = _severity(
                Decimal(str(req.required_level)),
                Decimal(str(level)) if level is not None else None,
            )
            gap = (
                max(
                    Decimal("0"), Decimal(str(req.required_level)) - Decimal(str(level))
                )
                if level is not None
                else None
            )
            freshness = (
                "unknown"
                if observed is None
                else ("fresh" if (now - observed).days <= FRESHNESS_DAYS else "stale")
            )
            if freshness == "stale" and sev != "met":
                sev = "insufficient_evidence"
            result.append(
                {
                    "user_id": a.user_id,
                    "requirement": req,
                    "role": role_map[a.role_id],
                    "target_type": typ,
                    "target_id": tid,
                    "target_name": names.get((req.id, tid)),
                    "demonstrated": level,
                    "confidence": confidence,
                    "count": count,
                    "observed": observed,
                    "freshness": freshness,
                    "severity": sev,
                    "gap": _round(gap),
                }
            )
    return result


def _row(item):
    req = item["requirement"]
    role = item["role"]
    return {
        "user_id": str(item["user_id"]),
        "role_id": str(role.id),
        "role": role.name,
        "role_requirement_id": str(req.id),
        "target_type": item["target_type"],
        "target_id": str(item["target_id"]),
        "target": item["target_name"],
        "required_level": float(req.required_level),
        "demonstrated_level": float(item["demonstrated"])
        if item["demonstrated"] is not None
        else None,
        "gap": float(item["gap"]) if item["gap"] is not None else None,
        "severity": item["severity"],
        "criticality": req.criticality,
        "weight": req.weight,
        "evidence_confidence": item["confidence"],
        "evidence_count": item["count"],
        "evidence_observed_at": item["observed"],
        "evidence_freshness": item["freshness"],
        "calculation_version": VERSION,
    }


@router.get("")
async def list_gaps(
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    severity: str | None = None,
    target_type: str | None = None,
    q: str | None = Query(None, max_length=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await _compute(db, user, user_id, role_id)
    if severity and severity not in SEVERITIES:
        raise HTTPException(422, "Invalid gap severity")
    if target_type and target_type not in {"capability", "competency", "skill"}:
        raise HTTPException(422, "Invalid target type")
    out = [
        _row(x)
        for x in rows
        if (not severity or x["severity"] == severity)
        and (not target_type or x["target_type"] == target_type)
    ]
    if q:
        needle = q.strip().lower()
        out = [
            x
            for x in out
            if needle in (x["target"] or "").lower() or needle in x["role"].lower()
        ]
    return out[:250]


@router.get("/summary")
async def gap_summary(
    scope: str = "enterprise",
    scope_id: UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if scope not in {
        "enterprise",
        "business_unit",
        "department",
        "team",
        "role",
        "person",
        "direct_reports",
    }:
        raise HTTPException(422, "Invalid scope")
    forced_user_ids = None
    if scope == "direct_reports":
        if not await user_has_permission(user, db, "team.read"):
            raise HTTPException(403, "Direct-report capability scope is not permitted")
        reports = (
            await db.execute(
                select(User.id).where(
                    User.tenant_id == user.tenant_id,
                    User.manager_id == user.id,
                    User.is_active.is_(True),
                )
            )
        ).scalars().all()
        forced_user_ids = {user.id, *reports}
    rows = await _compute(
        db,
        user,
        scope_id if scope == "person" else None,
        scope_id if scope == "role" else None,
        forced_user_ids=forced_user_ids,
    )
    if scope in {"business_unit", "department", "team"}:
        if scope_id is None:
            raise HTTPException(422, "scope_id is required")
        units = (
            (
                await db.execute(
                    select(OrgUnit).where(OrgUnit.tenant_id == user.tenant_id)
                )
            )
            .scalars()
            .all()
        )
        unit_map = {x.id: x for x in units}
        selected = unit_map.get(scope_id)
        if selected is None:
            raise HTTPException(404, "Organization unit not found")
        descendants = {selected.id}
        changed = True
        while changed:
            changed = False
            for x in units:
                if x.parent_id in descendants and x.id not in descendants:
                    descendants.add(x.id)
                    changed = True
        rows = (
            [
                x
                for x in rows
                if next(
                    (
                        u
                        for u in unit_map.values()
                        if u.id == next((z.org_unit_id for z in []), None)
                    ),
                    None,
                )
                is not None
            ]
            if False
            else rows
        )
        user_ids = {
            u.id
            for u in (
                await db.execute(
                    select(User).where(
                        User.tenant_id == user.tenant_id,
                        User.org_unit_id.in_(descendants),
                        User.is_active.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        }
        rows = [x for x in rows if x["user_id"] in user_ids]
    total = len(rows)
    by: dict[str, int] = {}
    for x in rows:
        by[x["severity"]] = by.get(x["severity"], 0) + 1
    material = [
        x
        for x in rows
        if x["severity"] in {"minor_gap", "moderate_gap", "major_gap", "critical_gap"}
    ]
    weighted = sum(float(x["gap"] or 0) * x["requirement"].weight for x in material)
    weight = sum(x["requirement"].weight for x in material)
    return {
        "scope": scope,
        "scope_id": str(scope_id) if scope_id else None,
        "total_requirements": total,
        "material_gaps": len(material),
        "counts": by,
        "critical_exposure": by.get("critical_gap", 0),
        "major_exposure": by.get("major_gap", 0),
        "weighted_gap": round(weighted / weight, 2) if weight else 0,
        "calculation_version": VERSION,
        "freshness_days": FRESHNESS_DAYS,
    }


async def _recalculate_user_internal(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, actor_id: UUID | None = None
):
    """Recalculate one user's persisted gaps inside an existing transaction.

    This is an internal orchestration primitive for evidence/assessment workflows;
    callers must already have passed their own authorization boundary.
    """
    actor = SimpleNamespace(id=actor_id or user_id, tenant_id=tenant_id)
    rows = await _compute(db, actor, user_id, bypass_authorization=True)
    now = datetime.now(timezone.utc)
    seen = {(x["user_id"], x["requirement"].id) for x in rows}
    for x in rows:
        req = x["requirement"]
        existing = await db.scalar(
            select(CapabilityGap).where(
                CapabilityGap.tenant_id == tenant_id,
                CapabilityGap.user_id == x["user_id"],
                CapabilityGap.role_requirement_id == req.id,
            )
        )
        if existing is None:
            existing = CapabilityGap(
                tenant_id=tenant_id,
                user_id=x["user_id"],
                role_requirement_id=req.id,
                target_type=x["target_type"],
                target_id=x["target_id"],
                required_level=req.required_level,
                severity=x["severity"],
                criticality=req.criticality,
                weight=req.weight,
                evidence_confidence=x["confidence"]
                if x["confidence"] is not None
                else 0,
                evidence_count=x["count"],
            )
            db.add(existing)
        existing.target_type = x["target_type"]
        existing.target_id = x["target_id"]
        existing.required_level = req.required_level
        existing.demonstrated_level = x["demonstrated"]
        existing.gap_value = x["gap"]
        existing.severity = x["severity"]
        existing.criticality = req.criticality
        existing.weight = req.weight
        existing.evidence_confidence = (
            x["confidence"] if x["confidence"] is not None else 0
        )
        existing.evidence_count = x["count"]
        existing.evidence_observed_at = x["observed"]
        existing.calculation_version = VERSION
        existing.computed_at = now
    existing_rows = (
        (
            await db.execute(
                select(CapabilityGap)
                .join(
                    RoleRequirement,
                    RoleRequirement.id == CapabilityGap.role_requirement_id,
                )
                .where(
                    CapabilityGap.tenant_id == tenant_id,
                    CapabilityGap.user_id == user_id,
                )
            )
        )
        .scalars()
        .all()
    )
    for stale in existing_rows:
        if (stale.user_id, stale.role_requirement_id) not in seen:
            await db.delete(stale)
    return {"records": len(rows), "calculation_version": VERSION, "computed_at": now}


@router.post("/recalculate")
async def recalculate(
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    user: User = Depends(require_permission("capability_gaps.manage")),
    db: AsyncSession = Depends(get_db),
):
    rows = await _compute(db, user, user_id, role_id)
    now = datetime.now(timezone.utc)
    created = 0
    seen = {(x["user_id"], x["requirement"].id) for x in rows}
    for x in rows:
        req = x["requirement"]
        existing = await db.scalar(
            select(CapabilityGap).where(
                CapabilityGap.tenant_id == user.tenant_id,
                CapabilityGap.user_id == x["user_id"],
                CapabilityGap.role_requirement_id == req.id,
            )
        )
        if existing is None:
            existing = CapabilityGap(
                tenant_id=user.tenant_id,
                user_id=x["user_id"],
                role_requirement_id=req.id,
                target_type=x["target_type"],
                target_id=x["target_id"],
                required_level=req.required_level,
                severity=x["severity"],
                criticality=req.criticality,
                weight=req.weight,
                evidence_confidence=x["confidence"]
                if x["confidence"] is not None
                else 0,
                evidence_count=x["count"],
            )
            db.add(existing)
            created += 1
        existing.target_type = x["target_type"]
        existing.target_id = x["target_id"]
        existing.required_level = req.required_level
        existing.demonstrated_level = x["demonstrated"]
        existing.gap_value = x["gap"]
        existing.severity = x["severity"]
        existing.criticality = req.criticality
        existing.weight = req.weight
        existing.evidence_confidence = (
            x["confidence"] if x["confidence"] is not None else 0
        )
        existing.evidence_count = x["count"]
        existing.evidence_observed_at = x["observed"]
        existing.calculation_version = VERSION
        existing.computed_at = now
    affected_users = {u for u, _ in seen}
    if not seen and user_id:
        affected_users = {user_id}
    if affected_users:
        conditions = [
            CapabilityGap.tenant_id == user.tenant_id,
            CapabilityGap.user_id.in_(affected_users),
        ]
        if role_id:
            conditions.append(RoleRequirement.role_id == role_id)
        existing_rows = (
            (
                await db.execute(
                    select(CapabilityGap)
                    .join(
                        RoleRequirement,
                        RoleRequirement.id == CapabilityGap.role_requirement_id,
                    )
                    .where(*conditions)
                )
            )
            .scalars()
            .all()
        )
        for stale in existing_rows:
            if (stale.user_id, stale.role_requirement_id) not in seen:
                await db.delete(stale)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="capability.gaps.recalculated",
        entity_type="capability_gap",
        entity_id=str(user_id or role_id or user.tenant_id),
        metadata={"records": len(rows), "created": created, "version": VERSION},
    )
    await db.commit()
    return {
        "status": "recalculated",
        "records": len(rows),
        "created": created,
        "calculation_version": VERSION,
        "computed_at": now,
    }


@router.get("/snapshots")
async def list_snapshots(
    user_id: UUID | None = None,
    severity: str | None = None,
    user: User = Depends(require_permission("capability_gaps.read")),
    db: AsyncSession = Depends(get_db),
):
    allowed = await _authorized_user_ids(user, db)
    if user_id:
        if allowed is not None and user_id not in allowed:
            raise HTTPException(
                403, "You may only view authorized capability gap snapshots"
            )
        allowed = {user_id}
    stmt = (
        select(CapabilityGap, RoleRequirement, Role)
        .join(RoleRequirement, RoleRequirement.id == CapabilityGap.role_requirement_id)
        .join(Role, Role.id == RoleRequirement.role_id)
        .where(CapabilityGap.tenant_id == user.tenant_id)
    )
    if allowed is not None:
        stmt = stmt.where(CapabilityGap.user_id.in_(allowed))
    if severity:
        stmt = stmt.where(CapabilityGap.severity == severity)
    rows = (
        await db.execute(stmt.order_by(CapabilityGap.computed_at.desc()).limit(250))
    ).all()
    return [
        _gap_json(
            g,
            role.name,
            None,
            "fresh"
            if not g.evidence_observed_at
            or (datetime.now(timezone.utc) - g.evidence_observed_at).days
            <= FRESHNESS_DAYS
            else "stale",
        )
        for g, _, role in rows
    ]
