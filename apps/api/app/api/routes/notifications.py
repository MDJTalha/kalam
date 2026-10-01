from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import utcnow
from app.db.models import Notification, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import classify_notification

router = APIRouter()

DEFAULT_NOTIFICATION_PREFERENCES = {
    "email_enabled": False,
    "learning": True,
    "compliance": True,
    "assessment": True,
    "credentials": True,
    "support": True,
    "approvals": True,
    "system": True,
    "security": True,
}

class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool = False
    learning: bool = True
    compliance: bool = True
    assessment: bool = True
    credentials: bool = True
    support: bool = True
    approvals: bool = True
    system: bool = True


def _serialize(item: Notification) -> dict:
    inferred_category, inferred_priority, inferred_href = classify_notification(item.notification_type)
    resolved_category = inferred_category if item.category == "system" and inferred_category != "system" else item.category
    resolved_priority = inferred_priority if item.priority == "normal" and inferred_priority != "normal" else item.priority
    return {
        "id": str(item.id),
        "type": item.notification_type,
        "category": resolved_category or inferred_category,
        "priority": resolved_priority or inferred_priority,
        "action_href": item.action_href or inferred_href,
        "title": item.title,
        "body": item.body,
        "email_sent_at": item.email_sent_at,
        "read_at": item.read_at,
        "created_at": item.created_at,
    }


@router.get("")
async def list_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification)
        .where(Notification.tenant_id == user.tenant_id, Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(200)
    )
    return [_serialize(item) for item in result.scalars().all()]


@router.get("/preferences")
async def get_notification_preferences(user: User = Depends(get_current_user)):
    stored = (user.preferences or {}).get("notification_preferences", {})
    return {**DEFAULT_NOTIFICATION_PREFERENCES, **stored, "security": True}


@router.patch("/preferences")
async def update_notification_preferences(payload: NotificationPreferencesUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current = dict(user.preferences or {})
    current["notification_preferences"] = {**payload.model_dump(), "security": True}
    user.preferences = current
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="user.notification_preferences.updated", entity_type="user", entity_id=str(user.id), metadata=current["notification_preferences"])
    await db.commit()
    return current["notification_preferences"]


@router.post("/read-all")
async def mark_all_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.tenant_id == user.tenant_id, Notification.user_id == user.id, Notification.read_at.is_(None)))
    items = result.scalars().all()
    now = utcnow()
    for item in items:
        item.read_at = now
    await db.commit()
    return {"status": "read", "count": len(items)}


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(Notification).where(Notification.id == notification_id, Notification.tenant_id == user.tenant_id, Notification.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.read_at = utcnow()
    await db.commit()
    return {"status": "read"}
