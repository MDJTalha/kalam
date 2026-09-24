from collections.abc import Callable
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import session_token_hash, utcnow
from app.db.models import Permission, Role, RolePermission, SessionRecord, User, UserRole
from app.db.session import get_db

async def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    result = await db.execute(
        select(SessionRecord, User)
        .join(User, User.id == SessionRecord.user_id)
        .where(SessionRecord.token_hash == session_token_hash(session_token))
        .where(SessionRecord.revoked_at.is_(None))
        .where(SessionRecord.expires_at > utcnow())
        .where(User.is_active.is_(True))
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return row[1]

async def user_has_permission(
    user: User,
    db: AsyncSession,
    permission_key: str,
) -> bool:
    result = await db.execute(
        select(Permission.id)
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
