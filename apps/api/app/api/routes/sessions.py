from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
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
async def list_sessions(
    limit: int = Query(default=100, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LiveSession).where(LiveSession.tenant_id == user.tenant_id)
    if not await user_has_permission(user, db, "courses.manage"):
        stmt = stmt.where(LiveSession.instructor_id == user.id)
    result = await db.execute(stmt.order_by(LiveSession.starts_at).limit(limit))
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.scalar(select(LiveSession).where(LiveSession.id == session_id, LiveSession.tenant_id == user.tenant_id))
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id))
    if session is None or learner is None:
        raise HTTPException(status_code=404, detail="Session or learner not found")
    can_manage_all = await user_has_permission(user, db, "courses.manage")
    if not can_manage_all and session.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="Facilitator scope does not include this session")
    row = await db.scalar(select(AttendanceRecord).where(AttendanceRecord.live_session_id == session.id, AttendanceRecord.user_id == learner.id))
    if row is None:
        row = AttendanceRecord(live_session_id=session.id, user_id=learner.id, status=payload.status)
        db.add(row)
    else:
        row.status = payload.status
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="attendance.marked", entity_type="attendance_record", entity_id=str(row.id), metadata={"status": payload.status})
    await db.commit()
    return {"status": row.status}

@router.get("/{session_id}/analytics")
async def session_analytics(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.scalar(
        select(LiveSession).where(
            LiveSession.id == session_id,
            LiveSession.tenant_id == user.tenant_id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    is_admin = await user_has_permission(user, db, "courses.manage")
    if not is_admin and session.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="Facilitator scope does not include this session")

    counts = await db.execute(
        select(AttendanceRecord.status, func.count(AttendanceRecord.id))
        .where(AttendanceRecord.live_session_id == session.id)
        .group_by(AttendanceRecord.status)
    )
    status_counts = {status: count for status, count in counts.all()}
    total_marked = sum(status_counts.values())
    present_like = status_counts.get("present", 0) + status_counts.get("late", 0)
    attendance_rate = round((present_like / total_marked) * 100, 2) if total_marked else 0.0

    roster = await db.execute(
        select(User.id, User.first_name, User.last_name, User.email, AttendanceRecord.status)
        .join(AttendanceRecord, AttendanceRecord.user_id == User.id)
        .where(
            User.tenant_id == user.tenant_id,
            AttendanceRecord.live_session_id == session.id,
        )
        .order_by(User.last_name, User.first_name)
    )
    return {
        "session": {
            "id": str(session.id),
            "course_id": str(session.course_id),
            "title": session.title,
            "instructor_id": str(session.instructor_id) if session.instructor_id else None,
            "starts_at": session.starts_at,
            "ends_at": session.ends_at,
            "status": session.status,
        },
        "attendance": {
            "total_marked": total_marked,
            "present": status_counts.get("present", 0),
            "late": status_counts.get("late", 0),
            "absent": status_counts.get("absent", 0),
            "excused": status_counts.get("excused", 0),
            "attendance_rate": attendance_rate,
        },
        "roster": [
            {
                "user_id": str(row.id),
                "learner": " ".join(part for part in (row.first_name, row.last_name) if part),
                "email": row.email,
                "status": row.status,
            }
            for row in roster.all()
        ],
    }
