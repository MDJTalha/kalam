"""Create deterministic demo records required by API integration tests."""
# ruff: noqa: E402
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.core.role_catalog import PERMISSION_DESCRIPTIONS, TENANT_ROLE_PERMISSIONS
from app.db.models import (
    AIGovernancePolicy, Assessment, ComplianceAssignment, ComplianceRequirement,
    Course, CourseModule, Enrollment, Lesson, Permission, Question, Role,
    RolePermission, Skill, Tenant, User, UserRole,
)
from app.db.session import SessionLocal

PASSWORD = "DemoOnly!1234"
PERMISSIONS = [
    "tenant.read", "tenant.manage", "users.read", "users.manage", "courses.read",
    "courses.manage", "learning.access", "assessments.manage", "certificates.manage",
    "compliance.manage", "skills.manage", "development.manage", "reports.read",
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
    # This intentionally broad identity is a test harness only. It is not the
    # customer-facing Tenant Administrator role used by role acceptance tests.
    "QA Harness Administrator": PERMISSIONS,
    "Tenant Administrator": list(TENANT_ROLE_PERMISSIONS["Tenant Administrator"]),
    "L&D Administrator": list(TENANT_ROLE_PERMISSIONS["L&D Administrator"]),
    "Manager": list(TENANT_ROLE_PERMISSIONS["Manager"]),
    "Instructor": list(TENANT_ROLE_PERMISSIONS["Instructor"]),
    "Learner": list(TENANT_ROLE_PERMISSIONS["Learner / Employee"]),
    "Quality & Compliance": list(TENANT_ROLE_PERMISSIONS["Quality & Compliance"]),
}


async def one_or_create(session, model, where, values):
    obj = (await session.execute(select(model).filter_by(**where))).scalar_one_or_none()
    if obj is None:
        obj = model(**where, **values)
        session.add(obj)
        await session.flush()
    return obj


async def seed():
    async with SessionLocal() as session:
        tenants = {}
        for slug, name in (("demo-corporation", "Demo Corporation"), ("isolation-corporation", "Isolation Corporation")):
            tenants[slug] = await one_or_create(session, Tenant, {"slug": slug}, {"name": name, "status": "active"})

        perms = {}
        for key in sorted(set(PERMISSIONS) | set(PERMISSION_DESCRIPTIONS)):
            perms[key] = await one_or_create(
                session,
                Permission,
                {"key": key},
                {"description": PERMISSION_DESCRIPTIONS.get(key, key.replace(".", " "))},
            )

        users = {}
        demo_users = [
            ("admin@demo.corp", "Demo", "QA Harness", "QA Harness Administrator"),
            ("tenant-admin@demo.corp", "Demo", "Tenant Administrator", "Tenant Administrator"),
            ("ld@demo.corp", "Demo", "Learning Administrator", "L&D Administrator"),
            ("quality@demo.corp", "Demo", "Quality Reviewer", "Quality & Compliance"),
            ("manager@demo.corp", "Demo", "Manager", "Manager"),
            ("instructor@demo.corp", "Demo", "Instructor", "Instructor"),
            ("learner@demo.corp", "Demo", "Learner", "Learner"),
        ]
        for slug, tenant in tenants.items():
            names = demo_users if slug == "demo-corporation" else [("isolated@other.corp", "Isolated", "Learner", "Learner")]
            for role_name in sorted({row[3] for row in names}):
                role_kind = "legacy" if role_name == "QA Harness Administrator" else "predefined"
                role = await one_or_create(
                    session,
                    Role,
                    {"tenant_id": tenant.id, "name": role_name},
                    {"description": f"CI fixture role: {role_name}", "role_kind": role_kind},
                )
                role.role_kind = role_kind
                desired_permission_ids = {
                    perms[key].id for key in ROLE_PERMISSIONS[role_name]
                }
                existing_links = list((await session.execute(
                    select(RolePermission).where(RolePermission.role_id == role.id)
                )).scalars().all())
                for link in existing_links:
                    if link.permission_id not in desired_permission_ids:
                        await session.delete(link)
                for key in ROLE_PERMISSIONS[role_name]:
                    link = (await session.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == role.id,
                            RolePermission.permission_id == perms[key].id,
                        )
                    )).scalar_one_or_none()
                    if link is None:
                        session.add(RolePermission(role_id=role.id, permission_id=perms[key].id))
            for email, first, last, role_name in names:
                user = await one_or_create(session, User, {"tenant_id": tenant.id, "email": email}, {"password_hash": hash_password(PASSWORD), "first_name": first, "last_name": last, "job_title": role_name, "is_active": True})
                users[email] = user
                role = (await session.execute(select(Role).where(Role.tenant_id == tenant.id, Role.name == role_name))).scalar_one()
                if (await session.execute(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id))).scalar_one_or_none() is None:
                    session.add(UserRole(user_id=user.id, role_id=role.id))

        users["learner@demo.corp"].manager_id = users["manager@demo.corp"].id
        tenant = tenants["demo-corporation"]
        course = await one_or_create(session, Course, {"tenant_id": tenant.id, "slug": "workplace-ethics-2026"}, {"title": "Workplace Ethics & Responsible Conduct", "description": "CI fixture course", "status": "published", "estimated_minutes": 45})
        module = await one_or_create(session, CourseModule, {"course_id": course.id, "position": 1}, {"title": "Core Principles", "description": "Foundation principles"})
        await one_or_create(session, Lesson, {"module_id": module.id, "position": 1}, {"title": "Expected Conduct", "content_type": "rich_text", "content": {"body": "Fixture content"}})
        learner = users["learner@demo.corp"]
        await one_or_create(session, Enrollment, {"tenant_id": tenant.id, "course_id": course.id, "user_id": learner.id}, {"status": "in_progress", "due_at": datetime.now(timezone.utc) + timedelta(days=30), "source": "ci_fixture"})
        assessment = await one_or_create(session, Assessment, {"tenant_id": tenant.id, "title": "Ethics Knowledge Check"}, {"course_id": course.id, "passing_score": 70})
        assessment.course_id = course.id
        await one_or_create(session, Question, {"assessment_id": assessment.id, "position": 1}, {"question_type": "single_choice", "prompt": "Which principle supports responsible decisions?", "options": ["Transparency", "Concealment", "Retaliation"], "answer_key": {"correct": "Transparency"}, "points": 1})
        req = await one_or_create(session, ComplianceRequirement, {"tenant_id": tenant.id, "name": "Annual Ethics Training"}, {"description": "CI fixture requirement", "recurrence_days": 365, "due_days": 30, "active": True})
        await one_or_create(session, ComplianceAssignment, {"tenant_id": tenant.id, "requirement_id": req.id, "user_id": learner.id}, {"course_id": course.id, "due_at": datetime.now(timezone.utc) + timedelta(days=30), "status": "assigned"})
        await one_or_create(session, Skill, {"tenant_id": tenant.id, "name": "Ethical Decision Making"}, {"description": "Ethical reasoning", "category": "Professional"})
        await one_or_create(session, AIGovernancePolicy, {"tenant_id": tenant.id}, {"enabled": False, "require_grounding": True, "employment_decisioning_allowed": False, "raw_prompt_storage_allowed": False, "raw_response_storage_allowed": False, "max_input_chars": 4000, "max_output_tokens": 1200, "allowed_provider_types": []})
        await session.commit()
    print("CI API fixtures seeded (demo and tenant-isolation records).")


if __name__ == "__main__":
    asyncio.run(seed())
