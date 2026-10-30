
from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import (
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
from app.db.session import SessionLocal

DEMO_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "")
DEMO_TENANT = "demo-corporation"
DEMO_USERS = [
    ("admin@demo.corp", "Demo", "Administrator", "Tenant Administrator"),
    ("manager@demo.corp", "Demo", "Manager", "Manager"),
    ("instructor@demo.corp", "Demo", "Instructor", "Instructor"),
    ("learner@demo.corp", "Demo", "Learner", "Learner"),
]

PERMISSIONS = [
    ("tenant.read", "View tenant"),
    ("tenant.manage", "Manage tenant"),
    ("users.read", "View users"),
    ("users.manage", "Manage users"),
    ("users.team.read", "View direct reports and their assigned learning status"),
    ("courses.read", "View courses"),
    ("courses.manage", "Manage courses"),
    ("courses.assign_team", "Assign published learning to direct reports"),
    ("learning.access", "Access learning"),
    ("assessments.manage", "Manage assessments"),
    ("certificates.manage", "Manage certificates"),
    ("compliance.manage", "Manage compliance"),
    ("skills.manage", "Manage skills"),
    ("development.manage", "Manage development plans"),
    ("development.team.read", "Read direct reports' development plans and progress"),
    ("development.team.manage", "Manage development milestones and feedback for direct reports"),
    ("reports.read", "View reports"),
    ("reports.team.read", "View manager-scoped team learning reports"),
    ("reports.manage", "Create and manage saved reports and schedules"),
    ("audit.read", "View audit logs"),
    ("files.read", "View and download governed files"),
    ("files.manage", "Manage file scanning and file controls"),
    ("integrations.manage", "Manage external integrations"),
    ("ai.manage", "Manage governed AI providers, models, prompts and policies"),
    ("capabilities.manage", "Manage capability framework"),
    ("capabilities.read", "View capability framework"),
    ("capability_assessments.manage", "Manage capability assessments"),
    ("capability_assessments.read", "View capability assessments"),
    ("capability_assessments.execute", "Execute assigned capability assessments"),
    ("reassessment.manage", "Manage reassessments"),
    ("competencies.manage", "Manage competencies"),
    ("competencies.read", "View competencies"),
    ("role_requirements.manage", "Manage role requirements"),
    ("role_requirements.read", "View role requirements"),
    ("strategic_objectives.manage", "Manage strategic objectives"),
    ("strategic_objectives.read", "View strategic objectives"),
    ("capability_gaps.manage", "Manage capability gaps"),
    ("capability_gaps.read", "View capability gaps"),
    ("capability_risk.manage", "Manage capability risk"),
    ("capability_risk.read", "View capability risk"),
    ("evidence.manage", "Manage capability evidence"),
    ("evidence.read", "View capability evidence"),
    ("evidence.verify", "Verify or reject capability evidence"),
    ("development.recommendations.read", "View governed development recommendations"),
    ("development.recommendations.manage", "Accept and manage development recommendations"),
  ]

ROLE_PERMISSIONS = {
    "Tenant Administrator": [key for key, _ in PERMISSIONS],
    "HR/L&D Admin": ["users.read", "users.manage", "courses.read", "courses.manage", "learning.access", "assessments.manage", "certificates.manage", "compliance.manage", "skills.manage", "development.manage", "reports.read", "audit.read", "files.read", "files.manage", "ai.manage"],
    "Manager": [
        "users.team.read", "courses.read", "courses.assign_team", "learning.access",
        "reports.team.read", "development.manage", "development.team.read",
        "development.team.manage", "capabilities.read",
    ],
    "Instructor": ["courses.read", "courses.manage", "learning.access", "assessments.manage"],
    "Learner": ["courses.read", "learning.access", "development.manage", "capability_assessments.read", "capability_assessments.execute"],
    "Auditor": ["reports.read", "audit.read", "compliance.manage"],
}


async def get_or_create(session: AsyncSession, model, where: dict, values: dict):
    result = await session.execute(select(model).filter_by(**where))
    obj = result.scalar_one_or_none()
    if obj is None:
        obj = model(**where, **values)
        session.add(obj)
        await session.flush()
    return obj


