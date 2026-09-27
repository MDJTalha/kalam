from calendar import monthrange
from datetime import timedelta
import json
from uuid import uuid4

from sqlalchemy import text

from app.core.security import utcnow
from app.db.session import SessionLocal
from app.services.email import send_email


def _next_run(now, frequency: str):
    if frequency == "monthly":
        next_month = now.month + 1
        year = now.year + (1 if next_month == 13 else 0)
        month = 1 if next_month == 13 else next_month
        day = min(now.day, monthrange(year, month)[1])
        return now.replace(year=year, month=month, day=day)
    return now + {"daily": timedelta(days=1), "weekly": timedelta(days=7)}[frequency]


async def _generate_report(db, tenant_id, report_type: str, definition: dict) -> dict:
    if report_type == "executive_summary":
        queries = {
            "users": "SELECT count(*) FROM users WHERE tenant_id=:t",
            "courses": "SELECT count(*) FROM courses WHERE tenant_id=:t",
            "enrollments": "SELECT count(*) FROM enrollments WHERE tenant_id=:t",
            "completed_enrollments": "SELECT count(*) FROM enrollments WHERE tenant_id=:t AND status='completed'",
        }
        data = {key: int((await db.execute(text(sql), {"t": tenant_id})).scalar() or 0) for key, sql in queries.items()}
        data["completion_rate"] = round(data["completed_enrollments"] / data["enrollments"] * 100, 1) if data["enrollments"] else 0
        return data

    if report_type == "course_performance":
        search = str(definition.get("search") or "").strip().lower()
        status = str(definition.get("status") or "all")
        result = await db.execute(text("""
            SELECT c.id, c.title, c.status, count(e.id) AS enrollments,
                   count(*) FILTER (WHERE e.status='completed') AS completions
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id=c.id AND e.tenant_id=:t
            WHERE c.tenant_id=:t
              AND (:status='all' OR c.status=:status)
              AND (:search='' OR lower(c.title) LIKE '%' || :search || '%')
            GROUP BY c.id, c.title, c.status
            ORDER BY enrollments DESC, c.title ASC
            LIMIT 100
        """), {"t": tenant_id, "status": status, "search": search})
        rows = []
        for course_id, title, course_status, enrollments, completions in result.all():
            enrollments, completions = int(enrollments), int(completions)
            rows.append({"course_id": str(course_id), "course": title, "status": course_status,
                         "enrollments": enrollments, "completions": completions,
                         "completion_rate": round(completions / enrollments * 100, 1) if enrollments else 0})
        return {"rows": rows, "total": len(rows)}

    if report_type == "learning_effectiveness":
        result = await db.execute(text("""
            SELECT count(*) FILTER (WHERE status='completed' AND completed_at IS NOT NULL),
                   count(*) FILTER (WHERE status IN ('enrolled','in_progress')),
                   avg(EXTRACT(EPOCH FROM (completed_at - created_at)) / 86400.0)
            FROM enrollments
            WHERE tenant_id=:t
        """), {"t": tenant_id})
        completed, in_progress, average_days = result.one()
        completed = int(completed or 0)
        in_progress = int(in_progress or 0)
        total = completed + in_progress
        return {"completed": completed, "in_progress": in_progress,
                "completion_rate": round(completed / total * 100, 1) if total else 0,
                "average_days_to_complete": round(float(average_days), 1) if average_days is not None else None,
                "measured_completions": completed}

    now = utcnow()
    result = await db.execute(text("""
        SELECT count(*),
               count(*) FILTER (WHERE status NOT IN ('completed','verified')),
               count(*) FILTER (
                   WHERE status NOT IN ('completed','verified')
                     AND due_at IS NOT NULL
                     AND due_at < :now
               )
        FROM compliance_assignments
        WHERE tenant_id=:t
    """), {"t": tenant_id, "now": now})
    total, open_count, overdue = result.one()
    total = int(total or 0)
    open_count = int(open_count or 0)
    overdue = int(overdue or 0)
    band = "low" if overdue == 0 else ("high" if overdue >= max(3, total // 5) else "medium")
    return {"total": total, "open": open_count, "overdue": overdue, "risk_band": band}


async def process_scheduled_reports() -> int:
    now = utcnow()
    processed = 0
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT rs.id, rs.tenant_id, rs.frequency, rs.next_run_at, sr.name,
                   sr.report_type, sr.definition, rs.recipients
            FROM report_schedules rs
            JOIN saved_reports sr ON sr.id = rs.saved_report_id
            WHERE rs.status='active' AND rs.next_run_at <= :now AND sr.enabled=true
            ORDER BY rs.next_run_at
            LIMIT 50
            FOR UPDATE OF rs SKIP LOCKED
        """), {"now": now})
        for row in result.mappings().all():
            run_id = uuid4()
            await db.execute(text("""
                INSERT INTO report_schedule_runs
                (id,tenant_id,schedule_id,started_at,status,output_metadata)
                VALUES (:id,:t,:s,:n,'running','{}'::jsonb)
            """), {"id": run_id, "t": row["tenant_id"], "s": row["id"], "n": now})
            try:
                data = await _generate_report(db, row["tenant_id"], row["report_type"], row["definition"] or {})
                body = "Scheduled report completed.\\n\\n" + json.dumps(data, indent=2, default=str)
                for recipient in row["recipients"]:
                    send_email(recipient=recipient, subject=f"LMS report: {row['name']}", text=body)
                next_run = _next_run(now, row["frequency"])
                completed_at = utcnow()
                await db.execute(text("""
                    UPDATE report_schedule_runs
                    SET status='completed', completed_at=:n, output_metadata=:m, updated_at=:n
                    WHERE id=:id
                """), {"n": completed_at, "id": run_id, "m": json.dumps(data, default=str)})
                await db.execute(text("""
                    UPDATE report_schedules SET next_run_at=:next, updated_at=:n WHERE id=:id
                """), {"next": next_run, "n": completed_at, "id": row["id"]})
                processed += 1
            except Exception as exc:
                failed_at = utcnow()
                await db.execute(text("""
                    UPDATE report_schedule_runs
                    SET status='failed', completed_at=:n, error=:e, updated_at=:n
                    WHERE id=:id
                """), {"n": failed_at, "e": str(exc)[:4000], "id": run_id})
                await db.execute(text("""
                    UPDATE report_schedules SET next_run_at=:next, updated_at=:n WHERE id=:id
                """), {"next": _next_run(now, row["frequency"]), "n": failed_at, "id": row["id"]})
        await db.commit()
    return processed
