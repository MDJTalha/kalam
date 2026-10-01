from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import (
    ComplianceAssignment,
    ComplianceRequirement,
    Course,
    CourseSkill,
    Enrollment,
    Role,
    RoleSkillRequirement,
    Skill,
    User,
    UserRole,
    UserSkill,
)
from app.db.session import get_db

router = APIRouter()


@router.get("/capability")
async def capability_intelligence(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """Tenant-scoped capability intelligence derived from persisted LMS records."""
    tenant_id = user.tenant_id
    population = int(
        await db.scalar(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
        )
        or 0
    )

    current_proficiency = func.coalesce(UserSkill.proficiency, 0)
    required_proficiency = func.max(RoleSkillRequirement.required_proficiency)
    gap_expression = required_proficiency - current_proficiency
    gap_query = (
        select(
            User.id.label("user_id"),
            User.first_name,
            User.last_name,
            func.min(Role.name).label("role"),
            Skill.id.label("skill_id"),
            Skill.name.label("skill"),
            current_proficiency.label("current"),
            required_proficiency.label("required"),
        )
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, and_(Role.id == UserRole.role_id, Role.tenant_id == tenant_id))
        .join(RoleSkillRequirement, RoleSkillRequirement.role_id == Role.id)
        .join(Skill, and_(Skill.id == RoleSkillRequirement.skill_id, Skill.tenant_id == tenant_id))
        .outerjoin(
            UserSkill,
            and_(UserSkill.user_id == User.id, UserSkill.skill_id == Skill.id),
        )
        .where(User.tenant_id == tenant_id, User.is_active.is_(True))
        .group_by(
            User.id, User.first_name, User.last_name, Skill.id, Skill.name,
            UserSkill.proficiency,
        )
        .having(gap_expression > 0)
        .order_by(gap_expression.desc(), required_proficiency.desc(), Skill.name.asc())
    )
    gap_rows = (await db.execute(gap_query)).all()
    gaps = [
        {
            "user_id": str(row.user_id),
            "user_name": f"{row.first_name} {row.last_name}".strip(),
            "role": row.role,
            "skill_id": str(row.skill_id),
            "skill": row.skill,
            "current": int(row.current or 0),
            "required": int(row.required or 0),
            "gap": int((row.required or 0) - (row.current or 0)),
        }
        for row in gap_rows
    ]

    now = datetime.now(timezone.utc)
    compliance_result = await db.execute(
        select(
            func.count(ComplianceAssignment.id),
            func.count(ComplianceAssignment.id).filter(
                ComplianceAssignment.status.not_in(["completed", "excepted"])
            ),
            func.count(ComplianceAssignment.id).filter(
                ComplianceAssignment.status.not_in(["completed", "excepted"]),
                ComplianceAssignment.due_at.is_not(None),
                ComplianceAssignment.due_at < now,
            ),
        )
        .join(
            ComplianceRequirement,
            and_(
                ComplianceRequirement.id == ComplianceAssignment.requirement_id,
                ComplianceRequirement.tenant_id == tenant_id,
            ),
        )
        .where(ComplianceAssignment.tenant_id == tenant_id)
    )
    total_compliance, open_compliance, overdue_compliance = compliance_result.one()
    total_compliance = int(total_compliance or 0)
    open_compliance = int(open_compliance or 0)
    overdue_compliance = int(overdue_compliance or 0)

    # Recommendations are built only from the highest-priority persisted gaps.
    top_gap_rows = gaps[:50]
    courses_by_skill: dict[str, list[dict[str, object]]] = {}
    if top_gap_rows:
        skill_ids = {item["skill_id"] for item in top_gap_rows}
        course_rows = (
            await db.execute(
                select(CourseSkill.skill_id, Course.id, Course.title, Course.estimated_minutes)
                .join(Course, Course.id == CourseSkill.course_id)
                .where(
                    Course.tenant_id == tenant_id,
                    CourseSkill.skill_id.in_(skill_ids),
                    Course.status == "published",
                )
            )
        ).all()
        for skill_id, course_id, title, minutes in course_rows:
            courses_by_skill.setdefault(str(skill_id), []).append(
                {"id": str(course_id), "title": title, "estimated_minutes": minutes}
            )

    completed_courses = set()
    candidate_users = {item["user_id"] for item in top_gap_rows}
    candidate_courses = {
        course["id"]
        for items in courses_by_skill.values()
        for course in items
    }
    if candidate_users and candidate_courses:
        completed_rows = await db.execute(
            select(Enrollment.user_id, Enrollment.course_id).where(
                Enrollment.tenant_id == tenant_id,
                Enrollment.user_id.in_(candidate_users),
                Enrollment.course_id.in_(candidate_courses),
                Enrollment.status == "completed",
            )
        )
        completed_courses = {(str(uid), str(cid)) for uid, cid in completed_rows.all()}

    recommendations = []
    seen = set()
    for gap in top_gap_rows:
        for course in courses_by_skill.get(gap["skill_id"], []):
            key = (gap["user_id"], course["id"])
            if key in seen or key in completed_courses:
                continue
            seen.add(key)
            recommendations.append({
                "user_id": gap["user_id"],
                "user_name": gap["user_name"],
                "role": gap["role"],
                "skill": gap["skill"],
                "skill_id": gap["skill_id"],
                "current": gap["current"],
                "required": gap["required"],
                "gap": gap["gap"],
                "course_id": course["id"],
                "course_title": course["title"],
                "estimated_minutes": course["estimated_minutes"],
                "rationale": f"Build {gap['skill']} from {gap['current']}/5 toward the role requirement of {gap['required']}/5.",
            })
            if len(recommendations) >= 12:
                break
        if len(recommendations) >= 12:
            break

    risk_score = overdue_compliance + len(gaps)
    if risk_score == 0:
        risk_band = "low"
    elif risk_score <= 5:
        risk_band = "moderate"
    elif risk_score <= 15:
        risk_band = "high"
    else:
        risk_band = "critical"

    return {
        "population": population,
        "skill_gaps": len(gaps),
        "people_with_skill_gaps": len({item["user_id"] for item in gaps}),
        "open_compliance": open_compliance,
        "overdue_compliance": overdue_compliance,
        "risk_band": risk_band,
        "evidence_model": "deterministic_persisted_records",
        "recommendation_model": "skill_gap_to_published_course_mapping",
        "recommended_actions": recommendations,
        "top_skill_gaps": gaps[:10],
    }
