from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import DevelopmentPlan, Role, User, UserRole
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class Goal(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    target_date: str | None = None
    status: str = Field(default="planned", pattern=r"^(planned|in_progress|completed|cancelled)$")
    notes: str | None = None

class DevelopmentPlanCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    goals: list[Goal] = Field(default_factory=list)

class DevelopmentPlanUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    status: str | None = Field(default=None, pattern=r"^(active|completed|cancelled)$")
    goals: list[Goal] | None = None

@router.get("/my")
async def my_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DevelopmentPlan)
        .where(
            DevelopmentPlan.tenant_id == user.tenant_id,
            DevelopmentPlan.user_id == user.id,
        )
        .order_by(DevelopmentPlan.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "status": item.status,
            "goals": item.goals,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in result.scalars().all()
    ]

@router.post("/my", status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: DevelopmentPlanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = DevelopmentPlan(
        tenant_id=user.tenant_id,
        user_id=user.id,
        title=payload.title,
        goals=[goal.model_dump() for goal in payload.goals],
    )
    db.add(item)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="development.plan.created",
        entity_type="development_plan",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"id": str(item.id), "title": item.title, "status": item.status}

@router.patch("/my/{plan_id}")
async def update_plan(
    plan_id: UUID,
    payload: DevelopmentPlanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.scalar(
        select(DevelopmentPlan).where(
            DevelopmentPlan.id == plan_id,
            DevelopmentPlan.tenant_id == user.tenant_id,
            DevelopmentPlan.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Development plan not found")

    values = payload.model_dump(exclude_unset=True)
    if "title" in values:
        item.title = values["title"]
    if "status" in values:
        item.status = values["status"]
    if "goals" in values:
        item.goals = [goal.model_dump() if isinstance(goal, Goal) else goal for goal in payload.goals or []]

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="development.plan.updated",
        entity_type="development_plan",
        entity_id=str(item.id),
    )
    await db.commit()
    return {"id": str(item.id), "title": item.title, "status": item.status, "goals": item.goals}

@router.get("/users/{user_id}")
async def user_plans(
    user_id: UUID,
    manager: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(
        select(User).where(User.id == user_id, User.tenant_id == manager.tenant_id)
    )
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.manager_id != manager.id and manager.id != target.id:
        admin_role = await db.scalar(
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == manager.id,
                Role.tenant_id == manager.tenant_id,
                Role.name == "Tenant Admin",
            )
        )
        if admin_role is None:
            raise HTTPException(status_code=403, detail="Manager scope does not include this user")

    result = await db.execute(
        select(DevelopmentPlan)
        .where(
            DevelopmentPlan.tenant_id == manager.tenant_id,
            DevelopmentPlan.user_id == target.id,
        )
        .order_by(DevelopmentPlan.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "status": item.status,
            "goals": item.goals,
        }
        for item in result.scalars().all()
    ]
