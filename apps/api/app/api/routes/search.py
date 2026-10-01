from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, user_has_permission
from app.db.models import Course, Enrollment, Program, Skill, User
from app.db.session import get_db

router = APIRouter()


@router.get("")
async def global_search(
    q: str = Query(min_length=2, max_length=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="Search needs at least two non-space characters")
    term = f"%{query}%"
    can_manage_courses = await user_has_permission(user, db, "courses.manage")
    can_read_users = await user_has_permission(user, db, "users.read")
    assigned_course_ids = select(Enrollment.course_id).where(
        Enrollment.tenant_id == user.tenant_id,
        Enrollment.user_id == user.id,
    )
    courses = await db.execute(
        select(Course).where(
            Course.tenant_id == user.tenant_id,
            Course.status == "published",
            or_(Course.visibility == "tenant", Course.id.in_(assigned_course_ids)),
            or_(Course.title.ilike(term), Course.description.ilike(term)),
        ).limit(10)
    )
    people = await db.execute(
        select(User).where(
            User.tenant_id == user.tenant_id,
            or_(User.first_name.ilike(term), User.last_name.ilike(term), User.email.ilike(term)),
        ).limit(10)
    ) if can_read_users else None
    skills = await db.execute(
        select(Skill).where(
            Skill.tenant_id == user.tenant_id,
            or_(Skill.name.ilike(term), Skill.description.ilike(term)),
        ).limit(10)
    )
    program_query = select(Program).where(
        Program.tenant_id == user.tenant_id,
        or_(Program.title.ilike(term), Program.description.ilike(term)),
    )
    if not can_manage_courses:
        program_query = program_query.where(Program.status == "published")
    programs = await db.execute(program_query.limit(10))
    return {
        "query": query,
        "courses": [{"id": str(item.id), "title": item.title} for item in courses.scalars().all()],
        "people": [{"id": str(item.id), "name": f"{item.first_name} {item.last_name}", "email": item.email} for item in people.scalars().all()] if people is not None else [],
        "skills": [{"id": str(item.id), "name": item.name} for item in skills.scalars().all()],
        "programs": [{"id": str(item.id), "title": item.title} for item in programs.scalars().all()],
    }
