from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification

async def create_notification(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    dedupe_key: str | None = None,
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
    item = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        dedupe_key=dedupe_key,
    )
    db.add(item)
    await db.flush()
    return item
