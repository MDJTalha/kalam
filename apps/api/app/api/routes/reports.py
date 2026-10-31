import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import require_permission
from app.db.models import (
    Assessment,
    AssessmentAttempt,
    Certificate,
    ComplianceAssignment,
    ComplianceRequirement,
    Course,
    Enrollment,
    OrgUnit,
    RoleSkillRequirement,
    Skill,
    User,
    UserSkill,
)
from app.db.session import get_db

router = APIRouter()


def csv_response(filename: str, headers: list[str], rows: list[list[Any]]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary")
async def summary(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    def base(model):
        return select(func.count()).select_from(model).where(getattr(model, "tenant_id") == user.tenant_id)

    users = await db.scalar(base(User))
    courses = await db.scalar(base(Course))
    enrollments = await db.scalar(base(Enrollment))
    completed = await db.scalar(
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.tenant_id == user.tenant_id, Enrollment.status == "completed")
    )
    certificates = await db.scalar(base(Certificate))
    compliance = await db.scalar(base(ComplianceAssignment))
    return {
        "users": users or 0,
        "courses": courses or 0,
        "enrollments": enrollments or 0,
        "completed_enrollments": completed or 0,
        "certificates": certificates or 0,
        "compliance_assignments": compliance or 0,
    }


@router.get("/learning-trends")
async def learning_trends(
    days: int = 30,
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    days = max(7, min(days, 365))
    start = datetime.now(timezone.utc) - timedelta(days=days - 1)
    result = await db.execute(
        select(Enrollment.created_at, Enrollment.completed_at)
        .where(Enrollment.tenant_id == user.tenant_id, Enrollment.created_at >= start)
    )
    enrolled: defaultdict[str, int] = defaultdict(int)
    completed: defaultdict[str, int] = defaultdict(int)
    for created_at, completed_at in result.all():
        enrolled[created_at.date().isoformat()] += 1
        if completed_at is not None:
            completed[completed_at.date().isoformat()] += 1
    points = []
    for index in range(days):
        day = (start + timedelta(days=index)).date().isoformat()
        points.append({"date": day, "enrollments": enrolled[day], "completions": completed[day]})
    return {"days": days, "points": points}


@router.get("/course-performance")
async def course_performance(
    search: str | None = Query(default=None, max_length=240),
    status: str | None = Query(default=None, max_length=30),
    sort: str | None = Query(default=None, pattern="^(course|enrollments|completions|completion_rate)$"),
    direction: str | None = Query(default=None, pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    sort_by: str | None = Query(default=None, pattern="^(course|enrollments|completions|completion_rate)$"),
    sort_dir: str | None = Query(default=None, pattern="^(asc|desc)$"),
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    """Tenant-scoped course performance with database-side aggregation and pagination."""
    sort = sort_by or sort or "enrollments"
    direction = sort_dir or direction or "desc"
    if page is not None:
        limit = page_size or limit
        offset = (page - 1) * limit
    elif page_size is not None:
        limit = page_size
    completion_count = func.count(Enrollment.id).filter(Enrollment.status == "completed")
    enrollment_count = func.count(Enrollment.id)
    filters = [Course.tenant_id == user.tenant_id]
    if status:
        filters.append(Course.status == status)
    if search and search.strip():
        filters.append(Course.title.ilike(f"%{search.strip()}%"))

    query = (
        select(
            Course.id.label("course_id"),
            Course.title.label("course"),
            Course.status.label("status"),
            enrollment_count.label("enrollments"),
            completion_count.label("completions"),
        )
        .outerjoin(
            Enrollment,
            (Enrollment.course_id == Course.id) & (Enrollment.tenant_id == user.tenant_id),
        )
        .where(*filters)
        .group_by(Course.id, Course.title, Course.status)
    )
    count_query = select(func.count()).select_from(query.subquery())
    total = int(await db.scalar(count_query) or 0)

    rate_expression = (completion_count * 100.0 / func.nullif(enrollment_count, 0))
    sort_expression = {
        "course": Course.title,
        "enrollments": enrollment_count,
        "completions": completion_count,
        "completion_rate": rate_expression,
    }[sort]
    query = query.order_by(sort_expression.desc() if direction == "desc" else sort_expression.asc())
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)

    rows = []
    for course_id, title, course_status, enrollments, completions in result.all():
        enrollments, completions = int(enrollments or 0), int(completions or 0)
        rows.append({
            "course_id": str(course_id),
            "course": title,
            "status": course_status,
            "enrollments": enrollments,
            "completions": completions,
            "completion_rate": round(completions / enrollments * 100, 1) if enrollments else 0,
        })
    pages = (total + limit - 1) // limit if total else 0
    return {
        "courses": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagination": {
            "page": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "pages": pages,
        },
        "filters": {
            "status": status,
            "search": search,
            "sort_by": sort,
            "sort_dir": direction,
        },
    }


@router.get("/learning-effectiveness")
async def learning_effectiveness(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    completed_result = await db.execute(
        select(
            func.count(Enrollment.id),
            func.avg(func.extract("epoch", Enrollment.completed_at - Enrollment.created_at) / 86400.0),
        )
        .where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.status == "completed",
            Enrollment.completed_at.is_not(None),
        )
    )
    completed, average_days = completed_result.one()
    in_progress = await db.scalar(
        select(func.count(Enrollment.id))
        .where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.status.in_(["enrolled", "in_progress"]),
        )
    ) or 0
    completed = int(completed or 0)
    in_progress = int(in_progress or 0)
    total = completed + in_progress
    return {
        "completed": completed,
        "in_progress": in_progress,
        "completion_rate": round(completed / total * 100, 1) if total else 0,
        "average_days_to_complete": round(float(average_days), 1) if average_days is not None else None,
        "measured_completions": completed,
        "evidence_model": "persisted_enrollment_timestamps",
    }


@router.get("/manager-performance")
async def manager_performance(
    search: str | None = Query(default=None, max_length=240),
    sort: str = Query(default="team_members", pattern="^(manager|team_members|enrollments|completions|completion_rate)$"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    manager = aliased(User)
    team_members = func.count(func.distinct(User.id))
    enrollments = func.count(Enrollment.id)
    completions = func.count(Enrollment.id).filter(Enrollment.status == "completed")
    rate = completions * 100.0 / func.nullif(enrollments, 0)
    filters = [
        manager.tenant_id == user.tenant_id,
        User.tenant_id == user.tenant_id,
        Enrollment.tenant_id == user.tenant_id,
    ]
    if search and search.strip():
        term = search.strip()
        filters.append((manager.first_name.ilike(f"%{term}%")) | (manager.last_name.ilike(f"%{term}%")))

    query = (
        select(
            manager.id.label("manager_id"),
            manager.first_name,
            manager.last_name,
            team_members.label("team_members"),
            enrollments.label("enrollments"),
            completions.label("completions"),
        )
        .join(User, User.manager_id == manager.id)
        .join(Enrollment, Enrollment.user_id == User.id)
        .where(*filters)
        .group_by(manager.id, manager.first_name, manager.last_name)
    )
    total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
    sort_expression = {
        "manager": manager.last_name,
        "team_members": team_members,
        "enrollments": enrollments,
        "completions": completions,
        "completion_rate": rate,
    }[sort]
    query = query.order_by(sort_expression.desc() if direction == "desc" else sort_expression.asc(), manager.id.asc())
    rows = []
    for manager_id, first_name, last_name, member_count, enrollment_count, completion_count in (
        await db.execute(query.offset(offset).limit(limit))
    ).all():
        enrollment_count = int(enrollment_count or 0)
        completion_count = int(completion_count or 0)
        rows.append({
            "manager_id": str(manager_id),
            "manager": f"{first_name} {last_name}".strip(),
            "team_members": int(member_count or 0),
            "enrollments": enrollment_count,
            "completions": completion_count,
            "completion_rate": round(completion_count / enrollment_count * 100, 1) if enrollment_count else 0,
        })
    return {
        "managers": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagination": {"page": (offset // limit) + 1, "page_size": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0},
    }


@router.get("/export/course-performance")
async def export_course_performance(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(Course.id, Course.title, Course.status, Enrollment.status)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Course.tenant_id == user.tenant_id, Enrollment.tenant_id == user.tenant_id)
    )
    grouped: dict[str, dict[str, Any]] = {}
    for course_id, title, course_status, enrollment_status in result.all():
        item = grouped.setdefault(str(course_id), {"course": title, "status": course_status, "enrollments": 0, "completions": 0})
        item["enrollments"] += 1
        if enrollment_status == "completed":
            item["completions"] += 1
    rows = []
    for item in grouped.values():
        rate = round(item["completions"] / item["enrollments"] * 100, 1) if item["enrollments"] else 0
        rows.append([item["course"], item["status"], item["enrollments"], item["completions"], rate])
    rows.sort(key=lambda row: (-row[2], row[0]))
    return csv_response("corporate-lms-course-performance.csv", ["Course", "Status", "Enrollments", "Completions", "Completion Rate %"], rows)


@router.get("/export/people")
async def export_people(
    user: User = Depends(require_permission("reports.export.people")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(User)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.last_name.asc(), User.first_name.asc(), User.email.asc())
    )
    rows = [
        [
            str(item.id),
            item.email,
            item.first_name,
            item.last_name,
            item.employee_number or "",
            item.job_title or "",
            "active" if item.is_active else "inactive",
            item.last_login_at.isoformat() if item.last_login_at else "",
        ]
        for item in result.scalars().all()
    ]
    return csv_response(
        "kognivon-people.csv",
        ["User ID", "Email", "First Name", "Last Name", "Employee Number", "Job Title", "Status", "Last Sign-in"],
        rows,
    )


@router.get("/export/enrollments")
async def export_enrollments(
    user: User = Depends(require_permission("reports.export.learning")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(Enrollment, Course, User)
        .join(Course, Course.id == Enrollment.course_id)
        .join(User, User.id == Enrollment.user_id)
        .where(
            Enrollment.tenant_id == user.tenant_id,
            Course.tenant_id == user.tenant_id,
            User.tenant_id == user.tenant_id,
        )
        .order_by(Enrollment.created_at.desc(), User.email.asc())
    )
    rows = [
        [
            str(item.id),
            learner.email,
            f"{learner.first_name} {learner.last_name}".strip(),
            course.title,
            item.status,
            item.created_at.isoformat() if item.created_at else "",
            item.due_at.isoformat() if item.due_at else "",
            item.completed_at.isoformat() if item.completed_at else "",
        ]
        for item, course, learner in result.all()
    ]
    return csv_response(
        "kognivon-enrollments.csv",
        ["Enrollment ID", "Learner Email", "Learner", "Course", "Status", "Enrolled At", "Due At", "Completed At"],
        rows,
    )


@router.get("/export/compliance")
async def export_compliance(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .where(ComplianceAssignment.tenant_id == user.tenant_id)
        .order_by(ComplianceAssignment.due_at.asc().nulls_last())
    )
    rows = [
        [
            item.user_id,
            requirement.name,
            item.status,
            item.due_at.isoformat() if item.due_at else "",
            item.course_id or "",
        ]
        for item, requirement in result.all()
    ]
    return csv_response("corporate-lms-compliance.csv", ["Learner ID", "Requirement", "Status", "Due At", "Course ID"], rows)



@router.get("/assessment-performance")
async def assessment_performance(
    search: str | None = Query(default=None, max_length=240),
    sort: str = Query(default="submitted_attempts", pattern="^(assessment|attempts|submitted_attempts|average_score|pass_rate)$"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    attempts = func.count(AssessmentAttempt.id)
    submitted = func.count(AssessmentAttempt.id).filter(AssessmentAttempt.score.is_not(None))
    passed = func.count(AssessmentAttempt.id).filter(AssessmentAttempt.score.is_not(None), AssessmentAttempt.passed.is_(True))
    average = func.avg(AssessmentAttempt.score)
    rate = passed * 100.0 / func.nullif(submitted, 0)
    filters = [
        Assessment.tenant_id == user.tenant_id,
        AssessmentAttempt.user_id.is_not(None),
    ]
    if search and search.strip():
        filters.append(Assessment.title.ilike(f"%{search.strip()}%"))
    query = (
        select(
            Assessment.id.label("assessment_id"),
            Assessment.title,
            Assessment.passing_score,
            attempts.label("attempts"),
            submitted.label("submitted_attempts"),
            passed.label("passed_attempts"),
            (submitted - passed).label("failed_attempts"),
            average.label("average_score"),
        )
        .join(AssessmentAttempt, AssessmentAttempt.assessment_id == Assessment.id)
        .where(*filters)
        .group_by(Assessment.id, Assessment.title, Assessment.passing_score)
    )
    total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
    sort_expression = {
        "assessment": Assessment.title,
        "attempts": attempts,
        "submitted_attempts": submitted,
        "average_score": average,
        "pass_rate": rate,
    }[sort]
    query = query.order_by(sort_expression.desc() if direction == "desc" else sort_expression.asc(), Assessment.title.asc())
    result = await db.execute(query.offset(offset).limit(limit))
    rows = []
    for assessment_id, title, passing_score, attempt_count, submitted_count, passed_count, failed_count, average_score in result.all():
        submitted_count = int(submitted_count or 0)
        passed_count = int(passed_count or 0)
        rows.append({
            "assessment_id": str(assessment_id),
            "assessment": title,
            "passing_score": passing_score,
            "attempts": int(attempt_count or 0),
            "submitted_attempts": submitted_count,
            "passed_attempts": passed_count,
            "failed_attempts": int(failed_count or 0),
            "average_score": round(float(average_score), 1) if average_score is not None else 0,
            "pass_rate": round(passed_count / submitted_count * 100, 1) if submitted_count else 0,
        })
    return {
        "assessments": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagination": {"page": (offset // limit) + 1, "page_size": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0},
    }


@router.get("/engagement")
async def engagement(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(Enrollment.id),
            func.count(func.distinct(Enrollment.user_id)),
            func.count(func.distinct(Enrollment.user_id)).filter(
                Enrollment.status.in_(["enrolled", "in_progress"])
            ),
            func.count(func.distinct(Enrollment.user_id)).filter(
                Enrollment.status == "completed"
            ),
        )
        .where(Enrollment.tenant_id == user.tenant_id)
    )
    enrollment_records, enrolled_learners, active_learners, completed_learners = result.one()
    enrolled_learners = int(enrolled_learners or 0)
    active_learners = int(active_learners or 0)
    completed_learners = int(completed_learners or 0)
    return {
        "enrolled_learners": enrolled_learners,
        "active_learners": active_learners,
        "learners_with_completion": completed_learners,
        "learner_activation_rate": round(active_learners / enrolled_learners * 100, 1) if enrolled_learners else 0,
        "learner_completion_reach": round(completed_learners / enrolled_learners * 100, 1) if enrolled_learners else 0,
        "enrollment_records": int(enrollment_records or 0),
        "evidence_model": "persisted_enrollment_status",
    }


@router.get("/organization-performance")
async def organization_performance(
    search: str | None = Query(default=None, max_length=240),
    sort: str = Query(default="people", pattern="^(org_unit|people|enrollments|completions|completion_rate)$"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    people = func.count(func.distinct(User.id))
    enrollments = func.count(Enrollment.id)
    completions = func.count(Enrollment.id).filter(Enrollment.status == "completed")
    rate = completions * 100.0 / func.nullif(enrollments, 0)
    filters = [OrgUnit.tenant_id == user.tenant_id, User.tenant_id == user.tenant_id]
    if search and search.strip():
        filters.append(OrgUnit.name.ilike(f"%{search.strip()}%"))
    query = (
        select(
            OrgUnit.id.label("org_unit_id"),
            OrgUnit.name,
            people.label("people"),
            enrollments.label("enrollments"),
            completions.label("completions"),
        )
        .join(User, User.org_unit_id == OrgUnit.id)
        .outerjoin(
            Enrollment,
            (Enrollment.user_id == User.id) & (Enrollment.tenant_id == user.tenant_id),
        )
        .where(*filters)
        .group_by(OrgUnit.id, OrgUnit.name)
    )
    total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
    sort_expression = {
        "org_unit": OrgUnit.name,
        "people": people,
        "enrollments": enrollments,
        "completions": completions,
        "completion_rate": rate,
    }[sort]
    query = query.order_by(sort_expression.desc() if direction == "desc" else sort_expression.asc(), OrgUnit.name.asc())
    result = await db.execute(query.offset(offset).limit(limit))
    rows = []
    for org_id, name, people_count, enrollment_count, completion_count in result.all():
        enrollment_count = int(enrollment_count or 0)
        completion_count = int(completion_count or 0)
        rows.append({
            "org_unit_id": str(org_id),
            "org_unit": name,
            "people": int(people_count or 0),
            "enrollments": enrollment_count,
            "completions": completion_count,
            "completion_rate": round(completion_count / enrollment_count * 100, 1) if enrollment_count else 0,
        })
    return {
        "organization_units": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagination": {"page": (offset // limit) + 1, "page_size": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0},
    }


@router.get("/skill-performance")
async def skill_performance(
    search: str | None = Query(default=None, max_length=240),
    sort: str = Query(default="gap_to_requirement", pattern="^(skill|required_proficiency|average_proficiency|evidence_count|coverage_rate|requirement_met_rate|gap_to_requirement)$"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    required_query = (
        select(
            RoleSkillRequirement.skill_id.label("skill_id"),
            func.avg(RoleSkillRequirement.required_proficiency).label("required_proficiency"),
        )
        .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
        .where(Skill.tenant_id == user.tenant_id)
        .group_by(RoleSkillRequirement.skill_id)
        .subquery()
    )
    evidence_count = func.count(UserSkill.id)
    average_proficiency = func.avg(UserSkill.proficiency)
    met_count = func.count(UserSkill.id).filter(
        UserSkill.proficiency >= required_query.c.required_proficiency
    )
    coverage_rate = evidence_count * 100.0 / func.nullif(
        select(func.count(User.id)).where(User.tenant_id == user.tenant_id, User.is_active.is_(True)).scalar_subquery(),
        0,
    )
    requirement_met_rate = met_count * 100.0 / func.nullif(evidence_count, 0)
    gap = func.greatest(
        0.0,
        required_query.c.required_proficiency - func.coalesce(average_proficiency, 0.0),
    )
    filters = [Skill.tenant_id == user.tenant_id]
    if search and search.strip():
        filters.append(Skill.name.ilike(f"%{search.strip()}%"))
    query = (
        select(
            Skill.id.label("skill_id"),
            Skill.name,
            required_query.c.required_proficiency,
            average_proficiency,
            evidence_count.label("evidence_count"),
            coverage_rate.label("coverage_rate"),
            requirement_met_rate.label("requirement_met_rate"),
            gap.label("gap_to_requirement"),
        )
        .join(required_query, required_query.c.skill_id == Skill.id)
        .outerjoin(UserSkill, UserSkill.skill_id == Skill.id)
        .where(*filters)
        .group_by(Skill.id, Skill.name, required_query.c.required_proficiency)
    )
    total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
    sort_expression = {
        "skill": Skill.name,
        "required_proficiency": required_query.c.required_proficiency,
        "average_proficiency": average_proficiency,
        "evidence_count": evidence_count,
        "coverage_rate": coverage_rate,
        "requirement_met_rate": requirement_met_rate,
        "gap_to_requirement": gap,
    }[sort]
    query = query.order_by(sort_expression.desc() if direction == "desc" else sort_expression.asc(), Skill.name.asc())
    result = await db.execute(query.offset(offset).limit(limit))
    rows = []
    for skill_id, name, required_average, average, evidence, coverage, met_rate, gap_value in result.all():
        rows.append({
            "skill_id": str(skill_id),
            "skill": name,
            "required_proficiency": round(float(required_average or 0), 2),
            "average_proficiency": round(float(average or 0), 2),
            "evidence_count": int(evidence or 0),
            "coverage_rate": round(float(coverage or 0), 1),
            "requirement_met_rate": round(float(met_rate or 0), 1),
            "gap_to_requirement": round(float(gap_value or 0), 2),
        })
    return {
        "skills": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagination": {"page": (offset // limit) + 1, "page_size": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0},
    }


@router.get("/compliance-risk")
async def compliance_risk(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(
            func.count(ComplianceAssignment.id),
            func.count(ComplianceAssignment.id).filter(
                ComplianceAssignment.status.not_in(["completed", "verified"])
            ),
            func.count(ComplianceAssignment.id).filter(
                ComplianceAssignment.status.not_in(["completed", "verified"]),
                ComplianceAssignment.due_at.is_not(None),
                ComplianceAssignment.due_at < now,
            ),
        )
        .where(ComplianceAssignment.tenant_id == user.tenant_id)
    )
    total, open_count, overdue = result.one()
    total = int(total or 0)
    open_count = int(open_count or 0)
    overdue = int(overdue or 0)
    risk_band = "low" if overdue == 0 else ("high" if overdue >= max(3, total // 5) else "medium")
    return {"total": total, "open": open_count, "overdue": overdue, "risk_band": risk_band}
