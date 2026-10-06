import base64
import hashlib
import json
import os
import secrets
from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import urlencode
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_platform_developer
from app.core.config import settings
from app.core.security import hash_password, new_session_token, session_token_hash, utcnow, verify_password
from app.db.models import Integration, Invitation, OrgUnit, PasswordResetToken, Permission, Role, RolePermission, SessionRecord, Tenant, User, UserRole
from app.db.session import get_db
from app.services.audit import audit
from app.services.email import send_email
from app.services.integration_adapters import IntegrationCheckError, get_oidc_discovery

router = APIRouter()

class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class ForgotPasswordRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email: EmailStr

def _validate_password_strength(value: str) -> str:
    if len(value) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if len(value) > 128:
        raise ValueError("Password must not exceed 128 characters")
    if not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value) or not any(not c.isalnum() for c in value):
        raise ValueError("Password must include uppercase, lowercase, number, and special character")
    return value

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)

class AuthDiscovery(BaseModel):
    recognized: bool = False
    tenant_slug: str
    tenant_name: str | None = None
    password_available: bool = True
    sso_providers: list[dict[str, str]] = Field(default_factory=list)


class UserPreferencesUpdate(BaseModel):
    preferred_name: str | None = Field(default=None, max_length=80)
    density: str = Field(default="comfortable", pattern=r"^(comfortable|compact)$")
    reduce_motion: bool = False
    timezone: str = Field(default="UTC", min_length=1, max_length=80)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        candidate = value.strip()
        try:
            ZoneInfo(candidate)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unsupported time zone") from exc
        return candidate