async def seed() -> None:
    if os.getenv("APP_ENV", "development").lower() in {"production", "prod", "staging"}:
        raise RuntimeError("Legacy demo seeding is disabled in production-like environments.")
    if os.getenv("ALLOW_LEGACY_DEMO_SEED") != "true":
        raise RuntimeError("Set ALLOW_LEGACY_DEMO_SEED=true only for an isolated demo database.")
    if len(DEMO_PASSWORD) < 16:
        raise RuntimeError("SEED_ADMIN_PASSWORD must be explicitly set to at least 16 characters.")
    allowed_database = os.getenv("LEGACY_DEMO_SEED_DATABASE", "")
    database_name = settings.database_url.rsplit("/", 1)[-1].split("?", 1)[0]
    if not allowed_database or database_name != allowed_database or not database_name.startswith("corplms_demo_"):
        raise RuntimeError("Database target is not explicitly allowlisted as an isolated corplms_demo_* database.")
    async with SessionLocal() as session:
        tenant = await get_or_create(
            session,
            Tenant,
            {"slug": DEMO_TENANT},
            {"name": "Demo Corporation", "status": "active"},
        )

        permissions = {}
        for key, description in PERMISSIONS:
            permission = await get_or_create(
                session, Permission, {"key": key}, {"description": description}
            )
            permissions[key] = permission

        roles = {}
        for role_name in ROLE_PERMISSIONS:
            role = await get_or_create(
                session,
                Role,
                {"tenant_id": tenant.id, "name": role_name},
                {"description": f"Demo role: {role_name}"},
            )
            roles[role_name] = role

        for role_name, keys in ROLE_PERMISSIONS.items():
            if role_name == "Manager":
                # The demo manager role is a security fixture. Reconcile its
                # grants exactly so stale tenant-wide permissions cannot survive
                # a rerun of this explicitly allowlisted demo seed.
                await session.execute(
                    delete(RolePermission).where(
                        RolePermission.role_id == roles[role_name].id
                    )
                )
            for key in keys:
                rp = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == roles[role_name].id,
                        RolePermission.permission_id == permissions[key].id,
                    )
                )
                if rp.scalar_one_or_none() is None:
                    session.add(RolePermission(role_id=roles[role_name].id, permission_id=permissions[key].id))

        users = {}
        for email, first, last, role_name in DEMO_USERS:
            user = await get_or_create(
                session,
                User,
                {"tenant_id": tenant.id, "email": email},
                {
                    "password_hash": hash_password(DEMO_PASSWORD),
                    "first_name": first,
                    "last_name": last,
                    "job_title": role_name,
                    "is_active": True,
                },
            )
            # Keep the explicitly isolated QA demo account password deterministic on reseed.
            # This script refuses production-like environments and non-allowlisted databases above.
            user.password_hash = hash_password(DEMO_PASSWORD)
            user.is_active = True
            users[email] = user
            ur = await session.execute(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == roles[role_name].id,
                )
            )
            if ur.scalar_one_or_none() is None:
                session.add(UserRole(user_id=user.id, role_id=roles[role_name].id))

        users["learner@demo.corp"].manager_id = users["manager@demo.corp"].id
        await session.flush()

        isolation_tenant = await get_or_create(
            session,
            Tenant,
            {"slug": "isolation-corporation"},
            {"name": "Isolation Corporation", "status": "active"},
        )
        isolation_role = await get_or_create(
            session,
            Role,
            {"tenant_id": isolation_tenant.id, "name": "Learner"},
            {"description": "Isolation test learner role"},
        )
        for key in ROLE_PERMISSIONS["Learner"]:
            rp = await session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == isolation_role.id,
                    RolePermission.permission_id == permissions[key].id,
                )
            )
            if rp.scalar_one_or_none() is None:
                session.add(RolePermission(role_id=isolation_role.id, permission_id=permissions[key].id))
        isolation_user = await get_or_create(
            session,
            User,
            {"tenant_id": isolation_tenant.id, "email": "isolated@other.corp"},
            {
                "password_hash": hash_password(DEMO_PASSWORD),
                "first_name": "Isolated",
                "last_name": "Learner",
                "job_title": "Learner",
                "is_active": True,
            },
        )
        isolation_user.password_hash = hash_password(DEMO_PASSWORD)
        isolation_user.is_active = True
        isolation_ur = await session.execute(
            select(UserRole).where(
                UserRole.user_id == isolation_user.id,
                UserRole.role_id == isolation_role.id,
            )
        )
        if isolation_ur.scalar_one_or_none() is None:
            session.add(UserRole(user_id=isolation_user.id, role_id=isolation_role.id))

        course = await get_or_create(
            session,
            Course,
            {"tenant_id": tenant.id, "slug": "workplace-ethics-2026"},
            {
                "title": "Workplace Ethics & Responsible Conduct",
                "description": "Demo mandatory learning course for the Corporate LMS.",
                "status": "published",
                "estimated_minutes": 45,
            },
        )

        module = await get_or_create(
            session,
            CourseModule,
            {"course_id": course.id, "position": 1},
            {"title": "Core Principles", "description": "Foundation principles"},
        )
        await get_or_create(
            session,
            Lesson,
            {"module_id": module.id, "position": 1},
            {
                "title": "Expected Conduct",
                "content_type": "rich_text",
                "content": {"body": "Demo content. Replace with governed organization content."},
            },
        )

        await get_or_create(
            session,
            Enrollment,
            {"tenant_id": tenant.id, "course_id": course.id, "user_id": users["learner@demo.corp"].id},
            {
                "status": "in_progress",
                "due_at": datetime.now(UTC) + timedelta(days=30),
                "source": "demo_seed",
            },
        )

        assessment = await get_or_create(
            session,
            Assessment,
            {"tenant_id": tenant.id, "title": "Ethics Knowledge Check"},
            {"course_id": course.id, "passing_score": 70, "max_attempts": None},
        )
        assessment.course_id = course.id
        assessment.passing_score = 70
        assessment.max_attempts = None
        await get_or_create(
            session,
            Question,
            {"assessment_id": assessment.id, "position": 1},
            {
                "question_type": "single_choice",
                "prompt": "Which principle supports responsible workplace decision-making?",
                "options": ["Transparency", "Concealment", "Retaliation"],
                "answer_key": {"correct": "Transparency"},
                "points": 1,
            },
        )

        requirement = await get_or_create(
            session,
            ComplianceRequirement,
            {"tenant_id": tenant.id, "name": "Annual Ethics Training"},
            {
                "description": "Demo recurring compliance requirement.",
                "recurrence_days": 365,
                "due_days": 30,
                "active": True,
            },
        )

        await get_or_create(
            session,
            ComplianceAssignment,
            {"tenant_id": tenant.id, "requirement_id": requirement.id, "user_id": users["learner@demo.corp"].id},
            {
                "course_id": course.id,
                "due_at": datetime.now(UTC) + timedelta(days=30),
                "status": "assigned",
            },
        )

        skill = await get_or_create(
            session,
            Skill,
            {"tenant_id": tenant.id, "name": "Ethical Decision Making"},
            {"description": "Applies ethical reasoning in workplace decisions.", "category": "Professional"},
        )

        await get_or_create(
            session,
            AIGovernancePolicy,
            {"tenant_id": tenant.id},
            {
                "enabled": False,
                "require_grounding": True,
                "employment_decisioning_allowed": False,
                "raw_prompt_storage_allowed": False,
                "raw_response_storage_allowed": False,
                "max_input_chars": 4000,
                "max_output_tokens": 1200,
                "allowed_provider_types": ["ollama"],
            },
        )
        await session.commit()

        print("DEMO seed complete")
        print(f"Tenant: {tenant.name} ({tenant.slug})")
        print("Demo users:")
        for email, _, _, role_name in DEMO_USERS:
            print(f"  {role_name}: {email}")
        print(f"Course: {course.title}")
        print(f"Compliance: {requirement.name}")
        print(f"Skill: {skill.name}")
        print("WARNING: Seed data is DEMO DATA only.")


if __name__ == "__main__":
    asyncio.run(seed())
