# ruff: noqa: E402

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import (
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
    Skill,
    Tenant,
    User,
    UserRole,
)
from app.db.session import SessionLocal


DEMO_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "DemoOnly!1234")
DEMO_TENANT = "demo-corporation"
DEMO_USERS = [
    ("admin@demo.corp", "Demo", "Administrator", "Tenant Admin"),
    ("manager@demo.corp", "Demo", "Manager", "Manager"),
    ("instructor@demo.corp", "Demo", "Instructor", "Instructor"),
    ("learner@demo.corp", "Demo", "Learner", "Learner"),
]

PERMISSIONS = [
    ("tenant.read", "View tenant"),
    ("tenant.manage", "Manage tenant"),
    ("users.read", "View users"),
    ("users.manage", "Manage users"),
    ("courses.read", "View courses"),
    ("courses.manage", "Manage courses"),
    ("learning.access", "Access learning"),
    ("assessments.manage", "Manage assessments"),
    ("certificates.manage", "Manage certificates"),
    ("compliance.manage", "Manage compliance"),
    ("skills.manage", "Manage skills"),
    ("development.manage", "Manage development plans"),
    ("reports.read", "View reports"),
    ("audit.read", "View audit logs"),
    ("files.manage", "Manage file scanning and file controls"),
    ("integrations.manage", "Manage external integrations"),
]

ROLE_PERMISSIONS = {
    "Tenant Admin": [key for key, _ in PERMISSIONS],
    "HR/L&D Admin": ["users.read", "users.manage", "courses.read", "courses.manage", "learning.access", "assessments.manage", "certificates.manage", "compliance.manage", "skills.manage", "development.manage", "reports.read", "audit.read"],
    "Manager": ["users.read", "courses.read", "learning.access", "reports.read"],
    "Instructor": ["courses.read", "courses.manage", "learning.access", "assessments.manage"],
    "Learner": ["courses.read", "learning.access", "development.manage"],
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
            for key in keys:
                from app.db.models import RolePermission
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
                "due_at": datetime.now(timezone.utc) + timedelta(days=30),
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
                "due_at": datetime.now(timezone.utc) + timedelta(days=30),
                "status": "assigned",
            },
        )

        skill = await get_or_create(
            session,
            Skill,
            {"tenant_id": tenant.id, "name": "Ethical Decision Making"},
            {"description": "Applies ethical reasoning in workplace decisions.", "category": "Professional"},
        )

        await session.commit()

        print("DEMO seed complete")
        print(f"Tenant: {tenant.name} ({tenant.slug})")
        print("Demo users:")
        for email, _, _, role_name in DEMO_USERS:
            print(f"  {role_name}: {email}")
        print(f"Demo password: {DEMO_PASSWORD}")
        print(f"Course: {course.title}")
        print(f"Compliance: {requirement.name}")
        print(f"Skill: {skill.name}")
        print("WARNING: Seed data is DEMO DATA only.")


if __name__ == "__main__":
    asyncio.run(seed())
