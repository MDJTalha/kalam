from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ValidationError, field_validator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission
from app.core.security import utcnow
from app.db.models import Certificate, Course, Tenant, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

EXPIRING_SOON_DAYS = 30


def certificate_status(certificate: Certificate) -> str:
    if certificate.revoked_at is not None:
        return "revoked"
    if certificate.expires_at is not None:
        now = utcnow()
        if certificate.expires_at <= now:
            return "expired"
        if certificate.expires_at <= now + timedelta(days=EXPIRING_SOON_DAYS):
            return "expiring_soon"
    return "active"


def certificate_template_for_tenant(tenant: Tenant) -> dict:
    raw_template = ((tenant.settings or {}).get("certificate_template") or {})
    try:
        return CertificateTemplate.model_validate(raw_template).model_dump()
    except ValidationError:
        return CertificateTemplate().model_dump()


def certificate_template_version(tenant: Tenant) -> int:
    value = (tenant.settings or {}).get("certificate_template_version", 1)
    return value if isinstance(value, int) and value > 0 else 1

@router.get("/verify/{verification_code}")
async def verify_certificate(verification_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Certificate, Course, User, Tenant)
        .join(Course, Course.id == Certificate.course_id)
        .join(User, User.id == Certificate.user_id)
        .join(Tenant, Tenant.id == Certificate.tenant_id)
        .where(Certificate.verification_code == verification_code)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    certificate, course, user, tenant = row
    status = certificate_status(certificate)
    valid = status in {"active", "expiring_soon"}
    template = certificate_template_for_tenant(tenant)
    return {"valid": valid, "certificate_id": str(certificate.id),
            "course": course.title,
            "learner": f"{user.first_name} {user.last_name[:1]}.",
            "issued_at": certificate.issued_at, "expires_at": certificate.expires_at,
            "revoked": certificate.revoked_at is not None,
            "status": status,
            "verification_code": certificate.verification_code,
            "template": template}

@router.get("/my")
async def my_certificates(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Certificate, Course)
        .join(Course, Course.id == Certificate.course_id)
        .where(Certificate.tenant_id == user.tenant_id, Certificate.user_id == user.id)
        .order_by(Certificate.issued_at.desc())
    )
    return [
        {"id": str(cert.id), "course": course.title,
         "verification_code": cert.verification_code,
         "issued_at": cert.issued_at, "expires_at": cert.expires_at,
         "revoked": cert.revoked_at is not None, "status": certificate_status(cert)}
        for cert, course in result.all()
    ]

class CertificateRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)

class CertificateTemplate(BaseModel):
    title: str = Field(default="Certificate of Completion", min_length=3, max_length=160)
    subtitle: str = Field(default="This certifies that", min_length=3, max_length=240)
    issuer_name: str = Field(default="Corporate LMS", min_length=2, max_length=160)
    primary_color: str = Field(default="#0e4c3d", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(default="#df9d13", pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_url: str | None = Field(default=None, max_length=1000)
    footer_text: str = Field(default="Verify this credential using the verification code.", max_length=500)

    @field_validator("logo_url")
    @classmethod
    def validate_logo_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith("https://"):
            raise ValueError("logo_url must use https://")
        return value

@router.get("/templates/default")
async def get_certificate_template(
    user: User = Depends(require_permission("certificates.manage")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {**certificate_template_for_tenant(tenant), "version": certificate_template_version(tenant)}

@router.patch("/templates/default")
async def update_certificate_template(
    payload: CertificateTemplate,
    user: User = Depends(require_permission("certificates.manage")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    settings = tenant.settings or {}
    version = certificate_template_version(tenant)
    stored_history = settings.get("certificate_template_history")
    history = stored_history if isinstance(stored_history, list) else []
    history = [*history, {"version": version, "template": certificate_template_for_tenant(tenant), "updated_at": utcnow().isoformat(), "updated_by": str(user.id)}][-20:]
    tenant.settings = {**settings, "certificate_template": payload.model_dump(), "certificate_template_version": version + 1, "certificate_template_history": history}
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="certificate.template.updated", entity_type="certificate_template", entity_id="default", metadata={"title": payload.title, "version": version + 1})
    await db.commit()
    return {**payload.model_dump(), "version": version + 1}

@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: UUID,
    payload: CertificateRevoke,
    user: User = Depends(require_permission("certificates.manage")),
    db: AsyncSession = Depends(get_db),
):
    cert = await db.scalar(
        select(Certificate).where(
            Certificate.id == certificate_id, Certificate.tenant_id == user.tenant_id
        )
    )
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.revoked_at is not None:
        return {"status": "already_revoked", "certificate_id": str(cert.id)}
    cert.revoked_at = utcnow()
    cert.record_metadata = {**(cert.record_metadata or {}), "revocation_reason": payload.reason}
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="certificate.revoked", entity_type="certificate", entity_id=str(cert.id), metadata={"reason": payload.reason})
    await db.commit()
    return {"status": "revoked", "certificate_id": str(cert.id)}

class CertificateLifecycle(BaseModel):
    action: str = Field(pattern='^(renew|set_expiry)$')
    expires_at: datetime | None = None
    reason: str = Field(min_length=3, max_length=2000)

@router.get('/admin')
async def admin_certificates(
    user: User = Depends(require_permission('certificates.manage')),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Certificate, Course, User)
        .join(Course, Course.id == Certificate.course_id)
        .join(User, User.id == Certificate.user_id)
        .where(Certificate.tenant_id == user.tenant_id)
        .order_by(Certificate.issued_at.desc())
    )
    return [
        {
            'id': str(cert.id),
            'learner_id': str(cert.user_id),
            'learner': f'{person.first_name} {person.last_name}',
            'course_id': str(cert.course_id),
            'course': course.title,
            'verification_code': cert.verification_code,
            'issued_at': cert.issued_at,
            'expires_at': cert.expires_at,
            'revoked': cert.revoked_at is not None,
            'status': certificate_status(cert),
            'metadata': cert.record_metadata,
        }
        for cert, course, person in result.all()
    ]

@router.patch('/{certificate_id}/lifecycle')
async def certificate_lifecycle(
    certificate_id: UUID,
    payload: CertificateLifecycle,
    user: User = Depends(require_permission('certificates.manage')),
    db: AsyncSession = Depends(get_db),
):
    cert = await db.scalar(select(Certificate).where(Certificate.id == certificate_id, Certificate.tenant_id == user.tenant_id))
    if cert is None:
        raise HTTPException(status_code=404, detail='Certificate not found')
    if cert.revoked_at is not None:
        raise HTTPException(status_code=409, detail='Revoked certificates cannot be renewed')
    expiry = payload.expires_at
    if payload.action == "renew" and expiry is None:
        from datetime import timedelta
        expiry = utcnow() + timedelta(days=365)
    if expiry is None or expiry <= utcnow():
        raise HTTPException(status_code=422, detail='expires_at must be a future timestamp')
    cert.expires_at = expiry
    cert.record_metadata = {**(cert.record_metadata or {}), 'lifecycle_reason': payload.reason, 'lifecycle_action': payload.action}
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action='certificate.renewed' if payload.action == 'renew' else 'certificate.expiry.updated', entity_type='certificate', entity_id=str(cert.id), metadata={'reason': payload.reason, 'expires_at': expiry.isoformat()})
    await db.commit()
    return {'id': str(cert.id), 'status': certificate_status(cert), 'expires_at': cert.expires_at}
