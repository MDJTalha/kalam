from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.db.models import Course, CourseModule, Enrollment, Lesson, Tenant, User
from app.db.session import SessionLocal
from app.services.ai_retrieval import retrieve_authorized_sources


@pytest.mark.asyncio
async def test_retrieval_ranks_exact_relevant_lesson_ahead_of_distractor():
    token = uuid4().hex[:8]
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "demo-corporation"))
        learner = await db.scalar(
            select(User).where(User.tenant_id == tenant.id, User.email == "learner@demo.corp")
        )
        course = Course(
            tenant_id=tenant.id,
            title=f"Retrieval Quality {token}",
            slug=f"retrieval-quality-{token}",
            description="Controlled Phase 7 retrieval benchmark.",
            status="published",
            visibility="tenant",
            enrollment_policy="open",
        )
        db.add(course)
        await db.flush()
        module = CourseModule(course_id=course.id, title="Benchmark module", position=1)
        db.add(module)
        await db.flush()
        relevant = Lesson(
            module_id=module.id,
            title="Workplace conflict resolution",
            content_type="rich_text",
            content={"text": "Conflict resolution uses active listening, de-escalation, and collaborative problem solving."},
            position=1,
        )
        distractor = Lesson(
            module_id=module.id,
            title="Spreadsheet formulas",
            content_type="rich_text",
            content={"text": "Spreadsheet formulas cover SUM, AVERAGE, references, and worksheet calculations."},
            position=2,
        )
        db.add_all([relevant, distractor])
        db.add(
            Enrollment(
                tenant_id=tenant.id,
                course_id=course.id,
                user_id=learner.id,
                status="active",
                source="phase7_test",
            )
        )
        await db.commit()
        sources = await retrieve_authorized_sources(
            learner,
            db,
            "How should I handle workplace conflict resolution using active listening?",
            str(course.id),
            top_k=4,
        )
        assert sources
        assert sources[0].lesson_id == str(relevant.id)
        assert sources[0].score > 0
        assert all(source.course_id == str(course.id) for source in sources)
        assert not any(source.lesson_id == str(distractor.id) and source.score == 0 for source in sources)

        await db.execute(delete(Enrollment).where(Enrollment.course_id == course.id))
        await db.execute(delete(Lesson).where(Lesson.module_id == module.id))
        await db.execute(delete(CourseModule).where(CourseModule.id == module.id))
        await db.execute(delete(Course).where(Course.id == course.id))
        await db.commit()
