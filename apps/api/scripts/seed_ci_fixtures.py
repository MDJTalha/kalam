"""Create deterministic demo records required by API integration tests."""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models import (  # noqa: E402
    AIGovernancePolicy,
    Assessment,
    ComplianceAssignment,
    ComplianceRequirement,
    Course,
    CourseModule,
    Enrollment,
    Lesson,
    Permission,
    Question,
    Role,
    RolePermission,
    Skill,
    Tenant,
    User,
    UserRole,
)
from app.db.session import SessionLocal  # noqa: E402

PASSWORD = os.getenv("CI_FIXTURE_PASSWORD", "DemoOnly!1234")


def validate_seed_target() -> None:
    """Restrict credential-mutating fixture seeding to explicit test/CI environments."""
    from sqlalchemy.engine import make_url

    if settings.app_env.lower() not in {"test", "ci"}:
        raise RuntimeError("Refusing to seed CI fixtures unless APP_ENV is test or ci.")
    explicit_test_url = os.getenv("KALAM_TEST_DATABASE_URL", "")
    if not explicit_test_url:
        raise RuntimeError("Refusing to seed CI fixtures without an explicit KALAM_TEST_DATABASE_URL.")
    database = make_url(settings.database_url)
    explicit_database = make_url(explicit_test_url)
    if not database.drivername.startswith("postgresql"):
        raise RuntimeError("Refusing to seed CI fixtures into a non-PostgreSQL database.")
    if database.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Refusing to seed CI fixtures into a non-local database target.")
    if database.render_as_string(hide_password=True) != explicit_database.render_as_string(hide_password=True):
        raise RuntimeError("DATABASE_URL must match the explicitly designated KALAM_TEST_DATABASE_URL.")
    if not explicit_database.drivername.startswith("postgresql") or explicit_database.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("KALAM_TEST_DATABASE_URL must point to a local PostgreSQL test service.")
    if not PASSWORD or (PASSWORD == "DemoOnly!1234" and os.getenv("CI_FIXTURE_PASSWORD") is None):
        raise RuntimeError("Set CI_FIXTURE_PASSWORD explicitly before seeding test credentials.")


PERMISSIONS = [
    "tenant.read", "tenant.manage", "users.read", "users.manage", "users.team.read",
    "users.invite.learning_roles", "roles.manage", "courses.read", "courses.manage",
    "courses.assign_team", "development.team.read", "development.team.manage", "learning.access", "assessments.manage", "certificates.manage", "compliance.manage",
    "skills.manage", "development.manage", "reports.read", "reports.team.read",
    "reports.manage", "audit.read", "files.read", "files.manage", "integrations.manage",
    "ai.manage", "capabilities.manage", "capabilities.read",
    "capability_assessments.manage", "capability_assessments.read",
    "capability_assessments.execute", "reassessment.manage", "competencies.manage",
    "competencies.read", "role_requirements.manage", "role_requirements.read",
    "strategic_objectives.manage", "strategic_objectives.read", "capability_gaps.manage",
    "capability_gaps.read", "capability_risk.manage", "capability_risk.read",
    "evidence.manage", "evidence.read", "evidence.verify",
    "development.recommendations.read", "development.recommendations.manage",
]
ROLE_PERMISSIONS = {
    "Tenant Administrator": PERMISSIONS,
    "Manager": ["users.team.read", "courses.read", "courses.assign_team", "learning.access", "reports.team.read", "development.team.read", "development.team.manage", "capabilities.read"],
    "Instructor": ["courses.read", "courses.manage", "learning.access", "assessments.manage"],
    "Learner": ["courses.read", "learning.access", "development.manage", "capability_assessments.read", "capability_assessments.execute"],
}


async def one_or_create(session, model, where, values):
    obj = (await session.execute(select(model).filter_by(**where))).scalar_one_or_none()
    if obj is None:
        obj = model(**where, **values)
        session.add(obj)
        await session.flush()
    return obj


