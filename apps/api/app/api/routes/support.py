from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_platform_developer, require_permission
from app.core.config import settings
from app.core.security import session_token_hash
from app.db.models import DeveloperSupportSession, Permission, RolePermission, SupportCase, SupportCaseMessage, Tenant, User, UserRole
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()

class DeveloperSupportStart(BaseModel):
    tenant_id: UUID
    reason: str = Field(min_length=10, max_length=500)
    duration_minutes: int = Field(default=60, ge=15, le=480)


async def _is_platform_developer(user: User, db: AsyncSession) -> bool:
    return await is_platform_developer(user, db)


@router.get("/developer/tenants")
async def developer_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Platform Developer access required")
    rows = (await db.execute(
        select(Tenant).where(Tenant.slug != settings.saas_ops_tenant_slug).order_by(Tenant.name)
    )).scalars().all()
    return [{"id": str(t.id), "name": t.name, "slug": t.slug, "status": t.status} for t in rows]


@router.post("/developer/support/start")
async def developer_support_start(
    payload: DeveloperSupportStart,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Platform Developer access required")
    tenant = await db.get(Tenant, payload.tenant_id)
    if tenant is None or tenant.status != "active" or tenant.slug == settings.saas_ops_tenant_slug:
        raise HTTPException(status_code=422, detail="Choose an active customer tenant")
    raw = token_urlsafe(48)
    session = DeveloperSupportSession(
        token_hash=session_token_hash(raw),
        developer_user_id=user.id,
        target_tenant_id=tenant.id,
        reason=payload.reason.strip(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes),
    )
    db.add(session)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="developer.support.started",
        entity_type="tenant", entity_id=str(tenant.id),
        metadata={"target_tenant_id": str(tenant.id), "reason": payload.reason.strip(), "duration_minutes": payload.duration_minutes})
    await db.commit()
    response.set_cookie("kalam_support_context", raw, httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=payload.duration_minutes * 60, path="/")
    return {"tenant_id": str(tenant.id), "tenant_name": tenant.name, "expires_at": session.expires_at, "reason": session.reason}


@router.get("/developer/support/current")
async def developer_support_current(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Platform Developer access required")
    raw = request.cookies.get("kalam_support_context")
    if not raw:
        return {"active": False}
    session = await db.scalar(select(DeveloperSupportSession).where(
        DeveloperSupportSession.token_hash == session_token_hash(raw),
        DeveloperSupportSession.developer_user_id == user.id,
        DeveloperSupportSession.revoked_at.is_(None),
        DeveloperSupportSession.expires_at > datetime.now(timezone.utc),
    ))
    if session is None:
        return {"active": False}
    tenant = await db.get(Tenant, session.target_tenant_id)
    return {"active": True, "tenant_id": str(session.target_tenant_id), "tenant_name": tenant.name if tenant else "Tenant", "expires_at": session.expires_at, "reason": session.reason}


@router.post("/developer/support/stop")
async def developer_support_stop(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _is_platform_developer(user, db):
        raise HTTPException(status_code=403, detail="Platform Developer access required")
    raw = request.cookies.get("kalam_support_context")
    if raw:
        session = await db.scalar(select(DeveloperSupportSession).where(
            DeveloperSupportSession.token_hash == session_token_hash(raw),
            DeveloperSupportSession.developer_user_id == user.id,
            DeveloperSupportSession.revoked_at.is_(None),
        ))
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="developer.support.stopped",
                entity_type="tenant", entity_id=str(session.target_tenant_id), metadata={"reason": session.reason})
            await db.commit()
    response.delete_cookie("kalam_support_context", path="/")
    return {"active": False}


class SupportCaseCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40, pattern=r"^(access|learning|assessment|credentials|compliance|reporting|integration|technical|security|other)$")
    severity: str = Field(min_length=3, max_length=20, pattern=r"^(routine|important|urgent)$")
    subject: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=10, max_length=4000)
    route: str | None = Field(default=None, max_length=300)


class SupportCaseAdminUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(open|in_progress|waiting|resolved|closed)$")
    internal_note: str | None = Field(default=None, max_length=4000)
    assign_to_self: bool | None = None


