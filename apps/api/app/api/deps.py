from collections.abc import Callable
from copy import copy
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import session_token_hash, utcnow
from app.db.models import DeveloperSupportSession, Permission, Role, RolePermission, SessionRecord, Tenant, User, UserRole
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
            DeveloperSupportSession.token_hash == session_token_hash(support_token),
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
    # CRM is a Kalam-internal capability and must never be granted to a
    # customer-tenant identity, even if a stale role-permission row exists.
    platform_developer = await is_platform_developer(user, db)
    if permission_key.startswith("saas.crm.") and not platform_developer:
        return False

    # Platform Developer is the internal product-development role. It must be
    # able to exercise every product permission for support, QA and debugging.
    # This is role-based (not tenant/customer-specific) and does not bypass the
    # normal tenant/session boundary enforced by get_current_user().
    if platform_developer:
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