@router.get("/discovery/{tenant_slug}", response_model=AuthDiscovery)
async def auth_discovery(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    slug = tenant_slug.strip().lower()
    if len(slug) < 2 or len(slug) > 100:
        return AuthDiscovery(tenant_slug=slug)
    tenant = await db.scalar(
        select(Tenant).where(Tenant.slug == slug, Tenant.status == "active")
    )
    if tenant is None:
        return AuthDiscovery(tenant_slug=slug)

    integrations = (
        await db.execute(
            select(Integration).where(
                Integration.tenant_id == tenant.id,
                Integration.provider == "oidc",
                Integration.status == "connected",
            )
        )
    ).scalars().all()

    providers: list[dict[str, str]] = []
    password_available = True
    for item in integrations:
        config = item.config or {}
        if config.get("login_enabled") is not True:
            continue
        providers.append({
            "provider": item.provider,
            "label": str(config.get("display_name") or ("OpenID Connect SSO" if item.provider == "oidc" else "SAML SSO")),
        })
        if config.get("password_login_enabled") is False:
            password_available = False

    return AuthDiscovery(
        recognized=True,
        tenant_slug=tenant.slug,
        tenant_name=tenant.name,
        password_available=password_available,
        sso_providers=providers,
    )


SSO_TRANSACTION_COOKIE = "kognivon_sso_txn"


def _sso_cipher() -> Fernet:
    if not settings.sso_state_key:
        raise HTTPException(status_code=503, detail="Enterprise SSO is not enabled for this environment")
    try:
        return Fernet(settings.sso_state_key.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=503, detail="Enterprise SSO protection is misconfigured") from exc


async def _oidc_login_integration(
    db: AsyncSession,
    tenant_slug: str,
) -> tuple[Tenant, Integration]:
    tenant = await db.scalar(
        select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active")
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    integration = await db.scalar(
        select(Integration).where(
            Integration.tenant_id == tenant.id,
            Integration.provider == "oidc",
            Integration.status == "connected",
        )
    )
    if integration is None or (integration.config or {}).get("login_enabled") is not True:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    return tenant, integration


def _oidc_redirect_uri() -> str:
    return settings.web_origin.rstrip("/") + "/api/auth/sso/oidc/callback"


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _validate_oidc_id_token(
    id_token: str,
    jwks: dict,
    *,
    issuer: str,
    client_id: str,
    nonce: str,
) -> dict:
    key_set = KeySet.import_key_set(jwks)  # type: ignore[arg-type]
    token = jwt.decode(
        id_token,
        key_set,
        algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
    )
    claims = token.claims
    JWTClaimsRegistry(
        iss={"essential": True, "value": issuer},
        aud={"essential": True, "value": client_id},
        exp={"essential": True},
        nonce={"essential": True, "value": nonce},
    ).validate(claims)
    return claims


async def _create_authenticated_session(
    user: User,
    response: Response,
    db: AsyncSession,
    *,
    audit_action: str,
) -> None:
    raw_token = new_session_token()
    session = SessionRecord(
        user_id=user.id,
        token_hash=session_token_hash(raw_token),
        expires_at=utcnow() + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(session)
    user.last_login_at = utcnow()
    user.failed_login_count = 0
    user.locked_until = None
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action=audit_action,
        entity_type="session",
        entity_id=str(session.id),
    )
    await db.commit()
    response.set_cookie(
        settings.session_cookie_name,
        raw_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )


@router.get("/sso/{tenant_slug}/oidc/start")
async def oidc_start(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    slug = tenant_slug.strip().lower()
    tenant, integration = await _oidc_login_integration(db, slug)
    config = integration.config or {}
    try:
        metadata = await get_oidc_discovery(config)
    except IntegrationCheckError as exc:
        raise HTTPException(status_code=503, detail="Enterprise SSO discovery failed") from exc

    client_id = str(config.get("client_id") or "").strip()
    secret_env = str(config.get("client_secret_env") or "").strip()
    if not client_id or not secret_env or not os.getenv(secret_env):
        raise HTTPException(status_code=503, detail="Enterprise SSO client credentials are not configured")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    transaction = {
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "state": state,
        "nonce": nonce,
        "code_verifier": verifier,
    }
    encrypted = _sso_cipher().encrypt(json.dumps(transaction).encode("utf-8")).decode("ascii")
    query = urlencode({
        "client_id": client_id,
        "response_type": "code",
        "scope": str(config.get("scope") or "openid email profile"),
        "redirect_uri": _oidc_redirect_uri(),
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    response = RedirectResponse(str(metadata["authorization_endpoint"]) + "?" + query, status_code=302)
    response.set_cookie(
        SSO_TRANSACTION_COOKIE,
        encrypted,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.sso_transaction_ttl_seconds,
        path="/api/auth/sso/oidc/callback",
    )
    return response


@router.get("/sso/oidc/callback")
async def oidc_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if error:
        return RedirectResponse(settings.web_origin.rstrip("/") + "/login?sso=failed", status_code=302)
    cookie = request.cookies.get(SSO_TRANSACTION_COOKIE)
    if not cookie or not code or not state:
        raise HTTPException(status_code=400, detail="Invalid SSO callback")
    try:
        raw = _sso_cipher().decrypt(
            cookie.encode("ascii"),
            ttl=settings.sso_transaction_ttl_seconds,
        )
        transaction = json.loads(raw.decode("utf-8"))
    except (InvalidToken, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Expired or invalid SSO transaction") from exc
    if not secrets.compare_digest(str(transaction.get("state") or ""), state):
        raise HTTPException(status_code=400, detail="Invalid SSO state")

    tenant_slug = str(transaction.get("tenant_slug") or "")
    tenant, integration = await _oidc_login_integration(db, tenant_slug)
    config = integration.config or {}
    try:
        metadata = await get_oidc_discovery(config)
    except IntegrationCheckError as exc:
        raise HTTPException(status_code=503, detail="Enterprise SSO discovery failed") from exc

    client_id = str(config.get("client_id") or "").strip()
    secret_env = str(config.get("client_secret_env") or "").strip()
    client_secret = os.getenv(secret_env) if secret_env else None
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Enterprise SSO client credentials are not configured")

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": _oidc_redirect_uri(),
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": str(transaction.get("code_verifier") or ""),
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        token_response = await client.post(str(metadata["token_endpoint"]), data=token_payload)
        if token_response.status_code >= 400:
            raise HTTPException(status_code=401, detail="Enterprise SSO token exchange failed")
        tokens = token_response.json()
        id_token = tokens.get("id_token")
        if not isinstance(id_token, str):
            raise HTTPException(status_code=401, detail="Enterprise SSO did not return an identity token")
        jwks_response = await client.get(str(metadata["jwks_uri"]), headers={"Accept": "application/json"})
        if jwks_response.status_code >= 400:
            raise HTTPException(status_code=503, detail="Enterprise SSO signing keys are unavailable")
        jwks = jwks_response.json()

    try:
        claims = _validate_oidc_id_token(
            id_token,
            jwks,
            issuer=str(metadata["issuer"]),
            client_id=client_id,
            nonce=str(transaction.get("nonce") or ""),
        )
    except JoseError as exc:
        raise HTTPException(status_code=401, detail="Enterprise SSO identity token validation failed") from exc

    email = str(claims.get("email") or "").strip().lower()
    if not email or claims.get("email_verified") is False:
        raise HTTPException(status_code=401, detail="Enterprise SSO requires a verified email address")
    user = await db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == email,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise HTTPException(status_code=403, detail="Your account is not provisioned for this Kalam workspace")

    response = RedirectResponse(settings.web_origin.rstrip("/") + "/dashboard", status_code=302)
    await _create_authenticated_session(user, response, db, audit_action="auth.sso.oidc.login")
    response.delete_cookie(SSO_TRANSACTION_COOKIE, path="/api/auth/sso/oidc/callback")
    return response


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
        .join(Tenant, Tenant.id == Invitation.tenant_id)
        .join(Role, Role.id == Invitation.role_id)
        .where(Invitation.token_hash == session_token_hash(payload.token))
        .where(Invitation.accepted_at.is_(None))
        .where(Invitation.expires_at > utcnow())
        .where(Tenant.status == "active")
        .where(Role.tenant_id == Invitation.tenant_id)
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

@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=422, detail="New password must be different from the current password")
    user.password_hash = hash_password(payload.new_password)
    raw_token = request.cookies.get(settings.session_cookie_name)
    current_hash = session_token_hash(raw_token) if raw_token else None
    result = await db.execute(select(SessionRecord).where(SessionRecord.user_id == user.id, SessionRecord.revoked_at.is_(None)))
    revoked = 0
    for session in result.scalars().all():
        if current_hash and session.token_hash == current_hash:
            continue
        session.revoked_at = utcnow()
        revoked += 1
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="auth.password.changed", entity_type="user", entity_id=str(user.id), metadata={"revoked_other_sessions": revoked})
    await db.commit()
    return {"status": "password_updated", "revoked_other_sessions": revoked}

@router.get("/sessions")
async def list_sessions(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get(settings.session_cookie_name)
    current_hash = session_token_hash(raw_token) if raw_token else None
    result = await db.execute(
        select(SessionRecord)
        .where(SessionRecord.user_id == user.id)
        .order_by(SessionRecord.expires_at.desc())
    )
    now = utcnow()
    return [{
        "id": str(item.id),
        "is_current": item.token_hash == current_hash,
        "status": "revoked" if item.revoked_at else ("expired" if item.expires_at <= now else "active"),
        "created_at": None,
        "expires_at": item.expires_at,
        "revoked_at": item.revoked_at,
    } for item in result.scalars().all()]

@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: UUID, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get(settings.session_cookie_name)
    current_hash = session_token_hash(raw_token) if raw_token else None
    session = await db.scalar(select(SessionRecord).where(SessionRecord.id == session_id, SessionRecord.user_id == user.id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.token_hash == current_hash:
        raise HTTPException(status_code=400, detail="Use logout to end the current session")
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="auth.session.revoked", entity_type="session", entity_id=str(session.id))
        await db.commit()
    return {"status": "revoked"}

@router.post("/sessions/revoke-others")
async def revoke_other_sessions(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get(settings.session_cookie_name)
    current_hash = session_token_hash(raw_token) if raw_token else None
    result = await db.execute(select(SessionRecord).where(SessionRecord.user_id == user.id, SessionRecord.revoked_at.is_(None)))
    sessions = list(result.scalars().all())
    count = 0
    for session in sessions:
        if session.token_hash != current_hash:
            session.revoked_at = utcnow()
            count += 1
    if count:
        await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="auth.sessions.revoked_others", entity_type="user", entity_id=str(user.id), metadata={"count": count})
        await db.commit()
    return {"status": "revoked", "count": count}

@router.get("/me")
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    access_rows = (
        await db.execute(
            select(Role.id, Role.name, Permission.key)
            .join(UserRole, UserRole.role_id == Role.id)
            .outerjoin(RolePermission, RolePermission.role_id == Role.id)
            .outerjoin(Permission, Permission.id == RolePermission.permission_id)
            .where(UserRole.user_id == user.id, Role.tenant_id == user.tenant_id)
            .order_by(Role.name, Permission.key)
        )
    ).all()
    role_map: dict[UUID, dict[str, str]] = {}
    permission_keys: set[str] = set()
    for role_id, role_name, permission_key in access_rows:
        role_map[role_id] = {"id": str(role_id), "name": role_name}
        if permission_key:
            permission_keys.add(permission_key)
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    org_unit_name = None
    if user.org_unit_id:
        org_unit_name = await db.scalar(select(OrgUnit.name).where(OrgUnit.id == user.org_unit_id, OrgUnit.tenant_id == user.tenant_id))
    manager_name = None
    if user.manager_id:
        manager = await db.scalar(select(User).where(User.id == user.manager_id, User.tenant_id == user.tenant_id))
        if manager:
            manager_name = f"{manager.first_name} {manager.last_name}".strip()
    roles = list(role_map.values())
    platform_developer = await is_platform_developer(user, db)
    if platform_developer and not any(item["name"].strip().lower() == "platform developer" for item in roles):
        platform_role_id = await db.scalar(select(Role.id).join(Tenant, Tenant.id == Role.tenant_id).where(
            Tenant.slug == settings.saas_ops_tenant_slug, Role.name.ilike("platform developer"), Role.role_kind == "platform"
        ))
        if platform_role_id is not None:
            roles.append({"id": str(platform_role_id), "name": "Platform Developer"})
    if platform_developer:
        # Platform Developer is the internal product-development role. Expose
        # the complete permission catalog so the web application can render
        # every authorized platform screen; endpoint authorization remains
        # enforced by user_has_permission().
        all_permission_keys = (
            await db.execute(select(Permission.key).order_by(Permission.key))
        ).scalars().all()
        permissions = sorted(set(all_permission_keys))
    else:
        permissions = sorted(key for key in permission_keys if not key.startswith("saas.crm."))
    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "tenant_name": tenant.name if tenant else None,
        "tenant_slug": tenant.slug if tenant else None,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "employee_number": user.employee_number,
        "job_title": user.job_title,
        "org_unit_name": org_unit_name,
        "manager_name": manager_name,
        "last_login_at": user.last_login_at,
        "preferences": user.preferences or {},
        "roles": roles,
        "permissions": permissions,
    }


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    defaults = {"preferred_name": None, "density": "comfortable", "reduce_motion": False, "timezone": "UTC"}
    return {**defaults, **(user.preferences or {})}


@router.patch("/preferences")
async def update_preferences(payload: UserPreferencesUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    preferred = payload.preferred_name.strip() if payload.preferred_name else None
    current_preferences = dict(user.preferences or {})
    current_preferences.update({
        "preferred_name": preferred or None,
        "density": payload.density,
        "reduce_motion": payload.reduce_motion,
        "timezone": payload.timezone.strip(),
    })
    user.preferences = current_preferences
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="user.preferences.updated",
        entity_type="user",
        entity_id=str(user.id),
        metadata={"density": payload.density, "reduce_motion": payload.reduce_motion, "timezone": payload.timezone.strip()},
    )
    await db.commit()
    return user.preferences

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
