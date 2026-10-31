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


async def is_saas_ops_user(user: User, db: AsyncSession) -> bool:
    """Return true only for identities whose persisted home tenant is the SaaS operations tenant."""
    slug = settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug
    if not slug:
        return False
    home_tenant_id = await db.scalar(select(User.tenant_id).where(User.id == user.id))
    if home_tenant_id is None:
        return False
    return await db.scalar(
        select(Tenant.id).where(Tenant.id == home_tenant_id, Tenant.slug == slug)
    ) is not None


async def is_saas_demo_user(user: User, db: AsyncSession) -> bool:
    """Recognize the explicitly configured demo CRM identity by persisted home tenant."""
    if (
        not settings.saas_demo_crm_enabled
        or not settings.saas_demo_tenant_slug
        or not settings.saas_demo_admin_email
    ):
        return False
    home_tenant_id = await db.scalar(select(User.tenant_id).where(User.id == user.id))
    if home_tenant_id is None:
        return False
    return await db.scalar(
        select(Tenant.id).where(
            Tenant.id == home_tenant_id,
            Tenant.slug == settings.saas_demo_tenant_slug,
            Tenant.status == "active",
        )
    ) is not None and user.email.lower() == settings.saas_demo_admin_email.lower()


async def is_saas_super_admin(user: User, db: AsyncSession) -> bool:
    """Recognize the explicit SaaS Super Admin role in its own operations tenant."""
    slug = settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug
    if not slug:
        return False
    result = await db.execute(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .join(Tenant, Tenant.id == Role.tenant_id)
        .where(UserRole.user_id == user.id)
        .where(User.tenant_id == Tenant.id)
        .where(Tenant.slug == slug)
        .where(Role.role_kind == "platform")
        .where(Role.name.ilike("saas super admin"))
    )
    return result.scalar_one_or_none() is not None


async def is_platform_developer(user: User, db: AsyncSession) -> bool:
    """Recognize only a Kalam-owned account carrying Kalam's platform role.

    Looking up the persisted User row (rather than trusting the request-scoped
    copy) keeps this check correct during a time-limited support context while
    preventing a customer-tenant identity from gaining privileges by being
    linked to an internal role.
    """
    slug = settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug
    if not slug:
        return False
    result = await db.execute(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .join(Tenant, Tenant.id == Role.tenant_id)
        .where(UserRole.user_id == user.id)
        .where(User.tenant_id == Tenant.id)
        .where(Tenant.slug == slug)
        .where(Role.role_kind == "platform")
        .where(Role.name.ilike("platform developer"))
    )
    return result.scalar_one_or_none() is not None

async def user_has_permission(
    user: User,
    db: AsyncSession,
    permission_key: str,
) -> bool:
    # Platform Developer is the internal engineering/support role and may
    # exercise product permissions after normal authentication/session checks.
    platform_developer = await is_platform_developer(user, db)
    if platform_developer:
        return True

    # Every SaaS capability is confined to the persisted internal operations
    # tenant, with one explicitly configured demo identity exception. Customer
    # tenant users cannot gain SaaS access from stale or accidentally assigned grants.
    if permission_key.startswith("saas.") and not (
        await is_saas_ops_user(user, db) or await is_saas_demo_user(user, db)
    ):
        return False

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
