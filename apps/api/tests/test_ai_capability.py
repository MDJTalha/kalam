from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.db.models import Course, CourseSkill, Role, RoleSkillRequirement, Skill, Tenant, User, UserRole, UserSkill
from app.db.session import SessionLocal
from app.services.ai_retrieval import retrieve_capability_sources


@pytest.mark.asyncio
async def test_capability_sources_are_tenant_scoped_and_gap_grounded():
    token = uuid4().hex[:10]
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "demo-corporation"))
        learner = await db.scalar(
            select(User).where(User.tenant_id == tenant.id, User.email == "learner@demo.corp")
        )
        role_id = await db.scalar(
            select(UserRole.role_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == learner.id, Role.name == "Learner")
        )
        course = await db.scalar(
            select(Course).where(
                Course.tenant_id == tenant.id,
                Course.status == "published",
                Course.visibility == "tenant",
            ).limit(1)
        )
        skill = Skill(
            tenant_id=tenant.id,
            name=f"Phase7 Capability {token}",
            description="Controlled Phase 7 capability evidence.",
            category="QA",
        )
        db.add(skill)
        await db.flush()
        db.add_all([
            RoleSkillRequirement(role_id=role_id, skill_id=skill.id, required_proficiency=4),
            UserSkill(user_id=learner.id, skill_id=skill.id, proficiency=1, evidence_source="phase7_test"),
            CourseSkill(course_id=course.id, skill_id=skill.id, target_proficiency=4),
        ])
        await db.commit()

        sources = await retrieve_capability_sources(learner, db)
        source = next(item for item in sources if item.lesson_id == str(skill.id))
        assert source.score == 3.0
        assert "Current proficiency: 1" in source.text
        assert "Required proficiency: 4" in source.text
        assert course.title in source.text
        assert "must not be used as an employment decision" in source.text

        await db.execute(delete(CourseSkill).where(CourseSkill.skill_id == skill.id))
        await db.execute(delete(RoleSkillRequirement).where(RoleSkillRequirement.skill_id == skill.id))
        await db.execute(delete(UserSkill).where(UserSkill.skill_id == skill.id))
        await db.execute(delete(Skill).where(Skill.id == skill.id))
        await db.commit()
