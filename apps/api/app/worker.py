from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select

from app.core.security import utcnow
from app.db.models import ComplianceAssignment, Notification, User
from app.db.session import SessionLocal
from app.services.email import send_email
from app.services.notifications import create_notification
from app.services.phase5_compliance import run_compliance_automation

logger = logging.getLogger("kalam.worker")

POLL_SECONDS = 60
DUE_SOON_HOURS = 72


async def process_compliance_notifications() -> int:
    async with SessionLocal() as db:
        now = utcnow()
        due_soon = now + timedelta(hours=DUE_SOON_HOURS)
        result = await db.execute(
            select(ComplianceAssignment, User)
            .join(User, User.id == ComplianceAssignment.user_id)
            .where(ComplianceAssignment.status.in_(["assigned", "overdue"]))
            .where(User.is_active.is_(True))
            .where(ComplianceAssignment.due_at.is_not(None))
        )
        created = 0

        for assignment, user in result.all():
            if assignment.due_at and assignment.due_at < now:
                notification_type = "compliance.overdue"
                title = "Compliance training overdue"
                body = "A mandatory learning requirement is overdue. Open your learning workspace to review the requirement."
                assignment.status = "overdue"
            elif assignment.due_at and assignment.due_at <= due_soon:
                notification_type = "compliance.due_soon"
                title = "Compliance training due soon"
                body = "A mandatory learning requirement is due within the next 72 hours."
            else:
                continue

            existing = await db.scalar(
                select(Notification.id)
                .where(
                    Notification.tenant_id == user.tenant_id,
                    Notification.user_id == user.id,
                    Notification.notification_type == notification_type,
                )
                .where(Notification.created_at >= now - timedelta(hours=24))
            )
            if existing:
                continue

            await create_notification(
                db,
                tenant_id=user.tenant_id,
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                body=body,
            )
            created += 1

        await db.commit()
        return created


async def process_notification_emails() -> int:
    async with SessionLocal() as db:
        result = await db.execute(
            select(Notification, User)
            .join(User, User.id == Notification.user_id)
            .where(Notification.email_sent_at.is_(None))
            .where(Notification.created_at >= utcnow() - timedelta(hours=24))
            .where(User.is_active.is_(True))
            .order_by(Notification.created_at.asc())
            .limit(100)
        )
        sent = 0
        for notification, user in result.all():
            try:
                send_email(
                    recipient=user.email,
                    subject=notification.title,
                    text=notification.body,
                )
            except RuntimeError:
                continue
            notification.email_sent_at = utcnow()
            sent += 1
        await db.commit()
        return sent


async def run() -> None:
    while True:
        try:
            async with SessionLocal() as db:
                await run_compliance_automation(db)
            await process_compliance_notifications()
        except Exception:
            logger.exception("Compliance worker cycle failed; retrying after backoff")
            await asyncio.sleep(5)
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
