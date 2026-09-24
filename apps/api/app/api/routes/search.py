from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Course, Program, Skill, User
from app.db.session import get_db

router = APIRouter()


@router.get("")
async def global_search(
    q: str = Query(min_length=2, max_length=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    term = f"%{q.strip()}%"
    courses = await db.execute(
        select(Course).where(
            Course.tenant_id == user.tenant_id,
            Course.status == "published",
            or_(Course.title.ilike(term), Course.description.ilike(term)),
        ).limit(10)
    )
    people = await db.execute(
        select(User).where(
            User.tenant_id == user.tenant_id,
            or_(User.first_name.ilike(term), User.last_name.ilike(term), User.email.ilike(term)),
        ).limit(10)
    )
    skills = await db.execute(
        select(Skill).where(
            Skill.tenant_id == user.tenant_id,
            or_(Skill.name.ilike(term), Skill.description.ilike(term)),
        ).limit(10)
    )
    programs = await db.execute(
        select(Program).where(
            Program.tenant_id == user.tenant_id,
            or_(Program.title.ilike(term), Program.description.ilike(term)),
        ).limit(10)
    )
    return {
        "query": q.strip(),
        "courses": [{"id": str(item.id), "title": item.title} for item in courses.scalars().all()],
        "people": [{"id": str(item.id), "name": f"{item.first_name} {item.last_name}", "email": item.email} for item in people.scalars().all()],
        "skills": [{"id": str(item.id), "name": item.name} for item in skills.scalars().all()],
        "programs": [{"id": str(item.id), "title": item.title} for item in programs.scalars().all()],
    }
