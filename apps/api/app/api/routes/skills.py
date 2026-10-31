from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_permission
from app.db.models import Course, CourseSkill, Role, RoleSkillRequirement, Skill, User, UserSkill
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()

class SkillCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    category: str | None = None

class UserSkillCreate(BaseModel):
    user_id: UUID
    skill_id: UUID
    proficiency: int = Field(ge=1, le=5)
    evidence_source: str | None = None

@router.get("")
async def list_skills(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Skill).where(Skill.tenant_id == user.tenant_id).order_by(Skill.name).limit(100)
    )
    return list(result.scalars().all())


@router.get("/page")
async def page_skills(
    q: str | None = None,
    page: int = Field(default=1, ge=1),
    page_size: int = Field(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Skill.tenant_id == user.tenant_id]
    if q and q.strip():
        filters.append(Skill.name.ilike(f"%{q.strip()}%"))
    total = int(await db.scalar(select(func.count(Skill.id)).where(*filters)) or 0)
    result = await db.execute(
        select(Skill).where(*filters).order_by(Skill.name).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "items": list(result.scalars().all()),
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.post("", status_code=201)
async def create_skill(payload: SkillCreate, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Skill name must have at least two characters")
    existing = await db.scalar(select(Skill.id).where(Skill.tenant_id == user.tenant_id, Skill.name.ilike(name)))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A skill with this name already exists")
    item = Skill(tenant_id=user.tenant_id, name=name, category=payload.category.strip() if payload.category else None, description=payload.description.strip() if payload.description else None)
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.created", entity_type="skill", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "name": item.name}

@router.get("/me")
async def my_skills(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSkill, Skill).join(Skill, Skill.id == UserSkill.skill_id).where(UserSkill.user_id == user.id, Skill.tenant_id == user.tenant_id).order_by(Skill.name))
    return [{"id": str(us.id), "skill": skill.name, "proficiency": us.proficiency, "evidence_source": us.evidence_source} for us, skill in result.all()]

@router.post("/evidence", status_code=201)
async def record_skill_evidence(payload: UserSkillCreate, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    learner = await db.scalar(select(User).where(User.id == payload.user_id, User.tenant_id == user.tenant_id))
    skill = await db.scalar(select(Skill).where(Skill.id == payload.skill_id, Skill.tenant_id == user.tenant_id))
    if learner is None or skill is None:
        raise HTTPException(status_code=404, detail="User or skill not found")
    item = await db.scalar(select(UserSkill).where(UserSkill.user_id == learner.id, UserSkill.skill_id == skill.id))
    if item is None:
        item = UserSkill(user_id=learner.id, skill_id=skill.id, proficiency=payload.proficiency, evidence_source=payload.evidence_source)
        db.add(item)
    else:
        item.proficiency = payload.proficiency
        item.evidence_source = payload.evidence_source
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.evidence.recorded", entity_type="user_skill", entity_id=str(item.id))
    await db.commit()
    return {"status": "recorded", "user_id": str(learner.id), "skill_id": str(skill.id), "proficiency": item.proficiency}


class CourseSkillMap(BaseModel):
    course_id: UUID
    skill_id: UUID
    target_proficiency: int = Field(ge=1, le=5)

class RoleSkillMap(BaseModel):
    role_id: UUID
    skill_id: UUID
    required_proficiency: int = Field(ge=1, le=5)

@router.post("/course-mapping", status_code=201)
async def map_course_skill(
    payload: CourseSkillMap,
    user: User = Depends(require_permission("skills.manage")),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == payload.course_id, Course.tenant_id == user.tenant_id))
    skill = await db.scalar(select(Skill).where(Skill.id == payload.skill_id, Skill.tenant_id == user.tenant_id))
    if course is None or skill is None:
        raise HTTPException(status_code=404, detail="Course or skill not found")
    item = await db.scalar(select(CourseSkill).where(
        CourseSkill.course_id == course.id,
        CourseSkill.skill_id == skill.id,
    ))
    if item is None:
        item = CourseSkill(course_id=course.id, skill_id=skill.id, target_proficiency=payload.target_proficiency)
        db.add(item)
    else:
        item.target_proficiency = payload.target_proficiency
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.course_mapping.saved", entity_type="course_skill", entity_id=str(course.id), metadata={"skill_id": str(skill.id)})
    await db.commit()
    return {"status": "mapped", "course_id": str(course.id), "skill_id": str(skill.id), "target_proficiency": item.target_proficiency}

@router.get("/course/{course_id}")
async def get_course_skills(
    course_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.tenant_id == user.tenant_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    result = await db.execute(
        select(CourseSkill, Skill)
        .join(Skill, Skill.id == CourseSkill.skill_id)
        .where(CourseSkill.course_id == course.id, Skill.tenant_id == user.tenant_id)
        .order_by(Skill.name)
    )
    return [
        {"skill_id": str(item.skill_id), "skill": skill.name, "target_proficiency": item.target_proficiency}
        for item, skill in result.all()
    ]

@router.post("/role-mapping", status_code=201)
async def map_role_skill(
    payload: RoleSkillMap,
    user: User = Depends(require_permission("skills.manage")),
    db: AsyncSession = Depends(get_db),
):
    role = await db.scalar(select(Role).where(Role.id == payload.role_id, Role.tenant_id == user.tenant_id))
    skill = await db.scalar(select(Skill).where(Skill.id == payload.skill_id, Skill.tenant_id == user.tenant_id))
    if role is None or skill is None:
        raise HTTPException(status_code=404, detail="Role or skill not found")
    item = await db.scalar(select(RoleSkillRequirement).where(
        RoleSkillRequirement.role_id == role.id,
        RoleSkillRequirement.skill_id == skill.id,
    ))
    if item is None:
        item = RoleSkillRequirement(role_id=role.id, skill_id=skill.id, required_proficiency=payload.required_proficiency)
        db.add(item)
    else:
        item.required_proficiency = payload.required_proficiency
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.role_mapping.saved", entity_type="role_skill_requirement", entity_id=str(role.id), metadata={"skill_id": str(skill.id)})
    await db.commit()
    return {"status": "mapped", "role_id": str(role.id), "skill_id": str(skill.id), "required_proficiency": item.required_proficiency}

@router.get("/role/{role_id}/gaps")
async def get_role_skill_gaps(
    role_id: UUID,
    target_user_id: UUID | None = None,
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """Return role-required competencies and learner gaps on a 1-5 proficiency scale."""
    role = await db.scalar(select(Role).where(Role.id == role_id, Role.tenant_id == user.tenant_id))
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    target = user if target_user_id is None else await db.scalar(
        select(User).where(User.id == target_user_id, User.tenant_id == user.tenant_id, User.is_active.is_(True))
    )
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    required = await db.execute(
        select(RoleSkillRequirement, Skill)
        .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
        .where(RoleSkillRequirement.role_id == role.id, Skill.tenant_id == user.tenant_id)
        .order_by(Skill.name)
    )
    actual_rows = await db.execute(
        select(UserSkill, Skill)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id == target.id, Skill.tenant_id == user.tenant_id)
    )
    actual = {skill.id: item.proficiency for item, skill in actual_rows.all()}
    gaps = []
    for requirement, skill in required.all():
        current = actual.get(skill.id, 0)
        gaps.append({
            "skill_id": str(skill.id),
            "skill": skill.name,
            "required_proficiency": requirement.required_proficiency,
            "current_proficiency": current,
            "gap": max(0, requirement.required_proficiency - current),
            "met": current >= requirement.required_proficiency,
        })
    return {
        "role_id": str(role.id),
        "role": role.name,
        "user_id": str(target.id),
        "skills": gaps,
        "gap_count": sum(1 for item in gaps if item["gap"] > 0),
    }


@router.get("/role/{role_id}")
async def get_role_skills(
    role_id: UUID,
    user: User = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    role = await db.scalar(select(Role).where(Role.id == role_id, Role.tenant_id == user.tenant_id))
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    result = await db.execute(
        select(RoleSkillRequirement, Skill)
        .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
        .where(RoleSkillRequirement.role_id == role.id, Skill.tenant_id == user.tenant_id)
        .order_by(Skill.name)
    )
    return [
        {"skill_id": str(item.skill_id), "skill": skill.name, "required_proficiency": item.required_proficiency}
        for item, skill in result.all()
    ]


@router.get("/governance")
async def skill_governance(user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    role_rows = await db.execute(select(RoleSkillRequirement, Role, Skill).join(Role, Role.id == RoleSkillRequirement.role_id).join(Skill, Skill.id == RoleSkillRequirement.skill_id).where(Role.tenant_id == user.tenant_id, Skill.tenant_id == user.tenant_id).order_by(Role.name, Skill.name))
    course_rows = await db.execute(select(CourseSkill, Course, Skill).join(Course, Course.id == CourseSkill.course_id).join(Skill, Skill.id == CourseSkill.skill_id).where(Course.tenant_id == user.tenant_id, Skill.tenant_id == user.tenant_id).order_by(Course.title, Skill.name))
    return {
        "role_requirements": [{"role_id": str(role.id), "role": role.name, "skill_id": str(skill.id), "skill": skill.name, "required_proficiency": mapping.required_proficiency} for mapping, role, skill in role_rows.all()],
        "course_mappings": [{"course_id": str(course.id), "course": course.title, "skill_id": str(skill.id), "skill": skill.name, "target_proficiency": mapping.target_proficiency} for mapping, course, skill in course_rows.all()],
    }

@router.delete("/role-mapping/{role_id}/{skill_id}", status_code=204)
async def delete_role_mapping(role_id: UUID, skill_id: UUID, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(RoleSkillRequirement).join(Role, Role.id == RoleSkillRequirement.role_id).join(Skill, Skill.id == RoleSkillRequirement.skill_id).where(RoleSkillRequirement.role_id == role_id, RoleSkillRequirement.skill_id == skill_id, Role.tenant_id == user.tenant_id, Skill.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Role requirement not found")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.role_mapping.deleted", entity_type="role_skill_requirement", entity_id=str(role_id), metadata={"skill_id": str(skill_id)})
    await db.commit()

@router.delete("/course-mapping/{course_id}/{skill_id}", status_code=204)
async def delete_course_mapping(course_id: UUID, skill_id: UUID, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(CourseSkill).join(Course, Course.id == CourseSkill.course_id).join(Skill, Skill.id == CourseSkill.skill_id).where(CourseSkill.course_id == course_id, CourseSkill.skill_id == skill_id, Course.tenant_id == user.tenant_id, Skill.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Course mapping not found")
    await db.delete(item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.course_mapping.deleted", entity_type="course_skill", entity_id=str(course_id), metadata={"skill_id": str(skill_id)})
    await db.commit()

@router.get("/me/gaps")
async def my_role_gaps(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.db.models import UserRole
    requirements = await db.execute(select(Role, Skill, RoleSkillRequirement.required_proficiency).join(UserRole, UserRole.role_id == Role.id).join(RoleSkillRequirement, RoleSkillRequirement.role_id == Role.id).join(Skill, Skill.id == RoleSkillRequirement.skill_id).where(UserRole.user_id == user.id, Role.tenant_id == user.tenant_id, Skill.tenant_id == user.tenant_id).order_by(Role.name, Skill.name))
    actual_rows = await db.execute(select(UserSkill.skill_id, UserSkill.proficiency).join(Skill, Skill.id == UserSkill.skill_id).where(UserSkill.user_id == user.id, Skill.tenant_id == user.tenant_id))
    actual: dict[UUID, int] = {
        skill_id: proficiency for skill_id, proficiency in actual_rows.all()
    }
    return [{"role": role.name, "role_id": str(role.id), "skill": skill.name, "skill_id": str(skill.id), "required_proficiency": required, "current_proficiency": actual.get(skill.id, 0), "gap": max(0, required - actual.get(skill.id, 0))} for role, skill, required in requirements.all()]

class SkillUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    category: str | None = Field(default=None, max_length=120)

@router.patch("/{skill_id}")
async def update_skill(skill_id: UUID, payload: SkillUpdate, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(Skill).where(Skill.id == skill_id, Skill.tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Skill name must have at least two characters")
    duplicate = await db.scalar(select(Skill.id).where(Skill.tenant_id == user.tenant_id, Skill.id != skill_id, Skill.name.ilike(name)))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="A skill with this name already exists")
    before = {"name": item.name, "category": item.category, "description": item.description}
    item.name = name
    item.category = payload.category.strip() if payload.category else None
    item.description = payload.description.strip() if payload.description else None
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="skill.updated", entity_type="skill", entity_id=str(item.id), metadata={"before": before, "after": {"name": item.name, "category": item.category, "description": item.description}})
    await db.commit()
    return {"id": str(item.id), "name": item.name, "category": item.category, "description": item.description}
