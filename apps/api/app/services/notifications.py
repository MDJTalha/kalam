from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, User
from app.services.email import send_email


def classify_notification(notification_type: str) -> tuple[str, str, str | None]:
    value = notification_type.lower()
    if value.startswith("support_case"):
        return "support", "high" if "created" in value or "status" in value else "normal", "/dashboard/help"
    if "compliance" in value or "readiness" in value:
        return "compliance", "high", "/dashboard/compliance"
    if "assessment" in value:
        return "assessment", "normal", "/dashboard/assessments"
    if "certificate" in value or "credential" in value:
        return "credentials", "normal", "/dashboard/certificates"
    if "security" in value or "auth" in value or "session" in value:
        return "security", "critical", "/dashboard/settings"
    if "approval" in value:
        return "approvals", "high", "/dashboard/ld-operations"
    if "learning" in value or "course" in value or "enrollment" in value:
        return "learning", "normal", "/dashboard/catalog"
    return "system", "normal", None


async def create_notification(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    dedupe_key: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    action_href: str | None = None,
) -> Notification:
    if dedupe_key:
        existing = await db.scalar(
            select(Notification).where(
                Notification.dedupe_key == dedupe_key,
                Notification.tenant_id == tenant_id,
            )
        )
        if existing:
            return existing

    inferred_category, inferred_priority, inferred_href = classify_notification(notification_type)
    resolved_category = category or inferred_category
    item = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        notification_type=notification_type,
        category=resolved_category,
        priority=priority or inferred_priority,
        action_href=action_href or inferred_href,
        title=title,
        body=body,
        dedupe_key=dedupe_key,
    )
    db.add(item)
    await db.flush()

    user = await db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    notification_preferences = ((user.preferences or {}).get("notification_preferences", {}) if user else {})
    email_enabled = bool(notification_preferences.get("email_enabled", False))
    category_enabled = bool(notification_preferences.get(resolved_category, True))
    security_required = resolved_category == "security"
    if user and (security_required or (email_enabled and category_enabled)):
        try:
            send_email(
                recipient=user.email,
                subject=title,
                text=f"{body}\n\nSign in to Kalam to review this notification.",
            )
            item.email_sent_at = datetime.now(timezone.utc)
        except RuntimeError:
            pass

    return item
