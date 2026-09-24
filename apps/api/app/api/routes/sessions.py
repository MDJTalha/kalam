from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import AttendanceRecord, Course, LiveSession, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class SessionCreate(BaseModel):
    course_id: UUID
    instructor_id: UUID | None = None
    title: str = Field(min_length=3, max_length=240)
    starts_at: datetime
    ends_at: datetime
    location: str | None = None

class AttendanceUpdate(BaseModel):
    user_id: UUID
    status: str = Field(pattern=r"^(present|absent|late|excused)$")

@router.get("")
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LiveSession).where(LiveSession.tenant_id == user.tenant_id).order_by(LiveSession.starts_at))
    return list(result.scalars().all())

@router.post("", status_code=201)
async def create_session(
    payload: SessionCreate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == payload.course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    session = LiveSession(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(session)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="live_session.created", entity_type="live_session", entity_id=str(session.id))
    await db.commit()
    return {"id": str(session.id), "status": session.status}

@router.post("/{session_id}/attendance", status_code=201)
async def mark_attendance(
    session_id: UUID,
    payload: AttendanceUpdate,
    user: User = Depends(require_permission("courses.manage")),
    db: AsyncSession = Depends(get_db),
):
    session = await db.scalar(select(LiveSession).where(LiveSession.id == session_id, LiveSession.tenant_id == user.tenant_id))
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id))
    if session is None or learner is None:
        raise HTTPException(status_code=404, detail="Session or learner not found")
    row = await db.scalar(select(AttendanceRecord).where(AttendanceRecord.live_session_id == session.id, AttendanceRecord.user_id == learner.id))
    if row is None:
        row = AttendanceRecord(live_session_id=session.id, user_id=learner.id, status=payload.status)
        db.add(row)
    else:
        row.status = payload.status
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="attendance.marked", entity_type="attendance_record", entity_id=str(row.id), metadata={"status": payload.status})
    await db.commit()
    return {"status": row.status}
