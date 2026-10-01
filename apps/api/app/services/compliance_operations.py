from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.db.models import (
    AuditLog,
    ComplianceAssignment,
    ComplianceException,
    ComplianceEvidence,
    ComplianceRequirement,
    Course,
    Enrollment,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.services.audit import audit
from app.services.notifications import create_notification

OPEN_ASSIGNMENT_STATUSES = (
    "assigned", "due_soon", "overdue", "evidence_submitted", "exception_requested"
)


async def _completion_timestamp(assignment: ComplianceAssignment, db: AsyncSession) -> datetime | None:
    if assignment.course_id:
        return await db.scalar(select(func.max(Enrollment.completed_at)).where(
            Enrollment.tenant_id == assignment.tenant_id,
            Enrollment.user_id == assignment.user_id,
            Enrollment.course_id == assignment.course_id,
            Enrollment.status == "completed",
            Enrollment.completed_at.is_not(None),
            Enrollment.completed_at >= assignment.created_at,
        ))
    return await db.scalar(select(func.max(ComplianceEvidence.verified_at)).where(
        ComplianceEvidence.tenant_id == assignment.tenant_id,
        ComplianceEvidence.assignment_id == assignment.id,
        ComplianceEvidence.verified_at.is_not(None),
    ))


async def _compliance_managers(db: AsyncSession, tenant_id: UUID) -> list[User]:
    result = await db.scalars(select(User).join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(User.tenant_id == tenant_id, User.is_active.is_(True),
               Role.tenant_id == tenant_id, Permission.key == "compliance.manage").distinct())
    return list(result.all())


async def _ensure_enrollment(
    db: AsyncSession, *, tenant_id: UUID, learner_id: UUID, course: Course,
    due_at: datetime, actor_id: UUID | None,
) -> None:
    existing = await db.scalar(select(Enrollment).where(
        Enrollment.tenant_id == tenant_id, Enrollment.user_id == learner_id,
        Enrollment.course_id == course.id,
    ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()))
    if existing and existing.status in {"enrolled", "in_progress", "waitlisted", "pending_approval"}:
        return
    active = await db.scalar(select(func.count(Enrollment.id)).where(
        Enrollment.tenant_id == tenant_id, Enrollment.course_id == course.id,
        Enrollment.status.in_(["enrolled", "in_progress"]),
    )) or 0
    next_status = "waitlisted" if course.capacity and active >= course.capacity else "enrolled"
    if existing and existing.status == "rejected":
        existing.status = next_status
        existing.due_at = due_at
        existing.source = "compliance"
    else:
        db.add(Enrollment(tenant_id=tenant_id, user_id=learner_id, course_id=course.id,
                          due_at=due_at, status=next_status, source="compliance"))
    await audit(db, tenant_id=tenant_id, actor_id=actor_id,
                action="compliance.learning.enrolled", entity_type="course",
                entity_id=str(course.id), metadata={"learner_id": str(learner_id), "status": next_status})


async def run_compliance_operations_for_tenant(
    db: AsyncSession, tenant_id: UUID, actor_id: UUID | None = None,
) -> dict[str, int | str | datetime]:
    now = utcnow()
    # One transaction-wide advisory lock prevents duplicate recurrence/escalation work
    # when multiple worker replicas or a manual admin run overlap for the same tenant.
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                     {"key": f"kalam:compliance-operations:{tenant_id}"})

    overdue = expired_exceptions = recurring_created = escalated = 0
    requirements = {item.id: item for item in (await db.scalars(
        select(ComplianceRequirement).where(ComplianceRequirement.tenant_id == tenant_id)
    )).all()}
    assignments = list((await db.scalars(
        select(ComplianceAssignment).where(ComplianceAssignment.tenant_id == tenant_id)
        .order_by(ComplianceAssignment.created_at.asc())
    )).all())

    for assignment in assignments:
        if assignment.due_at and assignment.due_at < now and assignment.status in {"assigned", "due_soon"}:
            assignment.status = "overdue"
            overdue += 1

    approved_exceptions = (await db.scalars(select(ComplianceException).join(
        ComplianceAssignment, ComplianceAssignment.id == ComplianceException.assignment_id).where(
            ComplianceException.tenant_id == tenant_id, ComplianceException.status == "approved",
            ComplianceException.expires_at.is_not(None), ComplianceException.expires_at <= now,
            ComplianceAssignment.tenant_id == tenant_id,
        ))).all()
    assignment_by_id = {item.id: item for item in assignments}
    for exception in approved_exceptions:
        exception.status = "expired"
        assignment = assignment_by_id.get(exception.assignment_id)
        if assignment and assignment.status == "excepted":
            assignment.status = "overdue" if assignment.due_at and assignment.due_at < now else "assigned"
        expired_exceptions += 1
        await audit(db, tenant_id=tenant_id, actor_id=actor_id, action="compliance.exception.expired",
                    entity_type="compliance_exception", entity_id=str(exception.id))

    open_by_requirement_user = {(item.requirement_id, item.user_id) for item in assignments
                                if item.status in OPEN_ASSIGNMENT_STATUSES}
    for assignment in assignments:
        requirement = requirements.get(assignment.requirement_id)
        if requirement is None or not requirement.active or not requirement.recurrence_days or assignment.status != "completed":
            continue
        completed_at = await _completion_timestamp(assignment, db)
        if completed_at is None or completed_at + timedelta(days=requirement.recurrence_days) > now:
            continue
        key = (assignment.requirement_id, assignment.user_id)
        if key in open_by_requirement_user:
            continue
        due_at = now + timedelta(days=requirement.due_days or 30)
        next_assignment = ComplianceAssignment(
            tenant_id=tenant_id, requirement_id=requirement.id, requirement_version=requirement.version,
            user_id=assignment.user_id, course_id=assignment.course_id, due_at=due_at, status="assigned",
        )
        db.add(next_assignment)
        await db.flush()
        if assignment.course_id:
            course = await db.scalar(select(Course).where(
                Course.id == assignment.course_id, Course.tenant_id == tenant_id, Course.status == "published"))
            if course is not None:
                await _ensure_enrollment(db, tenant_id=tenant_id, learner_id=assignment.user_id,
                                         course=course, due_at=due_at, actor_id=actor_id)
        open_by_requirement_user.add(key)
        recurring_created += 1
        await audit(db, tenant_id=tenant_id, actor_id=actor_id,
                    action="compliance.assignment.recurring_created",
                    entity_type="compliance_assignment", entity_id=str(next_assignment.id),
                    metadata={"source_assignment_id": str(assignment.id), "recurrence_days": requirement.recurrence_days})

    managers = await _compliance_managers(db, tenant_id)
    for assignment in assignments:
        if assignment.status not in {"overdue", "evidence_submitted", "exception_requested"} or not assignment.due_at:
            continue
        requirement = requirements.get(assignment.requirement_id)
        escalation_days = max(1, int((requirement.rules or {}).get("escalation_days", 7))) if requirement else 7
        escalation_at = assignment.due_at + timedelta(days=escalation_days)
        if now < escalation_at:
            continue
        already_logged = await db.scalar(select(AuditLog.id).where(
            AuditLog.tenant_id == tenant_id, AuditLog.action == "compliance.assignment.escalated",
            AuditLog.entity_type == "compliance_assignment", AuditLog.entity_id == str(assignment.id)))
        if already_logged:
            continue
        learner_name = await db.scalar(select(func.concat(User.first_name, " ", User.last_name)).where(
            User.id == assignment.user_id, User.tenant_id == tenant_id))
        requirement_name = requirement.name if requirement else "Compliance obligation"
        await create_notification(db, tenant_id=tenant_id, user_id=assignment.user_id,
            notification_type="compliance.escalation", title="Compliance obligation requires attention",
            body=f"{requirement_name} remains unresolved and has passed its escalation threshold. Review the requirement in Kalam.",
            dedupe_key=f"compliance-escalation:{assignment.id}")
        for manager in managers:
            await create_notification(db, tenant_id=tenant_id, user_id=manager.id,
                notification_type="compliance.escalation.manager", title="Compliance escalation requires review",
                body=f"{learner_name or 'A learner'} has an unresolved {requirement_name} obligation that passed its escalation threshold on {escalation_at.date().isoformat()}.",
                dedupe_key=f"compliance-escalation-manager:{assignment.id}:{manager.id}",
                action_href="/dashboard/compliance/admin")
        await audit(db, tenant_id=tenant_id, actor_id=actor_id,
                    action="compliance.assignment.escalated", entity_type="compliance_assignment",
                    entity_id=str(assignment.id), metadata={"escalation_days": escalation_days})
        escalated += 1

    await db.commit()
    return {"status": "completed", "overdue": overdue, "expired_exceptions": expired_exceptions,
            "recurring_created": recurring_created, "escalated": escalated, "processed_at": now}
