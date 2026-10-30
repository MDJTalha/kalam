from collections.abc import Callable
from copy import copy

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import session_token_hash, support_context_token_hash, utcnow
from app.db.models import (
    DeveloperSupportSession,
    Permission,
    Role,
    RolePermission,
    SessionRecord,
    Tenant,
    User,
    UserRole,
)
from app.db.session import get_db


async def get_current_user(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    result = await db.execute(
        select(SessionRecord, User)
        .join(User, User.id == SessionRecord.user_id)
        .join(Tenant, Tenant.id == User.tenant_id)
        .where(SessionRecord.token_hash == session_token_hash(session_token))
        .where(SessionRecord.revoked_at.is_(None))
        .where(SessionRecord.expires_at > utcnow())
        .where(User.is_active.is_(True))
        .where(Tenant.status == "active")
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = row[1]
    support_token = request.cookies.get("kalam_support_context")
    if not support_token:
        return user
    support = await db.scalar(
        select(DeveloperSupportSession).where(
            DeveloperSupportSession.token_hash
            == support_context_token_hash(support_token, session_token),
            DeveloperSupportSession.developer_user_id == user.id,
            DeveloperSupportSession.revoked_at.is_(None),
            DeveloperSupportSession.expires_at > utcnow(),
        )
    )
    if support is None:
        return user
    effective = copy(user)
    effective.tenant_id = support.target_tenant_id
    return effective


async def is_platform_developer(user: User, db: AsyncSession) -> bool:
    """Recognize only a Kalam-owned account carrying Kalam's platform role.

    Looking up the persisted User row (rather than trusting the request-scoped
    copy) keeps this check correct during a time-limited support context while
    preventing a customer-tenant identity from gaining privileges by being
    linked to an internal role.
    """
    if not settings.saas_ops_tenant_slug:
        return False
    result = await db.execute(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .join(Tenant, Tenant.id == Role.tenant_id)
        .where(UserRole.user_id == user.id)
        .where(User.tenant_id == Tenant.id)
        .where(Tenant.slug == settings.saas_ops_tenant_slug)
        .where(Role.role_kind == "platform")
        .where(Role.name.ilike("platform developer"))
    )
    return result.scalar_one_or_none() is not None

async def user_has_permission(
    user: User,
    db: AsyncSession,
    permission_key: str,
) -> bool:
    # Resolve the persisted home tenant. During an active, audited support
    # session get_current_user() returns a copy scoped to the customer tenant.
    home_tenant_id = await db.scalar(select(User.tenant_id).where(User.id == user.id))
    if home_tenant_id is None:
        return False

    platform_developer = await is_platform_developer(user, db)

    # Platform permissions are explicit and are only granted to a Platform
    # Developer whose persisted home identity belongs to Kalam's operations
    # tenant. There is no blanket "developer can do everything" shortcut.
    if permission_key.startswith("platform."):
        if not platform_developer:
            return False
        result = await db.execute(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
            .where(Role.tenant_id == home_tenant_id)
            .where(Role.role_kind == "platform")
            .where(Role.name.ilike("platform developer"))
            .where(Permission.key == permission_key)
        )
        return result.scalar_one_or_none() is not None

    # Commercial CRM belongs to the Kalam operations tenant, never a customer
    # tenant or a support context. Owner and sales roles receive explicit CRM
    # permissions in the internal workspace only.
    if permission_key.startswith("saas.crm."):
        ops_tenant_id = await db.scalar(
            select(Tenant.id).where(Tenant.slug == settings.saas_ops_tenant_slug)
        )
        if ops_tenant_id is None or home_tenant_id != ops_tenant_id or user.tenant_id != ops_tenant_id:
            return False

    # Customer workspace permissions are available to a Developer only while
    # get_current_user() has resolved a valid, unexpired support context.
    # The context is session-bound, reasoned, time-limited and audited.
    if platform_developer and user.tenant_id != home_tenant_id:
        return True

    result = await db.execute(
        select(Permission.id)
        .distinct()
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
        .where(Role.tenant_id == user.tenant_id)
        .where(Permission.key == permission_key)
    )
    return result.scalar_one_or_none() is not None


def require_permission(permission_key: str) -> Callable:
    async def dependency(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not await user_has_permission(user, db, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return dependency
