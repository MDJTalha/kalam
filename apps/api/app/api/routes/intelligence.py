

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
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
    """Tenant-scoped capability intelligence: skill gaps + compliance exposure.

    This is deliberately deterministic: every metric is derived from persisted LMS
    records and is suitable for executive dashboards and audit evidence.
    """
    users_result = await db.execute(
        select(User).where(
            User.tenant_id == user.tenant_id,
            User.is_active.is_(True),
        )
    )
    users = list(users_result.scalars().all())

    role_by_user: dict[str, list[Role]] = {}
    if users:
        role_result = await db.execute(
            select(UserRole, Role)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id.in_([item.id for item in users]),
                Role.tenant_id == user.tenant_id,
            )
        )
        role_rows = role_result.all()
    else:
        role_rows = []
    for user_role, role in role_rows:
        role_by_user.setdefault(str(user_role.user_id), []).append(role)

    requirements_result = await db.execute(
        select(RoleSkillRequirement, Skill)
        .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
        .where(Skill.tenant_id == user.tenant_id)
    )
    requirements_by_role: dict[str, list[tuple[RoleSkillRequirement, Skill]]] = {}
    for requirement, skill in requirements_result.all():
        requirements_by_role.setdefault(str(requirement.role_id), []).append((requirement, skill))

    skills_result = await db.execute(
        select(UserSkill, Skill)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(Skill.tenant_id == user.tenant_id)
    )
    skills_by_user: dict[str, dict[str, int]] = {}
    for user_skill, skill in skills_result.all():
        skills_by_user.setdefault(str(user_skill.user_id), {})[str(skill.id)] = user_skill.proficiency

    gaps: list[dict] = []
    for person in users:
        person_roles = role_by_user.get(str(person.id), [])
        for role in person_roles:
            for requirement, skill in requirements_by_role.get(str(role.id), []):
                current = skills_by_user.get(str(person.id), {}).get(str(skill.id), 0)
                if current < requirement.required_proficiency:
                    gaps.append(
                        {
                            "user_id": str(person.id),
                            "user_name": f"{person.first_name} {person.last_name}".strip(),
                            "role": role.name,
                            "skill_id": str(skill.id),
                            "skill": skill.name,
                            "current": current,
                            "required": requirement.required_proficiency,
                            "gap": requirement.required_proficiency - current,
                        }
                    )

    assignments_result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .where(
            ComplianceAssignment.tenant_id == user.tenant_id,
            ComplianceRequirement.tenant_id == user.tenant_id,
        )
    )
    assignments = list(assignments_result.all())
    overdue = [
        item for item, _ in assignments
        if item.status not in {"completed", "excepted"}
        and item.due_at is not None
        and item.due_at < datetime.now(timezone.utc)
    ]
    open_assignments = [
        item for item, _ in assignments
        if item.status not in {"completed", "excepted"}
    ]

    courses_by_skill: dict[str, list[Course]] = {}
    if gaps:
        course_map_result = await db.execute(
            select(CourseSkill, Course)
            .join(Course, Course.id == CourseSkill.course_id)
            .where(
                Course.tenant_id == user.tenant_id,
                CourseSkill.skill_id.in_([item["skill_id"] for item in gaps]),
                Course.status == "published",
            )
        )
        course_map_rows = course_map_result.all()
    else:
        course_map_rows = []
    for mapping, course in course_map_rows:
        courses_by_skill.setdefault(str(mapping.skill_id), []).append(course)

    enrollment_result = await db.execute(
        select(Enrollment).where(Enrollment.tenant_id == user.tenant_id)
    )
    completed_courses = {
        (str(item.user_id), str(item.course_id))
        for item in enrollment_result.scalars().all()
        if item.status == "completed"
    }

    recommendations: list[dict] = []
    seen_recommendations: set[tuple[str, str]] = set()
    for gap in sorted(gaps, key=lambda item: (item["gap"], item["required"]), reverse=True):
        for course in courses_by_skill.get(gap["skill_id"], []):
            key = (gap["user_id"], str(course.id))
            if key in seen_recommendations or key in completed_courses:
                continue
            seen_recommendations.add(key)
            recommendations.append(
                {
                    "user_id": gap["user_id"],
                    "user_name": gap["user_name"],
                    "role": gap["role"],
                    "skill": gap["skill"],
                    "skill_id": gap["skill_id"],
                    "current": gap["current"],
                    "required": gap["required"],
                    "gap": gap["gap"],
                    "course_id": str(course.id),
                    "course_title": course.title,
                    "estimated_minutes": course.estimated_minutes,
                    "rationale": f"Build {gap['skill']} from {gap['current']}/5 toward the role requirement of {gap['required']}/5.",
                }
            )

    high_risk = len(overdue) + len(gaps)
    if high_risk == 0:
        risk_band = "low"
    elif high_risk <= 5:
        risk_band = "moderate"
    elif high_risk <= 15:
        risk_band = "high"
    else:
        risk_band = "critical"

    return {
        "population": len(users),
        "skill_gaps": len(gaps),
        "people_with_skill_gaps": len({item["user_id"] for item in gaps}),
        "open_compliance": len(open_assignments),
        "overdue_compliance": len(overdue),
        "risk_band": risk_band,
        "evidence_model": "deterministic_persisted_records",
        "recommendation_model": "skill_gap_to_published_course_mapping",
        "recommended_actions": recommendations[:12],
        "top_skill_gaps": sorted(
            gaps,
            key=lambda item: (item["gap"], item["required"]),
            reverse=True,
        )[:10],
    }
