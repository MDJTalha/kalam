from __future__ import annotations

# The worker adjusts sys.path before importing the API package; keep that import boundary explicit for Ruff.
# ruff: noqa: E402

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

API_ROOT = Path(__file__).resolve().parents[1] / "api"
os.chdir(API_ROOT)
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select, text
from app.core.security import utcnow
from app.core.config import settings
from app.db.models import Notification, Tenant, User, WebhookEndpoint
from app.db.session import SessionLocal
from app.services.email import send_email
from app.services.learning_reminders import run_course_due_reminders
from app.services.notifications import classify_notification
from app.services.phase5_compliance import run_compliance_automation
from app.services.saas_renewals import reconcile_renewal_tasks
from app.services.audit import audit
from app.services.webhook_delivery import deliver_webhook, retry_delay
from app.services.webhook_secrets import decrypt_webhook_secret
from report_scheduler import process_scheduled_reports


WEBHOOK_BATCH_LIMIT = 100


async def process_notification_webhooks() -> int:
    async with SessionLocal() as db:
        now = utcnow()
        result = await db.execute(
            select(Notification, WebhookEndpoint)
            .join(WebhookEndpoint, WebhookEndpoint.tenant_id == Notification.tenant_id)
            .where(WebhookEndpoint.active.is_(True))
            .where(WebhookEndpoint.secret_encrypted.is_not(None))
            .where(Notification.created_at >= now - timedelta(hours=24))
            .where(WebhookEndpoint.event_types.contains(["notification.created"]))
            .limit(WEBHOOK_BATCH_LIMIT)
        )
        delivered = 0

        for notification, endpoint in result.all():
            delivery_id = await db.scalar(
                text(
                    "SELECT id FROM webhook_deliveries "
                    "WHERE webhook_id = :webhook_id AND notification_id = :notification_id"
                ),
                {"webhook_id": endpoint.id, "notification_id": notification.id},
            )
            if delivery_id is None:
                delivery_id = uuid4()
                await db.execute(
                    text(
                        "INSERT INTO webhook_deliveries "
                        "(id, webhook_id, notification_id, event_type, status, attempts, next_attempt_at) "
                        "VALUES (:id, :webhook_id, :notification_id, :event_type, 'pending', 0, :next_attempt_at)"
                    ),
                    {
                        "id": delivery_id,
                        "webhook_id": endpoint.id,
                        "notification_id": notification.id,
                        "event_type": "notification.created",
                        "next_attempt_at": now,
                    },
                )
                await db.flush()

            state = (
                await db.execute(
                    text(
                        "SELECT status, attempts, next_attempt_at FROM webhook_deliveries WHERE id = :id"
                    ),
                    {"id": delivery_id},
                )
            ).mappings().one()

            if state["status"] == "delivered" or (
                state["next_attempt_at"] is not None and state["next_attempt_at"] > now
            ):
                continue

            payload = {
                "id": str(notification.id),
                "type": notification.notification_type,
                "title": notification.title,
                "body": notification.body,
                "user_id": str(notification.user_id),
                "created_at": notification.created_at,
            }
            attempts = int(state["attempts"]) + 1
            await db.execute(
                text("UPDATE webhook_deliveries SET attempts = :attempts, updated_at = :now WHERE id = :id"),
                {"attempts": attempts, "now": now, "id": delivery_id},
            )

            try:
                await deliver_webhook(
                    url=endpoint.url,
                    secret=decrypt_webhook_secret(
                        endpoint.secret_encrypted,
                        endpoint.secret_key_id,
                    ),
                    event_type="notification.created",
                    event_id=delivery_id,
                    tenant_id=notification.tenant_id,
                    payload=payload,
                )
            except Exception as exc:
                status = "retrying" if attempts < 8 else "failed"
                await db.execute(
                    text(
                        "UPDATE webhook_deliveries "
                        "SET status = :status, last_error = :error, next_attempt_at = :next_attempt_at, updated_at = :now "
                        "WHERE id = :id"
                    ),
                    {
                        "status": status,
                        "error": str(exc)[:2000],
                        "next_attempt_at": now + retry_delay(attempts),
                        "now": now,
                        "id": delivery_id,
                    },
                )
                continue

            await db.execute(
                text(
                    "UPDATE webhook_deliveries SET status = 'delivered', delivered_at = :now, "
                    "next_attempt_at = NULL, last_error = NULL, updated_at = :now WHERE id = :id"
                ),
                {"now": now, "id": delivery_id},
            )
            delivered += 1

        await db.commit()
        return delivered


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
            category, _priority, _href = classify_notification(notification.notification_type)
            preferences = (user.preferences or {}).get("notification_preferences", {})
            email_enabled = bool(preferences.get("email_enabled", False))
            category_enabled = bool(preferences.get(category, True))
            if category != "security" and (not email_enabled or not category_enabled):
                continue
            try:
                send_email(recipient=user.email, subject=notification.title, text=notification.body)
            except RuntimeError:
                # Leave email_sent_at unset so the next worker run retries delivery.
                continue
            notification.email_sent_at = utcnow()
            sent += 1
        await db.commit()
        return sent


async def process_saas_renewals() -> int:
    slug = settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug
    if not slug:
        return 0
    async with SessionLocal() as db:
        ops = await db.scalar(select(Tenant).where(Tenant.slug == slug, Tenant.status == "active"))
        if ops is None:
            return 0
        result = await reconcile_renewal_tasks(db, ops.id)
        changed = result["created"] + result["updated"]
        if changed:
            await audit(
                db, tenant_id=ops.id, actor_id=None,
                action="crm.renewal_tasks.generated_by_worker",
                entity_type="crm_task", entity_id="bulk", metadata=result,
            )
        await db.commit()
        return changed


async def run_once() -> dict[str, int]:
    async with SessionLocal() as db:
        reminders = await run_course_due_reminders(db)
        compliance = await run_compliance_automation(db)
    reminders.update(compliance)
    reminders["notification_emails_sent"] = await process_notification_emails()
    reminders["notification_webhooks_delivered"] = await process_notification_webhooks()
    reminders["scheduled_reports_processed"] = await process_scheduled_reports()
    reminders["crm_renewal_tasks_reconciled"] = await process_saas_renewals()
    return reminders


async def main() -> None:
    interval = max(5, int(os.getenv("LEARNING_REMINDER_INTERVAL_MINUTES", "60"))) * 60
    once = "--once" in sys.argv[1:]
    while True:
        result = await run_once()
        print(f"course reminder run: {result}", flush=True)
        if once:
            return
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
