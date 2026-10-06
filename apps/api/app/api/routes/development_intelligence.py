"""Phase 6 governed development intervention intelligence."""

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, user_has_permission
from app.db.models import (
    CapabilityCompetency,
    CapabilityEvidence,
    CapabilityGap,
    CapabilityRisk,
    CapabilitySkill,
    Course,
    CourseSkill,
    DevelopmentPlan,
    DevelopmentIntervention,
    DevelopmentRecommendation,
    Enrollment,
    LearningPath,
    LearningPathItem,
    LiveSession,
    Program,
    ProgramCourse,
    Role,
    RoleRequirement,
    User,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()
VERSION = "phase6.v2"


def _priority(gap, risk):
    critical = (gap.criticality or "").lower()
    score = float(risk.risk_score) if risk else 0
    if critical == "critical" or score >= 75 or float(gap.gap_value or 0) >= 3:
        return "critical"
    if critical == "high" or score >= 50 or float(gap.gap_value or 0) >= 2:
        return "high"
    return "medium"


def _preference(user, kind):
    prefs = user.preferences if isinstance(user.preferences, dict) else {}
    dev = (
        prefs.get("development", {})
        if isinstance(prefs.get("development", {}), dict)
        else {}
    )
    weights = (
        dev.get("intervention_weights", {})
        if isinstance(dev.get("intervention_weights", {}), dict)
        else {}
    )
    try:
        return max(-15, min(15, float(weights.get(kind, 0))))
    except (TypeError, ValueError):
        return 0


async def _scope(user, db, target_id):
    if target_id is None or target_id == user.id:
        return user.id
    if not await user_has_permission(user, db, "users.read"):
        raise HTTPException(403, "You cannot view another user's recommendations")
    target = await db.scalar(
        select(User).where(
            User.id == target_id,
            User.tenant_id == user.tenant_id,
            User.is_active.is_(True),
        )
    )
    if target is None:
        raise HTTPException(404, "User not found")
    if target.manager_id != user.id and not await user_has_permission(
        user, db, "development.recommendations.manage"
    ):
        raise HTTPException(403, "Manager scope does not include this user")
    return target.id


async def _generate(user, db, target_id):
    uid = await _scope(user, db, target_id)
    gaps = (
        (
            await db.execute(
                select(CapabilityGap)
                .where(
                    CapabilityGap.tenant_id == user.tenant_id,
                    CapabilityGap.user_id == uid,
                    CapabilityGap.severity.notin_(["met", "not_required"]),
                )
                .order_by(CapabilityGap.gap_value.desc().nullslast())
            )
        )
        .scalars()
        .all()
    )
    enrollments = (
        await db.execute(
            select(Enrollment.course_id, Enrollment.status).where(
                Enrollment.tenant_id == user.tenant_id, Enrollment.user_id == uid
            )
        )
    ).all()
    history = {cid: st for cid, st in enrollments}
    plans = (
        (
            await db.execute(
                select(DevelopmentPlan).where(
                    DevelopmentPlan.tenant_id == user.tenant_id,
                    DevelopmentPlan.user_id == uid,
                )
            )
        )
        .scalars()
        .all()
    )
    prior_goals = [
        str(goal.get("title", "")).lower()
        for plan in plans
        for goal in (plan.goals or [])
        if isinstance(goal, dict)
    ]

    requirement_ids = {gap.role_requirement_id for gap in gaps}
    requirement_rows = (
        await db.execute(
            select(RoleRequirement).where(
                RoleRequirement.tenant_id == user.tenant_id,
                RoleRequirement.id.in_(requirement_ids or [UUID(int=0)]),
            )
        )
    ).scalars().all()
    requirements_by_id = {row.id: row for row in requirement_rows}

    role_ids = {row.role_id for row in requirement_rows}
    role_rows = (
        await db.execute(
            select(Role).where(
                Role.tenant_id == user.tenant_id,
                Role.id.in_(role_ids or [UUID(int=0)]),
            )
        )
    ).scalars().all()
    roles_by_id = {row.id: row for row in role_rows}

    capability_target_ids = {
        gap.target_id for gap in gaps if gap.target_type == "capability"
    }
    risk_by_capability = {}
    if capability_target_ids:
        risk_rows = (
            await db.execute(
                select(CapabilityRisk).where(
                    CapabilityRisk.tenant_id == user.tenant_id,
                    CapabilityRisk.capability_id.in_(capability_target_ids),
                )
            )
        ).scalars().all()
        risk_by_capability = {
            row.capability_id: row
            for row in risk_rows
        }

    evidence_target_ids = {gap.target_id for gap in gaps}
    evidence_rows = []
    if evidence_target_ids:
        latest_ranked = (
            select(
                CapabilityEvidence.target_type,
                CapabilityEvidence.target_id,
                CapabilityEvidence.observed_at,
                CapabilityEvidence.confidence,
                func.row_number()
                .over(
                    partition_by=[
                        CapabilityEvidence.target_type,
                        CapabilityEvidence.target_id,
                    ],
                    order_by=CapabilityEvidence.observed_at.desc(),
                )
                .label("evidence_rank"),
            )
            .where(
                CapabilityEvidence.tenant_id == user.tenant_id,
                CapabilityEvidence.user_id == uid,
                CapabilityEvidence.target_id.in_(evidence_target_ids),
            )
            .subquery()
        )
        evidence_rows = (
            await db.execute(
                select(
                    latest_ranked.c.target_type,
                    latest_ranked.c.target_id,
                    latest_ranked.c.observed_at,
                    latest_ranked.c.confidence,
                )
                .where(latest_ranked.c.evidence_rank <= 20)
                .order_by(
                    latest_ranked.c.target_type,
                    latest_ranked.c.target_id,
                    latest_ranked.c.observed_at.desc(),
                )
            )
        ).all()
    evidence_by_target = {}
    for row in evidence_rows:
        evidence_by_target.setdefault((row.target_type, row.target_id), []).append(
            (row.observed_at, row.confidence)
        )

    capability_ids = {
        gap.target_id for gap in gaps if gap.target_type == "capability"
    }
    competency_ids = {
        gap.target_id for gap in gaps if gap.target_type == "competency"
    }
    capability_links_by_competency = {}
    if competency_ids:
        link_rows = (
            await db.execute(
                select(CapabilityCompetency).where(
                    CapabilityCompetency.competency_id.in_(competency_ids)
                )
            )
        ).scalars().all()
        for link in link_rows:
            capability_links_by_competency.setdefault(link.competency_id, []).append(
                link.capability_id
            )
            capability_ids.add(link.capability_id)

    skill_rows = []
    if capability_ids:
        skill_rows = (
            await db.execute(
                select(CapabilitySkill).where(
                    CapabilitySkill.capability_id.in_(capability_ids)
                )
            )
        ).scalars().all()
    skills_by_capability = {}
    for row in skill_rows:
        skills_by_capability.setdefault(row.capability_id, []).append(
            (row.skill_id, row.weight)
        )

    all_learning_skill_ids = set()
    for skill_rows_for_capability in skills_by_capability.values():
        all_learning_skill_ids.update(skill_id for skill_id, _ in skill_rows_for_capability)
    all_learning_skill_ids.update(
        gap.target_id for gap in gaps if gap.target_type == "skill"
    )
    course_rows_by_skill = {}
    if all_learning_skill_ids:
        all_course_rows = (
            await db.execute(
                select(Course, CourseSkill.skill_id, CourseSkill.target_proficiency)
                .join(CourseSkill, CourseSkill.course_id == Course.id)
                .where(
                    Course.tenant_id == user.tenant_id,
                    Course.status == "published",
                    CourseSkill.skill_id.in_(all_learning_skill_ids),
                )
            )
        ).all()
        for course_row in all_course_rows:
            course_rows_by_skill.setdefault(course_row[1], []).append(course_row)

    out = []
    now = datetime.now(timezone.utc)
    for gap in gaps:
        requirement = requirements_by_id.get(gap.role_requirement_id)
        role = roles_by_id.get(requirement.role_id) if requirement else None
        risk = (
            risk_by_capability.get(gap.target_id)
            if gap.target_type == "capability"
            else None
        )
        priority = _priority(gap, risk)
        urgency = {"critical": 100, "high": 80, "medium": 60, "low": 40}[priority]
        evidence_rows = evidence_by_target.get((gap.target_type, gap.target_id), [])
        latest = evidence_rows[0][0] if evidence_rows else None
        evidence_age = max(0, (now - latest).days) if latest else 9999
        freshness = max(0, 100 - min(100, evidence_age / 180 * 100))
        assessment_history = min(100, len(evidence_rows) * 20)
        if gap.target_type == "capability":
            skill_rows = skills_by_capability.get(gap.target_id, [])
        elif gap.target_type == "competency":
            skill_rows = [
                row
                for capability_id in capability_links_by_competency.get(
                    gap.target_id, []
                )
                for row in skills_by_capability.get(capability_id, [])
            ]
        else:
            skill_rows = [(gap.target_id, 100)]
        skill_ids = {sid for sid, _ in skill_rows}
        course_rows = [
            row
            for skill_id in skill_ids
            for row in course_rows_by_skill.get(skill_id, [])
        ]
        course_scores = {}
        for course, skill_id, target in course_rows:
            fit = min(100, float(target) / max(1, float(gap.required_level)) * 100)
            course_scores[course.id] = max(course_scores.get(course.id, 0), fit)
        for course, _, _ in course_rows:
            course_id = course.id
            fit = course_scores.get(course_id, 0)
            prior_penalty = (
                30
                if history.get(course_id) in {"completed", "enrolled", "in_progress"}
                else 0
            )
            score = max(
                0,
                min(
                    100,
                    0.42 * fit
                    + 0.25 * urgency
                    + 0.13 * float(gap.evidence_confidence)
                    + 0.10 * freshness
                    + 0.10 * assessment_history
                    - prior_penalty
                    + _preference(user, "learning"),
                ),
            )
            out.append(
                (
                    uid,
                    gap,
                    role,
                    "learning",
                    "course",
                    str(course_id),
                    course.title,
                    float(score),
                    priority,
                    max(
                        14,
                        min(
                            180, 30 + int((5 - float(gap.demonstrated_level or 0)) * 30)
                        ),
                    ),
                    {
                        "course_id": str(course_id),
                        "fit": round(fit, 1),
                        "prior_status": history.get(course_id),
                        "role": role.name if role else None,
                        "evidence_age_days": evidence_age,
                        "assessment_history_count": len(evidence_rows),
                    },
                )
            )
        path_rows = (
            await db.execute(
                select(LearningPath, LearningPathItem.course_id)
                .join(LearningPathItem, LearningPathItem.path_id == LearningPath.id)
                .where(
                    LearningPath.tenant_id == user.tenant_id,
                    LearningPath.status == "published",
                    LearningPathItem.course_id.in_(
                        list(course_scores) or [UUID(int=0)]
                    ),
                )
            )
        ).all()
        path_courses = {}
        for path, cid in path_rows:
            path_courses.setdefault(path.id, [path, []])[1].append(cid)
        for path, cids in path_courses.values():
            fit = sum(course_scores.get(cid, 0) for cid in cids) / max(1, len(cids))
            score = max(
                0,
                min(
                    100,
                    0.45 * fit
                    + 0.30 * urgency
                    + 0.15 * freshness
                    + 0.10 * assessment_history
                    + _preference(user, "learning"),
                ),
            )
            out.append(
                (
                    uid,
                    gap,
                    role,
                    "learning",
                    "learning_path",
                    str(path.id),
                    path.title,
                    float(score),
                    priority,
                    max(
                        21,
                        min(
                            180, 45 + int((5 - float(gap.demonstrated_level or 0)) * 25)
                        ),
                    ),
                    {
                        "learning_path_id": str(path.id),
                        "course_count": len(cids),
                        "fit": round(fit, 1),
                        "role": role.name if role else None,
                    },
                )
            )
        program_rows = (
            await db.execute(
                select(Program, ProgramCourse.course_id)
                .join(ProgramCourse, ProgramCourse.program_id == Program.id)
                .where(
                    Program.tenant_id == user.tenant_id,
                    Program.status == "published",
                    ProgramCourse.course_id.in_(list(course_scores) or [UUID(int=0)]),
                )
            )
        ).all()
        program_courses = {}
        for program, cid in program_rows:
            program_courses.setdefault(program.id, [program, []])[1].append(cid)
        for program, cids in program_courses.values():
            fit = sum(course_scores.get(cid, 0) for cid in cids) / max(1, len(cids))
            score = max(
                0,
                min(
                    100,
                    0.45 * fit
                    + 0.30 * urgency
                    + 0.15 * freshness
                    + 0.10 * assessment_history
                    + _preference(user, "learning"),
                ),
            )
            out.append(
                (
                    uid,
                    gap,
                    role,
                    "learning",
                    "program",
                    str(program.id),
                    program.title,
                    float(score),
                    priority,
                    max(
                        30,
                        min(
                            180, 60 + int((5 - float(gap.demonstrated_level or 0)) * 25)
                        ),
                    ),
                    {
                        "program_id": str(program.id),
                        "course_count": len(cids),
                        "fit": round(fit, 1),
                        "role": role.name if role else None,
                    },
                )
            )
        session_rows = (
            await db.execute(
                select(LiveSession, LiveSession.course_id)
                .where(
                    LiveSession.tenant_id == user.tenant_id,
                    LiveSession.status == "scheduled",
                    LiveSession.starts_at >= datetime.now(timezone.utc),
                    LiveSession.course_id.in_(list(course_scores) or [UUID(int=0)]),
                )
                .limit(20)
            )
        ).all()
        for session, cid in session_rows:
            fit = course_scores.get(cid, 0)
            score = max(
                0,
                min(
                    100,
                    0.45 * fit
                    + 0.35 * urgency
                    + 0.10 * freshness
                    + 0.10 * assessment_history
                    + _preference(user, "learning"),
                ),
            )
            out.append(
                (
                    uid,
                    gap,
                    role,
                    "learning",
                    "session",
                    str(session.id),
                    session.title,
                    float(score),
                    priority,
                    max(
                        7,
                        min(
                            120,
                            (session.starts_at - datetime.now(timezone.utc)).days + 7,
                        ),
                    ),
                    {
                        "session_id": str(session.id),
                        "course_id": str(cid),
                        "fit": round(fit, 1),
                        "starts_at": session.starts_at.isoformat(),
                    },
                )
            )
        base = (
            0.45 * urgency
            + 0.20 * (100 - float(gap.evidence_confidence))
            + 0.15 * min(100, float(gap.gap_value or 0) / 4 * 100)
            + 0.10 * freshness
            + 0.10 * assessment_history
        )
        templates = [
            (
                "coaching",
                "Targeted manager coaching",
                "Use focused practice, observation and feedback against the capability gap.",
            ),
            (
                "mentoring",
                "Capability-focused mentoring",
                "Use guided experience and perspective from a knowledgeable mentor.",
            ),
            (
                "experiential",
                "Stretch assignment / field practice",
                "Build demonstrated capability through a scoped real-work assignment.",
            ),
            (
                "evidence_building",
                "Evidence-building assessment",
                "Create observable evidence and reassess the demonstrated capability level.",
            ),
        ]
        for kind, title, rationale in templates:
            prior = sum(
                1
                for g in prior_goals
                if kind.replace("_", " ") in g or title.lower() in g
            )
            score = max(
                0, min(100, base + _preference(user, kind) - min(20, prior * 10))
            )
            out.append(
                (
                    uid,
                    gap,
                    role,
                    kind,
                    "template",
                    "template:" + kind,
                    title,
                    float(score),
                    priority,
                    max(
                        30,
                        min(
                            180, 45 + int((5 - float(gap.demonstrated_level or 0)) * 25)
                        ),
                    ),
                    {
                        "gap_id": str(gap.id),
                        "evidence_confidence": gap.evidence_confidence,
                        "risk_score": float(risk.risk_score) if risk else None,
                        "role": role.name if role else None,
                        "evidence_age_days": evidence_age,
                        "assessment_history_count": len(evidence_rows),
                        "prior_intervention_count": prior,
                        "rationale_basis": rationale,
                    },
                )
            )
    out.sort(key=lambda x: x[7], reverse=True)
    return uid, out


@router.get("/recommendations")
async def recommendations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Query(None),
    intervention_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    uid, generated = await _generate(user, db, user_id)
    rows = (
        (
            await db.execute(
                select(DevelopmentRecommendation)
                .where(
                    DevelopmentRecommendation.tenant_id == user.tenant_id,
                    DevelopmentRecommendation.user_id == uid,
                    DevelopmentRecommendation.status.in_(["recommended", "accepted"]),
                )
                .order_by(DevelopmentRecommendation.score.desc())
            )
        )
        .scalars()
        .all()
    )
    existing = {
        (x.capability_gap_id, x.intervention_type, x.source_type, x.source_id): x
        for x in rows
    }
    generated_keys = set()
    for (
        uid,
        gap,
        role,
        kind,
        source_type,
        source_id,
        title,
        score,
        priority,
        days,
        meta,
    ) in generated:
        key = (gap.id, kind, source_type, source_id)
        generated_keys.add(key)
        item = existing.get(key)
        if item is None:
            reason = title + " is recommended to address the observed capability gap."
            item = DevelopmentRecommendation(
                tenant_id=user.tenant_id,
                user_id=uid,
                capability_gap_id=gap.id,
                intervention_type=kind,
                source_type=source_type,
                source_id=source_id,
                title=title,
                rationale=f"{reason} Gap severity is {gap.severity}; required level {gap.required_level}, demonstrated level {gap.demonstrated_level if gap.demonstrated_level is not None else 'not demonstrated'}. Role context: {role.name if role else 'not specified'}.",
                score=score,
                priority=priority,
                timeframe_days=days,
                recommendation_version=VERSION,
                metadata_json=meta,
            )
            db.add(item)
        else:
            item.score = score
            item.priority = priority
            item.timeframe_days = days
            item.metadata_json = meta
            item.rationale = f"{title} remains aligned to the observed capability gap. Role context: {role.name if role else 'not specified'}."
    # Reconcile persisted recommendations against the current governed gap state.
    for item in rows:
        key = (
            item.capability_gap_id,
            item.intervention_type,
            item.source_type,
            item.source_id,
        )
        if item.status == "recommended" and key not in generated_keys:
            item.status = "superseded"

    await db.commit()
    rows = (
        (
            await db.execute(
                select(DevelopmentRecommendation)
                .where(
                    DevelopmentRecommendation.tenant_id == user.tenant_id,
                    DevelopmentRecommendation.user_id == uid,
                    DevelopmentRecommendation.status.in_(["recommended", "accepted"]),
                    *([DevelopmentRecommendation.intervention_type == intervention_type] if intervention_type else []),
                )
                .order_by(DevelopmentRecommendation.score.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": str(x.id),
            "capability_gap_id": str(x.capability_gap_id),
            "intervention_type": x.intervention_type,
            "source_type": x.source_type,
            "source_id": x.source_id,
            "title": x.title,
            "rationale": x.rationale,
            "score": float(x.score),
            "priority": x.priority,
            "timeframe_days": x.timeframe_days,
            "status": x.status,
            "metadata": x.metadata_json,
            "recommendation_version": x.recommendation_version,
        }
        for x in rows[:limit]
    ]


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(DevelopmentRecommendation).where(
            DevelopmentRecommendation.id == recommendation_id,
            DevelopmentRecommendation.tenant_id == user.tenant_id,
        )
    )
    if item is None:
        raise HTTPException(404, "Development recommendation not found")
    if item.user_id != user.id and not await user_has_permission(
        user, db, "development.recommendations.manage"
    ):
        raise HTTPException(403, "You cannot accept this recommendation")
    if item.status == "accepted":
        return {"status": "accepted", "recommendation_id": str(item.id)}
    item.status = "accepted"
    if item.source_type in {"course", "learning_path", "program", "session"}:
        course_ids: Sequence[UUID] = []
        if item.source_type == "course":
            course_ids = [UUID(item.source_id)]
        elif item.source_type == "learning_path":
            course_ids = (
                (
                    await db.execute(
                        select(LearningPathItem.course_id)
                        .join(LearningPath, LearningPath.id == LearningPathItem.path_id)
                        .where(
                            LearningPathItem.path_id == UUID(item.source_id),
                            LearningPath.tenant_id == user.tenant_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
        elif item.source_type == "program":
            course_ids = (
                (
                    await db.execute(
                        select(ProgramCourse.course_id)
                        .join(Program, Program.id == ProgramCourse.program_id)
                        .where(
                            ProgramCourse.program_id == UUID(item.source_id),
                            Program.tenant_id == user.tenant_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
        else:
            session = await db.scalar(
                select(LiveSession).where(
                    LiveSession.id == UUID(item.source_id),
                    LiveSession.tenant_id == user.tenant_id,
                )
            )
            if session:
                course_ids = [session.course_id]
        courses = (
            (
                await db.execute(
                    select(Course).where(
                        Course.tenant_id == user.tenant_id,
                        Course.status == "published",
                        Course.id.in_(course_ids or [UUID(int=0)]),
                    )
                )
            )
            .scalars()
            .all()
        )
        if not courses:
            raise HTTPException(
                409, "The recommended learning resource is no longer available"
            )
        for course in courses:
            active = await db.scalar(
                select(Enrollment).where(
                    Enrollment.tenant_id == user.tenant_id,
                    Enrollment.user_id == item.user_id,
                    Enrollment.course_id == course.id,
                    Enrollment.status.notin_(["completed", "rejected"]),
                )
            )
            if not active:
                db.add(
                    Enrollment(
                        tenant_id=user.tenant_id,
                        course_id=course.id,
                        user_id=item.user_id,
                        status="enrolled",
                        source="development_recommendation",
                        due_at=datetime.now(timezone.utc)
                        + timedelta(days=item.timeframe_days),
                    )
                )
    else:
        plan = await db.scalar(
            select(DevelopmentPlan)
            .where(
                DevelopmentPlan.tenant_id == user.tenant_id,
                DevelopmentPlan.user_id == item.user_id,
                DevelopmentPlan.status == "active",
            )
            .order_by(DevelopmentPlan.created_at.desc())
        )
        goal = {
            "title": f"{item.title} — {item.intervention_type}",
            "target_date": (
                datetime.now(timezone.utc) + timedelta(days=item.timeframe_days)
            )
            .date()
            .isoformat(),
            "status": "planned",
            "notes": item.rationale,
        }
        if plan is None:
            plan = DevelopmentPlan(
                tenant_id=user.tenant_id,
                user_id=item.user_id,
                title=f"Capability development — {item.title}",
                status="active",
                goals=[goal],
            )
            db.add(plan)
        else:
            plan.goals = [*(plan.goals or []), goal]
        await db.flush()
        existing_intervention = await db.scalar(
            select(DevelopmentIntervention).where(
                DevelopmentIntervention.tenant_id == user.tenant_id,
                DevelopmentIntervention.recommendation_id == item.id,
            )
        )
        if existing_intervention is None:
            db.add(
                DevelopmentIntervention(
                    tenant_id=user.tenant_id,
                    user_id=item.user_id,
                    plan_id=plan.id,
                    recommendation_id=item.id,
                    intervention_type=item.intervention_type,
                    title=item.title,
                    objective=item.rationale,
                    status="planned",
                    due_at=datetime.now(timezone.utc) + timedelta(days=item.timeframe_days),
                    metadata_json={"recommendation_version": item.recommendation_version},
                )
            )
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="development.recommendation.accepted",
        entity_type="development_recommendation",
        entity_id=str(item.id),
        metadata={"type": item.intervention_type, "source": item.source_id},
    )
    await db.commit()
    return {
        "status": "accepted",
        "recommendation_id": str(item.id),
        "intervention_type": item.intervention_type,
        "source_type": item.source_type,
    }
