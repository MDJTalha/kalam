import csv
import io
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import Certificate, ComplianceAssignment, Course, Enrollment, User
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


@router.get("/export/people")
async def export_people(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(User)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.last_name, User.first_name)
    )
    rows = [
        [
            item.employee_number or "",
            item.first_name,
            item.last_name,
            item.email,
            item.job_title or "",
            "Active" if item.is_active else "Inactive",
        ]
        for item in result.scalars().all()
    ]
    return csv_response(
        "corporate-lms-people.csv",
        ["Employee Number", "First Name", "Last Name", "Email", "Job Title", "Status"],
        rows,
    )


@router.get("/export/enrollments")
async def export_enrollments(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(
        select(Enrollment, User, Course)
        .join(User, User.id == Enrollment.user_id)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.tenant_id == user.tenant_id)
        .order_by(Enrollment.created_at.desc())
    )
    rows = [
        [
            f"{person.first_name} {person.last_name}",
            person.email,
            course.title,
            enrollment.status,
            enrollment.source,
            enrollment.created_at.isoformat(),
            enrollment.completed_at.isoformat() if enrollment.completed_at else "",
        ]
        for enrollment, person, course in result.all()
    ]
    return csv_response(
        "corporate-lms-enrollments.csv",
        ["Learner", "Email", "Course", "Status", "Source", "Enrolled At", "Completed At"],
        rows,
    )
