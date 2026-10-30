from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import and_, case, func, or_, select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    is_platform_developer,
    require_permission,
    user_has_permission,
)
from app.core.config import settings
from app.core.security import support_context_token_hash
from app.db.models import (
    AuditLog,
    DeveloperSupportSession,
    KnowledgeArticle,
    Permission,
    PlatformIncident,
    RolePermission,
    SessionRecord,
    SupportCase,
    SupportCaseMessage,
    Tenant,
    User,
    UserRole,
)
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()

class DeveloperSupportStart(BaseModel):
    tenant_id: UUID
    reason: str = Field(min_length=10, max_length=500)
    duration_minutes: int = Field(default=60, ge=15, le=480)


class KnowledgeArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    summary: str | None = Field(default=None, max_length=500)
    body: str = Field(min_length=1, max_length=50000)
    category: str = Field(default="general", min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class KnowledgeArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    summary: str | None = Field(default=None, max_length=500)
    body: str | None = Field(default=None, min_length=1, max_length=50000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, pattern="^(draft|published|archived)$")


def _knowledge_article(item: KnowledgeArticle, *, include_body: bool = False) -> dict:
    article = {
        "id": str(item.id),
        "title": item.title,
        "summary": item.summary,
        "category": item.category,
        "tags": item.tags,
        "status": item.status,
        "published_at": item.published_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
    if include_body:
        article["body"] = item.body
    return article


async def _is_platform_developer(user: User, db: AsyncSession) -> bool:
    return await is_platform_developer(user, db)


async def _require_platform_permission(
    user: User,
    db: AsyncSession,
    permission_key: str,
    *,
    home_context_only: bool = False,
) -> UUID:
    home_tenant_id = await db.scalar(select(User.tenant_id).where(User.id == user.id))
    ops_tenant_id = await db.scalar(
        select(Tenant.id).where(Tenant.slug == settings.saas_ops_tenant_slug)
    )
    if (
        home_tenant_id is None
        or ops_tenant_id is None
        or home_tenant_id != ops_tenant_id
        or not await _is_platform_developer(user, db)
        or not await user_has_permission(user, db, permission_key)
    ):
        raise HTTPException(status_code=403, detail="Platform permission required")
    if home_context_only and user.tenant_id != home_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Exit customer support mode before changing platform operations",
        )
    return ops_tenant_id


class DeveloperTenantStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(active|suspended)$")


@router.get("/developer/health")
async def developer_platform_health(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_platform_permission(
        user, db, "platform.health.read", home_context_only=True
    )
    checks = {"database": "ready", "redis": "unknown"}
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        checks["database"] = "failed"

    redis = Redis.from_url(
        settings.redis_url, socket_connect_timeout=2, socket_timeout=2
    )
    try:
        checks["redis"] = "ready" if await redis.ping() else "failed"
    except RedisError:
        checks["redis"] = "failed"
    finally:
        await redis.aclose()

    status = "ready" if all(value == "ready" for value in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "checked_at": datetime.now(UTC)}


@router.get("/developer/audit")
async def developer_platform_audit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
):
    ops_tenant_id = await _require_platform_permission(
        user, db, "platform.audit.read", home_context_only=True
    )
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == ops_tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(item.id),
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "actor_id": str(item.actor_id) if item.actor_id else None,
            "request_id": item.request_id,
            "summary": item.summary,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


class PlatformIncidentCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=10, max_length=10000)
    severity: str = Field(pattern=r"^(sev1|sev2|sev3|sev4)$")
    impact: str | None = Field(default=None, max_length=500)
    owner_user_id: UUID | None = None


class PlatformIncidentUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(open|investigating|mitigated|resolved)$")
    severity: str | None = Field(default=None, pattern=r"^(sev1|sev2|sev3|sev4)$")
    impact: str | None = Field(default=None, max_length=500)
    owner_user_id: UUID | None = None


def _platform_incident_payload(item: PlatformIncident) -> dict:
    return {
        "id": str(item.id),
        "incident_number": item.incident_number,
        "title": item.title,
        "description": item.description,
        "severity": item.severity,
        "status": item.status,
        "impact": item.impact,
        "owner_user_id": str(item.owner_user_id) if item.owner_user_id else None,
        "detected_at": item.detected_at,
        "resolved_at": item.resolved_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/developer/incidents")
async def developer_list_incidents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
):
    await _require_platform_permission(
        user, db, "platform.incidents.manage", home_context_only=True
    )
    result = await db.execute(
        select(PlatformIncident).order_by(
            PlatformIncident.detected_at.desc(), PlatformIncident.created_at.desc()
        ).limit(limit)
    )
    return [_platform_incident_payload(item) for item in result.scalars().all()]


