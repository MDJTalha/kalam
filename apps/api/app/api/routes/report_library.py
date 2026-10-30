from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import (
    ComplianceAssignment,
    Course,
    Enrollment,
    ReportSchedule,
    ReportScheduleRun,
    SavedReport,
    User,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


class SavedReportPayload(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    report_type: str = Field(pattern=r"^(course[_-]performance|learning[_-]effectiveness|compliance[_-]risk|executive[_-]summary)$")
    definition: dict = Field(default_factory=dict)
    visibility: str = Field(default="private", pattern=r"^(private|tenant)$")
    enabled: bool = True


class SchedulePayload(BaseModel):
    frequency: str = Field(pattern=r"^(daily|weekly|monthly)$")
    next_run_at: datetime
    recipients: list[str] = Field(min_length=1, max_length=50)
    status: str = Field(default="active", pattern=r"^(active|paused)$")


def _schedule_guard(payload: SchedulePayload) -> None:
    if payload.next_run_at <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="next_run_at must be in the future")
    if any("@" not in item or len(item) > 320 for item in payload.recipients):
        raise HTTPException(status_code=422, detail="Invalid recipient")


def _canonical_report_type(value: str) -> str:
    return value.replace("-", "_")


async def _get_report(
    report_id: UUID,
    user: User,
    db: AsyncSession,
    manage: bool = False,
) -> SavedReport:
    item = await db.scalar(
        select(SavedReport).where(
            SavedReport.id == report_id,
            SavedReport.tenant_id == user.tenant_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Saved report not found")
    if not manage and item.visibility != "tenant" and item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Saved report is private to its owner")
    return item


@router.get("/saved")
async def list_saved_reports(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedReport)
        .where(
            SavedReport.tenant_id == user.tenant_id,
            (SavedReport.visibility == "tenant") | (SavedReport.owner_id == user.id),
        )
        .order_by(SavedReport.name)
    )
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "report_type": item.report_type,
            "definition": item.definition,
            "visibility": item.visibility,
            "enabled": item.enabled,
            "owner_id": str(item.owner_id),
        }
        for item in result.scalars().all()
    ]


