from uuid import UUID

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
) -> Notification:
    item = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
    )
    db.add(item)
    await db.flush()
    return item