@router.post("/developer/incidents", status_code=201)
async def developer_create_incident(
    payload: PlatformIncidentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ops_tenant_id = await _require_platform_permission(
        user, db, "platform.incidents.manage", home_context_only=True
    )
    if payload.owner_user_id is not None:
        owner = await db.scalar(
            select(User.id).where(
                User.id == payload.owner_user_id, User.tenant_id == ops_tenant_id, User.is_active.is_(True)
            )
        )
        if owner is None:
            raise HTTPException(status_code=422, detail="Incident owner must be an active platform operator")
    item = PlatformIncident(
        incident_number=f"KAL-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:10].upper()}",
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        impact=payload.impact,
        owner_user_id=payload.owner_user_id,
    )
    db.add(item)
    db.add(AuditLog(
        tenant_id=ops_tenant_id, actor_id=user.id, action="platform.incident.created",
        entity_type="platform_incident", entity_id=str(item.id),
        summary=f"Created {item.incident_number}: {item.title}",
        record_metadata={"severity": item.severity, "status": item.status},
    ))
    await db.commit()
    await db.refresh(item)
    return _platform_incident_payload(item)


@router.patch("/developer/incidents/{incident_id}")
async def developer_update_incident(
    incident_id: UUID,
    payload: PlatformIncidentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ops_tenant_id = await _require_platform_permission(
        user, db, "platform.incidents.manage", home_context_only=True
    )
    item = await db.get(PlatformIncident, incident_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one incident field must be updated")
    if "owner_user_id" in changes and changes["owner_user_id"] is not None:
        owner = await db.scalar(
            select(User.id).where(
                User.id == changes["owner_user_id"], User.tenant_id == ops_tenant_id, User.is_active.is_(True)
            )
        )
        if owner is None:
            raise HTTPException(status_code=422, detail="Incident owner must be an active platform operator")
    previous_status = item.status
    for key, value in changes.items():
        setattr(item, key, value)
    if item.status == "resolved" and previous_status != "resolved":
        item.resolved_at = datetime.now(UTC)
    elif item.status != "resolved":
        item.resolved_at = None
    db.add(AuditLog(
        tenant_id=ops_tenant_id, actor_id=user.id, action="platform.incident.updated",
        entity_type="platform_incident", entity_id=str(item.id),
        summary=f"Updated {item.incident_number}: {item.title}",
        record_metadata={"changes": {key: str(value) if value is not None else None for key, value in changes.items()}},
    ))
    await db.commit()
    await db.refresh(item)
    return _platform_incident_payload(item)


@router.get("/developer/tenants")
async def developer_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_platform_permission(
        user, db, "platform.tenants.read", home_context_only=True
    )
    rows = (await db.execute(
        select(Tenant).where(
            Tenant.slug != settings.saas_ops_tenant_slug,
            Tenant.slug != settings.saas_demo_tenant_slug,
        ).order_by(Tenant.name)
    )).scalars().all()
    return [{"id": str(t.id), "name": t.name, "slug": t.slug, "status": t.status} for t in rows]


@router.patch("/developer/tenants/{tenant_id}/status")
async def developer_update_tenant_status(
    tenant_id: UUID,
    payload: DeveloperTenantStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ops_tenant_id = await _require_platform_permission(
        user, db, "platform.tenants.manage", home_context_only=True
    )
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None or tenant.id == ops_tenant_id or tenant.slug == settings.saas_demo_tenant_slug:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    previous_status = tenant.status
    tenant.status = payload.status
    revoked_sessions = 0
    if payload.status == "suspended":
        result = await db.execute(
            update(SessionRecord)
            .where(
                SessionRecord.user_id.in_(
                    select(User.id).where(User.tenant_id == tenant.id)
                ),
                SessionRecord.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        revoked_sessions = int(getattr(result, "rowcount", 0) or 0)
    await audit(
        db,
        tenant_id=ops_tenant_id,
        actor_id=user.id,
        action="platform.tenant.status_changed",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={
            "from": previous_status,
            "to": payload.status,
            "revoked_sessions": revoked_sessions,
        },
    )
    await db.commit()
    return {
        "id": str(tenant.id),
        "status": tenant.status,
        "revoked_sessions": revoked_sessions,
    }


@router.post("/developer/support/start")
async def developer_support_start(
    payload: DeveloperSupportStart,
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_platform_permission(
        user, db, "platform.support.access", home_context_only=True
    )
    tenant = await db.get(Tenant, payload.tenant_id)
    if tenant is None or tenant.status != "active" or tenant.slug in {
        settings.saas_ops_tenant_slug, settings.saas_demo_tenant_slug
    }:
        raise HTTPException(status_code=422, detail="Choose an active customer tenant")
    raw_login_token = request.cookies.get(settings.session_cookie_name)
    if not raw_login_token:
        raise HTTPException(status_code=401, detail="Authenticated platform session required")
    raw = token_urlsafe(48)
    session = DeveloperSupportSession(
        token_hash=support_context_token_hash(raw, raw_login_token),
        developer_user_id=user.id,
        target_tenant_id=tenant.id,
        reason=payload.reason.strip(),
        expires_at=datetime.now(UTC) + timedelta(minutes=payload.duration_minutes),
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
    await _require_platform_permission(user, db, "platform.support.access")
    raw = request.cookies.get("kalam_support_context")
    if not raw:
        return {"active": False}
    raw_login_token = request.cookies.get(settings.session_cookie_name, "")
    session = await db.scalar(select(DeveloperSupportSession).where(
        DeveloperSupportSession.token_hash == support_context_token_hash(raw, raw_login_token),
        DeveloperSupportSession.developer_user_id == user.id,
        DeveloperSupportSession.revoked_at.is_(None),
        DeveloperSupportSession.expires_at > datetime.now(UTC),
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
    await _require_platform_permission(user, db, "platform.support.access")
    raw = request.cookies.get("kalam_support_context")
    if raw:
        raw_login_token = request.cookies.get(settings.session_cookie_name, "")
        session = await db.scalar(select(DeveloperSupportSession).where(
            DeveloperSupportSession.token_hash == support_context_token_hash(raw, raw_login_token),
            DeveloperSupportSession.developer_user_id == user.id,
            DeveloperSupportSession.revoked_at.is_(None),
        ))
        if session:
            session.revoked_at = datetime.now(UTC)
            platform_user = await db.scalar(select(User).where(User.id == user.id))
            if platform_user is not None:
                await audit(
                    db,
                    tenant_id=platform_user.tenant_id,
                    actor_id=platform_user.id,
                    action="developer.support.stopped",
                    entity_type="tenant",
                    entity_id=str(session.target_tenant_id),
                    metadata={"reason": session.reason},
                )
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


@router.get("/knowledge")
async def list_knowledge_articles(
    q: str | None = Query(default=None, max_length=160),
    category: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    can_manage = await user_has_permission(user, db, "tenant.manage")
    stmt = select(KnowledgeArticle).where(KnowledgeArticle.tenant_id == user.tenant_id)
    if not can_manage:
        stmt = stmt.where(KnowledgeArticle.status == "published")
    if category:
        stmt = stmt.where(KnowledgeArticle.category == category.strip())
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(KnowledgeArticle.title.ilike(pattern), KnowledgeArticle.summary.ilike(pattern), KnowledgeArticle.body.ilike(pattern)))
    rows = (await db.execute(stmt.order_by(KnowledgeArticle.updated_at.desc()).limit(limit))).scalars().all()
    return [_knowledge_article(item) for item in rows]


@router.get("/knowledge/{article_id}")
async def get_knowledge_article(
    article_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id, KnowledgeArticle.tenant_id == user.tenant_id))
    can_manage = await user_has_permission(user, db, "tenant.manage")
    if item is None or (item.status != "published" and not can_manage):
        raise HTTPException(status_code=404, detail="Knowledge article not found")
    return _knowledge_article(item, include_body=True)


@router.post("/admin/knowledge", status_code=201)
async def create_knowledge_article(
    payload: KnowledgeArticleCreate,
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = KnowledgeArticle(
        tenant_id=user.tenant_id,
        title=payload.title.strip(),
        summary=payload.summary.strip() if payload.summary else None,
        body=payload.body.strip(),
        category=payload.category.strip(),
        tags=list(dict.fromkeys(tag.strip() for tag in payload.tags if tag.strip())),
        status=payload.status,
        created_by=user.id,
        updated_by=user.id,
        published_at=datetime.now(UTC) if payload.status == "published" else None,
    )
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="knowledge.article.created", entity_type="knowledge_article", entity_id=str(item.id), metadata={"status": item.status, "category": item.category})
    await db.commit()
    await db.refresh(item)
    return _knowledge_article(item, include_body=True)


@router.patch("/admin/knowledge/{article_id}")
async def update_knowledge_article(
    article_id: UUID,
    payload: KnowledgeArticleUpdate,
    user: User = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id, KnowledgeArticle.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge article not found")
    changes = payload.model_dump(exclude_unset=True)
    for field in ("title", "summary", "body", "category"):
        if field in changes and changes[field] is not None:
            changes[field] = changes[field].strip()
    if "tags" in changes and changes["tags"] is not None:
        changes["tags"] = list(dict.fromkeys(tag.strip() for tag in changes["tags"] if tag.strip()))
    elif "tags" in changes:
        raise HTTPException(status_code=422, detail="tags must be a list of strings")
    for field, value in changes.items():
        if field == "summary":
            setattr(item, field, value.strip() if isinstance(value, str) and value.strip() else None)
        elif value is not None:
            setattr(item, field, value)
    if item.status == "published" and item.published_at is None:
        item.published_at = datetime.now(UTC)
    item.updated_by = user.id
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="knowledge.article.updated", entity_type="knowledge_article", entity_id=str(item.id), metadata={"fields": sorted(changes), "status": item.status})
    await db.commit()
    await db.refresh(item)
    return _knowledge_article(item, include_body=True)


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
        item.resolved_at = datetime.now(UTC) if payload.status in {"resolved", "closed"} else None
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