@router.post("/saved")
async def create_saved_report(
    payload: SavedReportPayload,
    user: User = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(SavedReport).where(
            SavedReport.tenant_id == user.tenant_id,
            SavedReport.name == payload.name,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Saved report name already exists")
    item = SavedReport(
        tenant_id=user.tenant_id,
        owner_id=user.id,
        name=payload.name,
        report_type=_canonical_report_type(payload.report_type),
        definition=payload.definition,
        visibility=payload.visibility,
        enabled=payload.enabled,
    )
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="report.saved.created",
        entity_type="saved_report",
        entity_id=str(item.id),
        metadata={"report_type": item.report_type},
    )
    await db.commit()
    return {
        "id": str(item.id),
        "name": item.name,
        "report_type": item.report_type,
        "visibility": item.visibility,
        "enabled": item.enabled,
        "owner_id": str(item.owner_id),
    }


@router.post("/saved/{report_id}/run")
async def run_saved_report(
    report_id: UUID,
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_report(report_id, user, db)
    if not item.enabled:
        raise HTTPException(status_code=409, detail="Saved report is disabled")

    data: dict[str, Any]
    if item.report_type == "executive_summary":
        users = await db.scalar(select(func.count()).select_from(User).where(User.tenant_id == user.tenant_id)) or 0
        courses = await db.scalar(select(func.count()).select_from(Course).where(Course.tenant_id == user.tenant_id)) or 0
        enrollments = await db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.tenant_id == user.tenant_id)) or 0
        completed = await db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(Enrollment.tenant_id == user.tenant_id, Enrollment.status == "completed")
        ) or 0
        data = {
            "users": users,
            "courses": courses,
            "enrollments": enrollments,
            "completed_enrollments": completed,
            "completion_rate": round(completed / enrollments * 100, 1) if enrollments else 0,
        }
    elif item.report_type == "course_performance":
        result = await db.execute(
            select(Course.id, Course.title, Course.status, Enrollment.status)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(Course.tenant_id == user.tenant_id, Enrollment.tenant_id == user.tenant_id)
        )
        grouped: dict[str, dict[str, Any]] = {}
        definition = item.definition or {}
        search = str(definition.get("search") or "").strip().lower()
        status = str(definition.get("status") or "all")
        for course_id, title, course_status, enrollment_status in result.all():
            row = grouped.setdefault(
                str(course_id),
                {"course_id": str(course_id), "course": title, "status": course_status, "enrollments": 0, "completions": 0},
            )
            row["enrollments"] += 1
            if enrollment_status == "completed":
                row["completions"] += 1
        rows = list(grouped.values())
        rows = [row for row in rows if (status == "all" or row["status"] == status) and (not search or search in row["course"].lower())]
        for row in rows:
            row["completion_rate"] = round(row["completions"] / row["enrollments"] * 100, 1) if row["enrollments"] else 0
        data = {"rows": rows[:100], "total": len(rows)}
    elif item.report_type == "learning_effectiveness":
        result = await db.execute(
            select(Enrollment.created_at, Enrollment.completed_at, Enrollment.status)
            .where(Enrollment.tenant_id == user.tenant_id)
        )
        completed = 0
        in_progress = 0
        durations: list[float] = []
        for created_at, completed_at, status in result.all():
            if status == "completed" and completed_at is not None:
                completed += 1
                durations.append(max(0.0, (completed_at - created_at).total_seconds() / 86400))
            elif status in {"enrolled", "in_progress"}:
                in_progress += 1
        total = completed + in_progress
        data = {
            "completed": completed,
            "in_progress": in_progress,
            "completion_rate": round(completed / total * 100, 1) if total else 0,
            "average_days_to_complete": round(sum(durations) / len(durations), 1) if durations else None,
            "measured_completions": len(durations),
        }
    else:
        now = datetime.now(UTC)
        result = await db.execute(
            select(ComplianceAssignment.status, ComplianceAssignment.due_at)
            .where(ComplianceAssignment.tenant_id == user.tenant_id)
        )
        total = open_count = overdue = 0
        for status, due_at in result.all():
            total += 1
            if status not in {"completed", "verified"}:
                open_count += 1
                if due_at is not None and due_at < now:
                    overdue += 1
        band = "low" if overdue == 0 else ("high" if overdue >= max(3, total // 5) else "medium")
        data = {"total": total, "open": open_count, "overdue": overdue, "risk_band": band}

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="report.saved.executed",
        entity_type="saved_report",
        entity_id=str(item.id),
        metadata={"report_type": item.report_type},
    )
    await db.commit()
    return {"id": str(item.id), "name": item.name, "report_type": item.report_type, "generated_at": datetime.now(UTC), "data": data}


@router.patch("/saved/{report_id}")
async def update_saved_report(
    report_id: UUID,
    payload: SavedReportPayload,
    user: User = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_report(report_id, user, db, manage=True)
    item.name = payload.name
    item.report_type = _canonical_report_type(payload.report_type)
    item.definition = payload.definition
    item.visibility = payload.visibility
    item.enabled = payload.enabled
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="report.saved.updated", entity_type="saved_report", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "status": "updated"}


@router.delete("/saved/{report_id}")
async def delete_saved_report(
    report_id: UUID,
    user: User = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_report(report_id, user, db, manage=True)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="report.saved.deleted", entity_type="saved_report", entity_id=str(item.id))
    await db.delete(item)
    await db.commit()
    return {"status": "deleted"}


@router.post("/saved/{report_id}/schedule")
async def schedule_saved_report(
    report_id: UUID,
    payload: SchedulePayload,
    user: User = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    _schedule_guard(payload)
    report = await _get_report(report_id, user, db, manage=True)
    schedule = ReportSchedule(
        tenant_id=user.tenant_id,
        saved_report_id=report.id,
        frequency=payload.frequency,
        next_run_at=payload.next_run_at,
        recipients=payload.recipients,
        status=payload.status,
    )
    db.add(schedule)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="report.schedule.created", entity_type="report_schedule", entity_id=str(schedule.id), metadata={"frequency": schedule.frequency})
    await db.commit()
    return {"id": str(schedule.id), "status": schedule.status, "next_run_at": schedule.next_run_at}


@router.get("/schedules/{schedule_id}/runs")
async def list_report_schedule_runs(
    schedule_id: UUID,
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    schedule = await db.scalar(select(ReportSchedule).where(ReportSchedule.id == schedule_id, ReportSchedule.tenant_id == user.tenant_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    report = await _get_report(schedule.saved_report_id, user, db)
    result = await db.execute(
        select(ReportScheduleRun.id, ReportScheduleRun.started_at, ReportScheduleRun.completed_at, ReportScheduleRun.status, ReportScheduleRun.output_metadata, ReportScheduleRun.error)
        .where(ReportScheduleRun.schedule_id == schedule.id, ReportScheduleRun.tenant_id == user.tenant_id)
        .order_by(ReportScheduleRun.started_at.desc())
        .limit(50)
    )
    return [{"id": str(run_id), "saved_report_id": str(report.id), "started_at": started_at, "completed_at": completed_at, "status": status, "output_metadata": output_metadata, "error": error} for run_id, started_at, completed_at, status, output_metadata, error in result.all()]


@router.get("/schedules")
async def list_report_schedules(
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReportSchedule, SavedReport)
        .join(SavedReport, SavedReport.id == ReportSchedule.saved_report_id)
        .where(
            ReportSchedule.tenant_id == user.tenant_id,
            (SavedReport.visibility == "tenant") | (SavedReport.owner_id == user.id),
        )
        .order_by(ReportSchedule.next_run_at)
    )
    return [
        {
            "id": str(schedule.id),
            "saved_report_id": str(schedule.saved_report_id),
            "frequency": schedule.frequency,
            "next_run_at": schedule.next_run_at,
            "recipients": schedule.recipients,
            "status": schedule.status,
        }
        for schedule, _ in result.all()
    ]
