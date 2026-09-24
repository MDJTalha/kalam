from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission
from app.db.models import User
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_people(user: User = Depends(require_permission("users.read")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User.id, User.email, User.first_name, User.last_name, User.employee_number, User.job_title, User.is_active)
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
    return [
        {
            "id": str(item.id),
            "email": item.email,
            "first_name": item.first_name,
            "last_name": item.last_name,
            "employee_number": item.employee_number,
            "job_title": item.job_title,
        }
        for item in result.scalars().all()
    ]