class SupportMessageCreate(BaseModel):
    body: str = Field(min_length=2, max_length=4000)


class SupportAdminMessageCreate(SupportMessageCreate):
    visibility: str = Field(default="requester", pattern=r"^(requester|internal)$")


class SupportPolicyUpdate(BaseModel):
    response_targets_enabled: bool = False
    routine_hours: int = Field(default=48, ge=1, le=720)
    important_hours: int = Field(default=24, ge=1, le=720)
    urgent_hours: int = Field(default=4, ge=1, le=168)
    escalation_note: str | None = Field(default=None, max_length=1000)


def _case_number() -> str:
    return "SUP-" + uuid4().hex[:10].upper()


async def _support_admin_ids(db: AsyncSession, tenant_id: UUID) -> list[UUID]:
    rows = await db.execute(
        select(UserRole.user_id)
        .join(RolePermission, RolePermission.role_id == UserRole.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .join(User, User.id == UserRole.user_id)
        .where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
            Permission.key == "tenant.manage",
        )
        .distinct()
    )
    return list(rows.scalars().all())


def _serialize(item: SupportCase, requester: User | None = None, assignee: User | None = None) -> dict:
    return {
        "id": str(item.id),
        "case_number": item.case_number,
        "category": item.category,
        "severity": item.severity,
        "subject": item.subject,
        "description": item.description,
        "route": item.route,
        "status": item.status,
        "internal_note": item.internal_note,
        "assigned_to_user_id": str(item.assigned_to_user_id) if item.assigned_to_user_id else None,
        "requester": {
            "id": str(requester.id), "name": f"{requester.first_name} {requester.last_name}".strip(),
            "email": requester.email, "job_title": requester.job_title,
        } if requester else None,
        "assignee": {
            "id": str(assignee.id), "name": f"{assignee.first_name} {assignee.last_name}".strip(), "email": assignee.email,
        } if assignee else None,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "resolved_at": item.resolved_at,
    }


async def _messages(db: AsyncSession, case_id: UUID, *, include_internal: bool) -> list[dict]:
    stmt = select(SupportCaseMessage, User).join(User, User.id == SupportCaseMessage.author_user_id).where(SupportCaseMessage.case_id == case_id)
    if not include_internal:
        stmt = stmt.where(SupportCaseMessage.visibility == "requester")
    rows = (await db.execute(stmt.order_by(SupportCaseMessage.created_at.asc()))).all()
    return [{
        "id": str(message.id), "body": message.body, "visibility": message.visibility,
        "created_at": message.created_at,
        "author": {"id": str(author.id), "name": f"{author.first_name} {author.last_name}".strip()},
    } for message, author in rows]


@router.post("/cases", status_code=201)
async def create_case(payload: SupportCaseCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = SupportCase(
        tenant_id=user.tenant_id, requester_user_id=user.id, case_number=_case_number(),
        category=payload.category, severity=payload.severity, subject=payload.subject.strip(),
        description=payload.description.strip(), route=payload.route.strip() if payload.route else None, status="open",
    )
    db.add(item)
    await db.flush()
    for admin_id in await _support_admin_ids(db, user.tenant_id):
        if admin_id == user.id:
            continue
        await create_notification(
            db, tenant_id=user.tenant_id, user_id=admin_id,
            notification_type="support_case_created",
            title=f"New support case {item.case_number}",
            body=f"{item.severity.title()} · {item.subject}",
            dedupe_key=f"support-created:{item.id}:{admin_id}",
            action_href="/dashboard/admin/support",
            priority="critical" if item.severity == "urgent" else "high" if item.severity == "important" else "normal",
        )
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="support.case.created", entity_type="support_case", entity_id=str(item.id), metadata={"case_number": item.case_number, "category": item.category, "severity": item.severity})
    await db.commit()
    return _serialize(item)


@router.get("/cases")
async def list_cases(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(SupportCase).where(SupportCase.tenant_id == user.tenant_id, SupportCase.requester_user_id == user.id).order_by(SupportCase.created_at.desc()).limit(20))).scalars().all()
    return [_serialize(item) for item in items]


