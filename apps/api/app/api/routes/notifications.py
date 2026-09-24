from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import utcnow
from app.db.models import Notification, User
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(
            Notification.tenant_id == user.tenant_id,
            Notification.user_id == user.id,
        )
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": str(item.id),
            "type": item.notification_type,
            "title": item.title,
            "body": item.body,
            "read_at": item.read_at,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == user.tenant_id,
            Notification.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.read_at = utcnow()
    await db.commit()
    return {"status": "read"}
