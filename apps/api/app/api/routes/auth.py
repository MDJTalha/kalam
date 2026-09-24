from datetime import timedelta
from secrets import token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import hash_password, new_session_token, session_token_hash, utcnow, verify_password
from app.db.models import Invitation, PasswordResetToken, SessionRecord, Tenant, User, UserRole
from app.db.session import get_db
from app.services.audit import audit
from app.services.email import send_email

router = APIRouter()

class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class ForgotPasswordRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

async def _request_password_reset(payload: ForgotPasswordRequest, db: AsyncSession):
    result = await db.execute(
        select(User).join(Tenant, Tenant.id == User.tenant_id)
        .where(User.email == str(payload.email).lower())
        .where(Tenant.slug == payload.tenant_slug.lower())
        .where(Tenant.status == "active")
        .where(User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return {"status": "accepted"}
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=utcnow())
    )
    raw_token = token_urlsafe(36)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=session_token_hash(raw_token),
        expires_at=utcnow() + timedelta(minutes=settings.reset_token_minutes),
    ))
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="auth.password_reset.requested", entity_type="user", entity_id=str(user.id))
    await db.commit()
    reset_url = f"{settings.web_origin}/reset-password?token={raw_token}"
    send_email(
        recipient=user.email,
        subject="Corporate LMS password reset",
        text=("Use this secure link to reset your password. "
              f"It expires in {settings.reset_token_minutes} minutes.\n\n{reset_url}"),
    )
    return {"status": "accepted"}

@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).join(Tenant, Tenant.id == User.tenant_id)
        .where(User.email == str(payload.email).lower())
        .where(Tenant.slug == payload.tenant_slug.lower())
        .where(Tenant.status == "active")
    )
    user = result.scalar_one_or_none()
    now = utcnow()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= settings.max_failed_login_attempts:
            user.failed_login_count = 0
            user.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
            await audit(
                db,
                tenant_id=user.tenant_id,
                actor_id=user.id,
                action="auth.account.locked",
                entity_type="user",
                entity_id=str(user.id),
                summary="Account temporarily locked after repeated failed authentication attempts",
            )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.failed_login_count = 0
    user.locked_until = None
    raw_token = new_session_token()
    session = SessionRecord(
        user_id=user.id, token_hash=session_token_hash(raw_token),
        expires_at=utcnow() + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(session)
    user.last_login_at = utcnow()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="auth.login", entity_type="session", entity_id=str(session.id))
    await db.commit()
    response.set_cookie(
        settings.session_cookie_name, raw_token, httponly=True,
        secure=settings.cookie_secure, samesite="lax",
        max_age=settings.session_ttl_seconds, path="/",
    )
    return {"status": "authenticated", "user_id": str(user.id),
            "tenant_id": str(user.tenant_id), "tenant_slug": payload.tenant_slug.lower()}

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await _request_password_reset(payload, db)

@router.post("/reset-password")
@router.post("/password-reset/confirm")
async def reset_password(payload: ResetPasswordRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken, User).join(User, User.id == PasswordResetToken.user_id)
        .where(PasswordResetToken.token_hash == session_token_hash(payload.token))
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > utcnow())
        .where(User.is_active.is_(True))
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    token_record, user = row
    user.password_hash = hash_password(payload.new_password)
    token_record.used_at = utcnow()
    await db.execute(
        update(SessionRecord)
        .where(SessionRecord.user_id == user.id, SessionRecord.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="auth.password_reset.completed", entity_type="user", entity_id=str(user.id))
    await db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"status": "password_updated"}

@router.post("/invitations/accept")
async def accept_invitation(payload: InvitationAccept, db: AsyncSession = Depends(get_db)):
    invite = await db.scalar(
        select(Invitation)
        .where(Invitation.token_hash == session_token_hash(payload.token))
        .where(Invitation.accepted_at.is_(None))
        .where(Invitation.expires_at > utcnow())
    )
    if invite is None:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    existing = await db.scalar(
        select(User).where(User.tenant_id == invite.tenant_id, User.email == invite.email)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(
        tenant_id=invite.tenant_id, email=invite.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name, last_name=payload.last_name, is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=invite.role_id))
    invite.accepted_at = utcnow()
    await audit(db, tenant_id=invite.tenant_id, actor_id=user.id,
                action="user.invitation.accepted", entity_type="user", entity_id=str(user.id))
    await db.commit()
    return {"status": "accepted", "user_id": str(user.id)}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "tenant_id": str(user.tenant_id),
            "email": user.email, "first_name": user.first_name,
            "last_name": user.last_name, "employee_number": user.employee_number,
            "job_title": user.job_title}

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        result = await db.execute(
            select(SessionRecord, User).join(User, User.id == SessionRecord.user_id)
            .where(SessionRecord.token_hash == session_token_hash(raw_token))
        )
        row = result.first()
        if row:
            session, user = row
            session.revoked_at = utcnow()
            await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                        action="auth.logout", entity_type="session", entity_id=str(session.id))
            await db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"status": "logged_out"}
