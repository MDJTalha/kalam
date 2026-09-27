from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.db.models import ComplianceAssignment, ComplianceException, ComplianceRequirement, Course, Enrollment, Notification, User
from app.services.audit import audit


async def run_compliance_automation(db: AsyncSession) -> dict[str, int]:
    now = utcnow()
    expired_exceptions = (await db.scalars(
        select(ComplianceException).where(
            ComplianceException.status == "approved",
            or_(ComplianceException.expires_at.is_(None), ComplianceException.expires_at <= now),
        )
    )).all()
    for exception in expired_exceptions:
        exception.status = "expired"
        assignment = await db.scalar(select(ComplianceAssignment).where(
            ComplianceAssignment.id == exception.assignment_id,
            ComplianceAssignment.tenant_id == exception.tenant_id,
        ))
        if assignment and assignment.status == "excepted":
            assignment.status = "overdue" if assignment.due_at and assignment.due_at < now else "assigned"
        await audit(db, tenant_id=exception.tenant_id, actor_id=None,
                    action="compliance.exception.expired", entity_type="compliance_exception", entity_id=str(exception.id))
    result = await db.execute(
        select(ComplianceAssignment, ComplianceRequirement, User)
        .join(ComplianceRequirement, ComplianceRequirement.id == ComplianceAssignment.requirement_id)
        .join(User, User.id == ComplianceAssignment.user_id)
        .where(ComplianceAssignment.tenant_id == ComplianceRequirement.tenant_id)
        .where(ComplianceRequirement.active.is_(True))
        .where(User.is_active.is_(True))
    )
    overdue = reminders = recurring = escalations = 0
    for assignment, requirement, learner in result.all():
        rules = requirement.rules or {}
        escalation_days = max(1, int(rules.get("escalation_days", 7)))
        if assignment.status in {"completed", "excepted"}:
            if assignment.status == "completed" and requirement.recurrence_days:
                next_due = (assignment.updated_at or now) + timedelta(days=requirement.recurrence_days)
                existing = await db.scalar(
                    select(ComplianceAssignment.id).where(
                        ComplianceAssignment.tenant_id == assignment.tenant_id,
                        ComplianceAssignment.requirement_id == assignment.requirement_id,
                        ComplianceAssignment.user_id == assignment.user_id,
                        ComplianceAssignment.id != assignment.id,
                        or_(
                            ComplianceAssignment.created_at > assignment.created_at,
                            ComplianceAssignment.status.in_(["assigned", "due_soon", "overdue", "evidence_submitted", "exception_requested"]),
                        ),
                    )
                )
                if existing is None and next_due <= now:
                    course = None
                    if assignment.course_id:
                        course = await db.scalar(select(Course).where(
                            Course.id == assignment.course_id,
                            Course.tenant_id == assignment.tenant_id,
                            Course.status == "published",
                        ).with_for_update())
                        if course is None:
                            await audit(db, tenant_id=assignment.tenant_id, actor_id=None,
                                        action="compliance.recurrence.blocked_unpublished_course",
                                        entity_type="compliance_assignment", entity_id=str(assignment.id))
                            continue
                    due_at = now + timedelta(days=requirement.due_days or 30)
                    renewed = ComplianceAssignment(
                        tenant_id=assignment.tenant_id,
                        requirement_id=assignment.requirement_id,
                        requirement_version=requirement.version,
                        user_id=assignment.user_id,
                        course_id=assignment.course_id,
                        due_at=due_at,
                        status="assigned",
                    )
                    db.add(renewed)
                    await db.flush()
                    if course:
                        latest = await db.scalar(select(Enrollment).where(
                            Enrollment.tenant_id == assignment.tenant_id,
                            Enrollment.course_id == course.id,
                            Enrollment.user_id == assignment.user_id,
                        ).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()))
                        if latest is None or latest.status in {"completed", "rejected"}:
                            active = await db.scalar(select(func.count(Enrollment.id)).where(
                                Enrollment.tenant_id == assignment.tenant_id,
                                Enrollment.course_id == course.id,
                                Enrollment.status.in_(["enrolled", "in_progress"]),
                            )) or 0
                            status = "waitlisted" if course.capacity and active >= course.capacity else "enrolled"
                            db.add(Enrollment(tenant_id=assignment.tenant_id, course_id=course.id,
                                              user_id=assignment.user_id, status=status, source="compliance",
                                              due_at=due_at))
                    await audit(db, tenant_id=assignment.tenant_id, actor_id=None,
                                action="compliance.assignment.renewed", entity_type="compliance_assignment",
                                entity_id=str(renewed.id), metadata={"previous_assignment_id": str(assignment.id)})
                    recurring += 1
            continue
        if assignment.due_at and assignment.due_at < now and assignment.status not in {"overdue", "exception_requested", "evidence_submitted"}:
            assignment.status = "overdue"
            overdue += 1
        if not assignment.due_at:
            continue
        days_left = (assignment.due_at - now).total_seconds() / 86400
        bucket = "overdue" if days_left < 0 else "due"
        if days_left < 0 or days_left <= 7:
            key = f"compliance:{assignment.id}:{bucket}"
            existing = await db.scalar(select(Notification.id).where(Notification.dedupe_key == key))
            if existing is None:
                title = f"Compliance {'overdue' if bucket == 'overdue' else 'due soon'}: {requirement.name}"
                body = (
                    f"{requirement.name} is overdue."
                    if bucket == "overdue"
                    else f"{requirement.name} is due by {assignment.due_at.isoformat()}."
                )
                db.add(Notification(
                    tenant_id=assignment.tenant_id,
                    user_id=learner.id,
                    notification_type="compliance.reminder",
                    title=title,
                    body=body,
                    dedupe_key=key,
                ))
                reminders += 1
        if assignment.due_at and assignment.due_at + timedelta(days=escalation_days) <= now and learner.manager_id:
            escalation_key = f"compliance:{assignment.id}:manager-escalation"
            existing = await db.scalar(select(Notification.id).where(Notification.dedupe_key == escalation_key))
            if existing is None:
                manager = await db.scalar(select(User).where(
                    User.id == learner.manager_id,
                    User.tenant_id == learner.tenant_id,
                    User.is_active.is_(True),
                ))
                if manager is not None:
                    db.add(Notification(
                        tenant_id=assignment.tenant_id,
                        user_id=manager.id,
                        notification_type="compliance.manager_escalation",
                        title=f"Compliance escalation: {learner.first_name} {learner.last_name}",
                        body=f"{requirement.name} remains overdue for {learner.first_name} {learner.last_name}. Due date: {assignment.due_at.isoformat()}.",
                        dedupe_key=escalation_key,
                    ))
                    escalations += 1
    await db.commit()
    return {
        "compliance_overdue": overdue,
        "compliance_reminders": reminders,
        "compliance_recurring": recurring,
        "compliance_escalations": escalations,
        "compliance_exceptions_expired": len(expired_exceptions),
    }
