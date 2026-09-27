from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission
from app.db.models import User, Role, UserRole, OrgUnit, Enrollment, ComplianceAssignment, DevelopmentPlan
from app.db.session import get_db
from app.core.security import utcnow

router = APIRouter()

@router.get("")
async def list_people(user: User = Depends(require_permission("users.read")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User.id, User.email, User.first_name, User.last_name, User.employee_number, User.job_title, User.manager_id, User.org_unit_id, User.is_active)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.last_name.asc(), User.first_name.asc())
    )
    return [
        {
            "id": str(row.id),
            "email": row.email,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "employee_number": row.employee_number,
            "job_title": row.job_title,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "org_unit_id": str(row.org_unit_id) if row.org_unit_id else None,
            "is_active": row.is_active,
        }
        for row in result.all()
    ]

@router.get("/me")
async def profile(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "employee_number": user.employee_number,
        "job_title": user.job_title,
        "manager_id": str(user.manager_id) if user.manager_id else None,
        "org_unit_id": str(user.org_unit_id) if user.org_unit_id else None,
    }


@router.get("/team")
async def team(
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(
            User.tenant_id == user.tenant_id,
            User.manager_id == user.id,
            User.is_active.is_(True),
        )
        .order_by(User.last_name, User.first_name)
    )
    members = result.scalars().all()
    if not members:
        return []
    ids = [item.id for item in members]
    now = utcnow()
    learning_result = await db.execute(
        select(
            Enrollment.user_id,
            func.count().filter(Enrollment.status == "completed"),
            func.count().filter(Enrollment.status.notin_(["completed", "declined"])),
            func.count().filter(Enrollment.due_at < now, Enrollment.status.notin_(["completed", "declined"])),
        ).where(Enrollment.tenant_id == user.tenant_id, Enrollment.user_id.in_(ids))
        .group_by(Enrollment.user_id)
    )
    learning = {row[0]: row[1:] for row in learning_result.all()}
    compliance_result = await db.execute(
        select(
            ComplianceAssignment.user_id,
            func.count().filter(ComplianceAssignment.status != "completed"),
            func.count().filter(ComplianceAssignment.due_at < now, ComplianceAssignment.status != "completed"),
        ).where(ComplianceAssignment.tenant_id == user.tenant_id, ComplianceAssignment.user_id.in_(ids))
        .group_by(ComplianceAssignment.user_id)
    )
    compliance = {row[0]: row[1:] for row in compliance_result.all()}
    plans_result = await db.execute(
        select(DevelopmentPlan.user_id, func.count())
        .where(DevelopmentPlan.tenant_id == user.tenant_id, DevelopmentPlan.user_id.in_(ids), DevelopmentPlan.status != "completed")
        .group_by(DevelopmentPlan.user_id)
    )
    plans = {row[0]: row[1] for row in plans_result.all()}
    return [
        {
            "id": str(item.id),
            "email": item.email,
            "first_name": item.first_name,
            "last_name": item.last_name,
            "employee_number": item.employee_number,
            "job_title": item.job_title,
            "completed_learning": learning.get(item.id, (0, 0, 0))[0],
            "open_learning": learning.get(item.id, (0, 0, 0))[1],
            "overdue_learning": learning.get(item.id, (0, 0, 0))[2],
            "open_compliance": compliance.get(item.id, (0, 0))[0],
            "overdue_compliance": compliance.get(item.id, (0, 0))[1],
            "active_plans": plans.get(item.id, 0),
        }
        for item in members
    ]

@router.get("/{person_id}")
async def person_detail(
    person_id: UUID,
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    person = await db.scalar(select(User).where(User.id == person_id, User.tenant_id == user.tenant_id))
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    role_result = await db.execute(
        select(Role.name).join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == person.id, Role.tenant_id == user.tenant_id)
        .order_by(Role.name)
    )
    unit = await db.scalar(select(OrgUnit).where(OrgUnit.id == person.org_unit_id, OrgUnit.tenant_id == user.tenant_id)) if person.org_unit_id else None
    manager = await db.scalar(select(User).where(User.id == person.manager_id, User.tenant_id == user.tenant_id)) if person.manager_id else None
    return {
        "id": str(person.id), "first_name": person.first_name, "last_name": person.last_name,
        "email": person.email, "employee_number": person.employee_number,
        "job_title": person.job_title, "is_active": person.is_active,
        "org_unit_id": str(unit.id) if unit else None, "org_unit": unit.name if unit else None,
        "manager_id": str(manager.id) if manager else None,
        "manager": f"{manager.first_name} {manager.last_name}" if manager else None,
        "roles": list(role_result.scalars().all()),
    }
