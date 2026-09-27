from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Enrollment, Notification, User
from app.services.notifications import create_notification

REMINDER_WINDOWS = ((7, "7d"), (1, "1d"))


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def run_course_due_reminders(
    db: AsyncSession,
    *,
    tenant_id: UUID | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Create idempotent in-app reminders for active course assignments."""
    current = _as_utc(now or datetime.now(timezone.utc))
    statement = (
        select(Enrollment, Course, User)
        .join(Course, Course.id == Enrollment.course_id)
        .join(User, User.id == Enrollment.user_id)
        .where(
            Enrollment.due_at.is_not(None),
            Enrollment.status != "completed",
            User.is_active.is_(True),
            Course.tenant_id == Enrollment.tenant_id,
            User.tenant_id == Enrollment.tenant_id,
        )
    )
    if tenant_id is not None:
        statement = statement.where(Enrollment.tenant_id == tenant_id)
    result = await db.execute(statement)
    sent = 0
    processed = 0
    for enrollment, course, user in result.all():
        processed += 1
        due_at = _as_utc(enrollment.due_at)
        reminder: tuple[str, str, str] | None = None
        for days, code in REMINDER_WINDOWS:
            window_start = current + timedelta(days=days - 1)
            window_end = current + timedelta(days=days)
            if window_start < due_at <= window_end:
                reminder = (
                    code,
                    f"Course due in {days} day{'s' if days != 1 else ''}",
                    f"{course.title} is due by {due_at.date().isoformat()}.",
                )
                break
        if reminder is None and current - timedelta(days=1) <= due_at < current:
            code = f"overdue:{current.date().isoformat()}"
            reminder = (
                code,
                "Course assignment is overdue",
                f"{course.title} was due on {due_at.date().isoformat()}. Please complete it or contact your L&D administrator.",
            )
        if reminder is None:
            continue
        code, title, body = reminder
        dedupe_key = f"learning:due:{enrollment.id}:{code}"
        existing = await db.scalar(select(Notification).where(Notification.dedupe_key == dedupe_key))
        if existing:
            continue
        await create_notification(
            db,
            tenant_id=enrollment.tenant_id,
            user_id=user.id,
            notification_type="learning.due_reminder",
            title=title,
            body=body,
            dedupe_key=dedupe_key,
        )
        sent += 1
    await db.commit()
    return {"processed": processed, "created": sent}
