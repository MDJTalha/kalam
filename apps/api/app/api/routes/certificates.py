from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission
from app.core.security import utcnow
from app.db.models import Certificate, Course, User
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

@router.get("/verify/{verification_code}")
async def verify_certificate(verification_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Certificate, Course, User)
        .join(Course, Course.id == Certificate.course_id)
        .join(User, User.id == Certificate.user_id)
        .where(Certificate.verification_code == verification_code)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    certificate, course, user = row
    valid = certificate.revoked_at is None and (
        certificate.expires_at is None or certificate.expires_at > utcnow()
    )
    return {"valid": valid, "certificate_id": str(certificate.id),
            "course": course.title,
            "learner": f"{user.first_name} {user.last_name}",
            "issued_at": certificate.issued_at, "expires_at": certificate.expires_at,
            "revoked": certificate.revoked_at is not None}

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
         "revoked": cert.revoked_at is not None}
        for cert, course in result.all()
    ]

@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: UUID,
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
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id,
                action="certificate.revoked", entity_type="certificate", entity_id=str(cert.id))
    await db.commit()
    return {"status": "revoked", "certificate_id": str(cert.id)}