@router.get("/cases/{case_id}")
async def requester_case(case_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == user.tenant_id, SupportCase.requester_user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    assignee = await db.scalar(select(User).where(User.id == item.assigned_to_user_id, User.tenant_id == user.tenant_id)) if item.assigned_to_user_id else None
    return _serialize(item, user, assignee)


@router.get("/cases/{case_id}/messages")
async def requester_messages(case_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == user.tenant_id, SupportCase.requester_user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    return await _messages(db, item.id, include_internal=False)


@router.post("/cases/{case_id}/messages", status_code=201)
async def requester_message(case_id: UUID, payload: SupportMessageCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == user.tenant_id, SupportCase.requester_user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    message = SupportCaseMessage(case_id=item.id, author_user_id=user.id, body=payload.body.strip(), visibility="requester")
    db.add(message)
    if item.status in {"waiting", "resolved"}:
        item.status = "open"
        item.resolved_at = None
    recipients = [item.assigned_to_user_id] if item.assigned_to_user_id else await _support_admin_ids(db, item.tenant_id)
    for recipient_id in recipients:
        if recipient_id == user.id:
            continue
        await create_notification(
            db, tenant_id=item.tenant_id, user_id=recipient_id,
            notification_type="support_case_reply",
            title=f"Requester replied to {item.case_number}",
            body=item.subject,
            dedupe_key=f"support-requester-reply:{message.id}:{recipient_id}",
            action_href="/dashboard/admin/support",
            priority="high",
        )
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="support.case.message.created", entity_type="support_case", entity_id=str(item.id), metadata={"case_number": item.case_number, "visibility": "requester"})
    await db.commit()
    return {"id": str(message.id), "status": "created"}


@router.get("/admin/cases")
async def admin_list_cases(admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(SupportCase).where(SupportCase.tenant_id == admin.tenant_id).order_by(SupportCase.created_at.desc()).limit(200))).scalars().all()
    user_ids = {item.requester_user_id for item in items} | {item.assigned_to_user_id for item in items if item.assigned_to_user_id}
    users = {}
    if user_ids:
        users = {item.id: item for item in (await db.execute(select(User).where(User.id.in_(user_ids), User.tenant_id == admin.tenant_id))).scalars().all()}
    result = []
    for item in items:
        row = _serialize(item, users.get(item.requester_user_id), users.get(item.assigned_to_user_id) if item.assigned_to_user_id else None)
        row["message_count"] = len(await _messages(db, item.id, include_internal=True))
        result.append(row)
    return result


@router.get("/admin/cases/{case_id}/messages")
async def admin_messages(case_id: UUID, admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == admin.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    return await _messages(db, item.id, include_internal=True)


@router.post("/admin/cases/{case_id}/messages", status_code=201)
async def admin_message(case_id: UUID, payload: SupportAdminMessageCreate, admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == admin.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    message = SupportCaseMessage(case_id=item.id, author_user_id=admin.id, body=payload.body.strip(), visibility=payload.visibility)
    db.add(message)
    if payload.visibility == "requester":
        await create_notification(
            db, tenant_id=item.tenant_id, user_id=item.requester_user_id,
            notification_type="support_case_update",
            title=f"Support case {item.case_number} updated",
            body=f"A support administrator replied to: {item.subject}",
            dedupe_key=f"support-reply:{message.id}",
            action_href=f"/dashboard/help/cases/{item.id}",
            priority="high",
        )
    await audit(db, tenant_id=admin.tenant_id, actor_id=admin.id, action="support.case.message.created", entity_type="support_case", entity_id=str(item.id), metadata={"case_number": item.case_number, "visibility": payload.visibility})
    await db.commit()
    return {"id": str(message.id), "status": "created"}


@router.patch("/admin/cases/{case_id}")
async def admin_update_case(case_id: UUID, payload: SupportCaseAdminUpdate, admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SupportCase).where(SupportCase.id == case_id, SupportCase.tenant_id == admin.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Support case not found")
    changed: list[str] = []
    previous_status = item.status
    if payload.status is not None:
        item.status = payload.status
        item.resolved_at = datetime.now(timezone.utc) if payload.status in {"resolved", "closed"} else None
        changed.append("status")
    if payload.internal_note is not None:
        item.internal_note = payload.internal_note.strip() or None
        changed.append("internal_note")
    if payload.assign_to_self is True:
        item.assigned_to_user_id = admin.id
        changed.append("assigned_to_user_id")
    elif payload.assign_to_self is False and "assign_to_self" in payload.model_fields_set:
        item.assigned_to_user_id = None
        changed.append("assigned_to_user_id")
    if payload.status is not None and payload.status != previous_status:
        await create_notification(
            db, tenant_id=item.tenant_id, user_id=item.requester_user_id,
            notification_type="support_case_status",
            title=f"Support case {item.case_number}: {payload.status.replace('_', ' ').title()}",
            body=item.subject,
            dedupe_key=f"support-status:{item.id}:{payload.status}:{uuid4().hex[:8]}",
            action_href=f"/dashboard/help/cases/{item.id}",
            priority="high" if payload.status not in {"resolved", "closed"} else "normal",
        )
    await audit(db, tenant_id=admin.tenant_id, actor_id=admin.id, action="support.case.updated", entity_type="support_case", entity_id=str(item.id), metadata={"case_number": item.case_number, "changed_fields": changed, "status": item.status})
    await db.commit()
    await db.refresh(item)
    requester = await db.scalar(select(User).where(User.id == item.requester_user_id, User.tenant_id == admin.tenant_id))
    assignee = await db.scalar(select(User).where(User.id == item.assigned_to_user_id, User.tenant_id == admin.tenant_id)) if item.assigned_to_user_id else None
    return _serialize(item, requester, assignee)


@router.get("/admin/policy")
async def get_policy(admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == admin.tenant_id))
    settings = tenant.settings or {} if tenant else {}
    defaults = {"response_targets_enabled": False, "routine_hours": 48, "important_hours": 24, "urgent_hours": 4, "escalation_note": None}
    return {**defaults, **settings.get("support_policy", {})}


@router.patch("/admin/policy")
async def update_policy(payload: SupportPolicyUpdate, admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == admin.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    settings = dict(tenant.settings or {})
    settings["support_policy"] = payload.model_dump()
    tenant.settings = settings
    await audit(db, tenant_id=admin.tenant_id, actor_id=admin.id, action="support.policy.updated", entity_type="tenant", entity_id=str(tenant.id), metadata={"response_targets_enabled": payload.response_targets_enabled})
    await db.commit()
    return settings["support_policy"]


@router.get("/admin/metrics")
async def support_metrics(admin: User = Depends(require_permission("tenant.manage")), db: AsyncSession = Depends(get_db)):
    summary = await db.execute(
        select(
            func.count(SupportCase.id),
            func.sum(case((SupportCase.status == "open", 1), else_=0)),
            func.sum(case((SupportCase.status == "in_progress", 1), else_=0)),
            func.sum(case((SupportCase.status == "waiting", 1), else_=0)),
            func.sum(case((and_(SupportCase.severity == "urgent", SupportCase.status.not_in(("resolved", "closed"))), 1), else_=0)),
            func.sum(case((SupportCase.status.in_(("resolved", "closed")), 1), else_=0)),
            func.avg(func.extract("epoch", SupportCase.resolved_at - SupportCase.created_at)),
        ).where(SupportCase.tenant_id == admin.tenant_id)
    )
    total, open_count, in_progress, waiting, urgent_open, resolved, avg_resolution_seconds = summary.one()
    category_rows = await db.execute(
        select(SupportCase.category, func.count(SupportCase.id))
        .where(SupportCase.tenant_id == admin.tenant_id)
        .group_by(SupportCase.category)
    )
    return {
        "total": total or 0,
        "open": open_count or 0,
        "in_progress": in_progress or 0,
        "waiting": waiting or 0,
        "urgent_open": urgent_open or 0,
        "resolved": resolved or 0,
        "avg_resolution_hours": round(float(avg_resolution_seconds) / 3600, 1) if avg_resolution_seconds is not None else None,
        "by_category": {category: count for category, count in category_rows.all()},
    }
