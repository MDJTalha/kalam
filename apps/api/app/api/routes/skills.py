from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
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
    result = await db.execute(select(Skill).where(Skill.tenant_id == user.tenant_id).order_by(Skill.name))
    return list(result.scalars().all())

@router.post("", status_code=201)
async def create_skill(payload: SkillCreate, user: User = Depends(require_permission("skills.manage")), db: AsyncSession = Depends(get_db)):
    item = Skill(tenant_id=user.tenant_id, **payload.model_dump())
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