async def seed():
    validate_seed_target()
    async with SessionLocal() as session:
        tenants = {}
        for slug, name in (("demo-corporation", "Demo Corporation"), ("isolation-corporation", "Isolation Corporation")):
            tenants[slug] = await one_or_create(session, Tenant, {"slug": slug}, {"name": name, "status": "active"})

        perms = {}
        for key in PERMISSIONS:
            perms[key] = await one_or_create(session, Permission, {"key": key}, {"description": key.replace(".", " ")})

        users = {}
        demo_users = [
            ("admin@demo.corp", "Demo", "Administrator", "Tenant Administrator"),
            ("manager@demo.corp", "Demo", "Manager", "Manager"),
            ("instructor@demo.corp", "Demo", "Instructor", "Instructor"),
            ("learner@demo.corp", "Demo", "Learner", "Learner"),
        ]
        for slug, tenant in tenants.items():
            names = demo_users if slug == "demo-corporation" else [("isolated@other.corp", "Isolated", "Learner", "Learner")]
            for role_name in sorted({row[3] for row in names}):
                role = await one_or_create(
                    session,
                    Role,
                    {"tenant_id": tenant.id, "name": role_name},
                    {"description": f"CI fixture role: {role_name}", "role_kind": "predefined"},
                )
                if settings.app_env.lower() in {"test", "ci"}:
                    # These reserved CI fixture identities model built-in roles,
                    # not tenant-created custom roles. Preserve the same role
                    # governance boundary as production predefined roles.
                    role.role_kind = "predefined"
                    # The CI fixture role matrix is intentionally authoritative:
                    # remove stale grants so a role change cannot leave broader
                    # permissions behind on a repeated seed.
                    await session.execute(
                        delete(RolePermission).where(RolePermission.role_id == role.id)
                    )
                for key in ROLE_PERMISSIONS[role_name]:
                    link = (await session.execute(select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == perms[key].id))).scalar_one_or_none()
                    if link is None:
                        session.add(RolePermission(role_id=role.id, permission_id=perms[key].id))
            for email, first, last, role_name in names:
                user = await one_or_create(session, User, {"tenant_id": tenant.id, "email": email}, {"password_hash": hash_password(PASSWORD), "first_name": first, "last_name": last, "job_title": role_name, "is_active": True})
                if settings.app_env.lower() in {"test", "ci"}:
                    user.password_hash = hash_password(PASSWORD)
                    user.first_name = first
                    user.last_name = last
                    user.job_title = role_name
                    user.is_active = True
                    user.failed_login_count = 0
                    user.locked_until = None
                users[email] = user
                role = (await session.execute(select(Role).where(Role.tenant_id == tenant.id, Role.name == role_name))).scalar_one()
                if settings.app_env.lower() in {"test", "ci"}:
                    # Tests mutate role assignments; reseeding must restore exactly the
                    # fixture role so reruns cannot accidentally grant stale privileges.
                    await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
                session.add(UserRole(user_id=user.id, role_id=role.id))

        users["learner@demo.corp"].manager_id = users["manager@demo.corp"].id
        tenant = tenants["demo-corporation"]
        course = await one_or_create(session, Course, {"tenant_id": tenant.id, "slug": "workplace-ethics-2026"}, {"title": "Workplace Ethics & Responsible Conduct", "description": "CI fixture course", "status": "published", "estimated_minutes": 45})
        module = await one_or_create(session, CourseModule, {"course_id": course.id, "position": 1}, {"title": "Core Principles", "description": "Foundation principles"})
        await one_or_create(session, Lesson, {"module_id": module.id, "position": 1}, {"title": "Expected Conduct", "content_type": "rich_text", "content": {"body": "Fixture content"}})
        learner = users["learner@demo.corp"]
        await one_or_create(session, Enrollment, {"tenant_id": tenant.id, "course_id": course.id, "user_id": learner.id}, {"status": "in_progress", "due_at": datetime.now(UTC) + timedelta(days=30), "source": "ci_fixture"})
        assessment = await one_or_create(session, Assessment, {"tenant_id": tenant.id, "title": "Ethics Knowledge Check"}, {"course_id": course.id, "passing_score": 70})
        assessment.course_id = course.id
        await one_or_create(session, Question, {"assessment_id": assessment.id, "position": 1}, {"question_type": "single_choice", "prompt": "Which principle supports responsible decisions?", "options": ["Transparency", "Concealment", "Retaliation"], "answer_key": {"correct": "Transparency"}, "points": 1})
        req = await one_or_create(session, ComplianceRequirement, {"tenant_id": tenant.id, "name": "Annual Ethics Training"}, {"description": "CI fixture requirement", "recurrence_days": 365, "due_days": 30, "active": True})
        await one_or_create(session, ComplianceAssignment, {"tenant_id": tenant.id, "requirement_id": req.id, "user_id": learner.id}, {"course_id": course.id, "due_at": datetime.now(UTC) + timedelta(days=30), "status": "assigned"})
        await one_or_create(session, Skill, {"tenant_id": tenant.id, "name": "Ethical Decision Making"}, {"description": "Ethical reasoning", "category": "Professional"})
        await one_or_create(session, AIGovernancePolicy, {"tenant_id": tenant.id}, {"enabled": False, "require_grounding": True, "employment_decisioning_allowed": False, "raw_prompt_storage_allowed": False, "raw_response_storage_allowed": False, "max_input_chars": 4000, "max_output_tokens": 1200, "allowed_provider_types": []})
        await session.commit()
    print("CI API fixtures seeded (demo and tenant-isolation records).")


if __name__ == "__main__":
    asyncio.run(seed())
