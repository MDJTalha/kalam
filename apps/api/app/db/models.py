from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    org_units: Mapped[list["OrgUnit"]] = relationship(back_populates="tenant")

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    employee_number: Mapped[str | None] = mapped_column(String(80))
    job_title: Mapped[str | None] = mapped_column(String(160))
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    org_unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("org_units.id", ondelete="SET NULL"), index=True)
    manager_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def session_ttl(self) -> timedelta:
        return timedelta(hours=8)

class SessionRecord(Base):
    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class DeveloperSupportSession(Base, TimestampMixin):
    __tablename__ = "developer_support_sessions"
    __table_args__ = (
        Index("ix_dev_support_session_token", "token_hash"),
        Index("ix_dev_support_session_developer", "developer_user_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    developer_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class SupportCase(Base, TimestampMixin):
    __tablename__ = "support_cases"
    __table_args__ = (
        Index("ix_support_cases_tenant_status", "tenant_id", "status"),
        Index("ix_support_cases_requester_created", "requester_user_id", "created_at"),
        Index("ix_support_cases_assigned_status", "assigned_to_user_id", "status"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    requester_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    internal_note: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportCaseMessage(Base):
    __tablename__ = "support_case_messages"
    __table_args__ = (Index("ix_support_case_messages_case_created", "case_id", "created_at"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False)
    author_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="requester", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    role_kind: Mapped[str] = mapped_column(String(20), default="custom", nullable=False)
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    roles: Mapped[list["RolePermission"]] = relationship(back_populates="permission")

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="roles")

class OrgUnit(Base, TimestampMixin):
    __tablename__ = "org_units"
    __table_args__ = (UniqueConstraint("tenant_id", "name", "parent_id", name="uq_orgunit_tenant_name_parent"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("org_units.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(40), default="department", nullable=False)
    code: Mapped[str | None] = mapped_column(String(80))
    tenant: Mapped["Tenant"] = relationship(back_populates="org_units")
    parent: Mapped["OrgUnit | None"] = relationship(remote_side=[id])
class CourseVisibility(StrEnum):
    TENANT = "tenant"
    PRIVATE = "private"

class CourseStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CourseCategory(Base, TimestampMixin):
    __tablename__ = "course_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_course_category_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_courses_tenant_slug"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=CourseStatus.DRAFT.value, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("course_categories.id", ondelete="SET NULL"), index=True)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    visibility: Mapped[str] = mapped_column(String(30), default=CourseVisibility.TENANT.value, nullable=False)
    enrollment_policy: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    capacity: Mapped[int | None] = mapped_column(Integer)
    audience_org_units: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    tags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    prerequisites: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_mandatory_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    modules: Mapped[list["CourseModule"]] = relationship(back_populates="course", cascade="all, delete-orphan")

class CourseModule(Base, TimestampMixin):
    __tablename__ = "course_modules"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    course: Mapped["Course"] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="module", cascade="all, delete-orphan")

class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), default="rich_text", nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    module: Mapped["CourseModule"] = relationship(back_populates="lessons")

class CourseContentVersion(Base):
    __tablename__ = "course_content_versions"
    __table_args__ = (UniqueConstraint("lesson_id", "version_number", name="uq_course_content_version"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollments"
    __table_args__ = (Index("uq_enrollment_active_tenant_course_user", "tenant_id", "course_id", "user_id", unique=True, postgresql_where=text("status NOT IN (\'completed\', \'rejected\')")),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="enrolled", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(30), default="admin", nullable=False)

class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("enrollment_id", "lesson_id", name="uq_progress_enrollment_lesson"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="not_started", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    max_attempts: Mapped[int | None] = mapped_column(Integer)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer)
    assessment_type: Mapped[str] = mapped_column(String(40), default="knowledge_test", nullable=False)
    measurement_method: Mapped[str] = mapped_column(String(40), default="score_based", nullable=False)
    validity_days: Mapped[int | None] = mapped_column(Integer)
    reassessment_interval_days: Mapped[int | None] = mapped_column(Integer)
    instructions: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class AssessmentTarget(Base):
    __tablename__ = "assessment_targets"
    __table_args__ = (
        UniqueConstraint("assessment_id", "target_type", "target_id", name="uq_assessment_target"),
        CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_target_type"),
        CheckConstraint("target_level >= 1 AND target_level <= 5", name="ck_assessment_target_level"),
        CheckConstraint("weight >= 1 AND weight <= 100", name="ck_assessment_target_weight"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    target_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("3.00"), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class Question(Base, TimestampMixin):
    __tablename__ = "questions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String(40), default="single_choice", nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
class AssessmentCycle(Base, TimestampMixin):
    __tablename__ = "assessment_cycles"
    __table_args__ = (
        CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_cycle_target_type"),
        CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_assessment_cycle_required_level"),
        CheckConstraint("baseline_level IS NULL OR (baseline_level >= 1 AND baseline_level <= 5)", name="ck_assessment_cycle_baseline_level"),
        CheckConstraint("current_level IS NULL OR (current_level >= 1 AND current_level <= 5)", name="ck_assessment_cycle_current_level"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    required_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    baseline_level: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    current_level: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    baseline_attempt_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    latest_attempt_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(30), default="baseline_due", nullable=False, index=True)
    next_reassessment_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    development_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("development_plans.id", ondelete="SET NULL"), index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

class AssessmentReviewerAssignment(Base, TimestampMixin):
    __tablename__ = "assessment_reviewer_assignments"
    __table_args__ = (
        UniqueConstraint("cycle_id", "reviewer_id", name="uq_assessment_cycle_reviewer"),
        CheckConstraint("reviewer_type IN ('self','manager','assessor','peer')", name="ck_assessment_reviewer_type"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[UUID] = mapped_column(ForeignKey("assessment_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="assigned", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[UUID | None] = mapped_column(ForeignKey("assessment_cycles.id", ondelete="SET NULL"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(20), default="standalone", nullable=False)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    demonstrated_level: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    confidence: Mapped[int | None] = mapped_column(Integer)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    feedback: Mapped[str | None] = mapped_column(Text)
    assessor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    graded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    grade_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    grade_override_reason: Mapped[str | None] = mapped_column(Text)
    assessment_method: Mapped[str] = mapped_column(String(40), default="score_based", nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AssessmentOutcome(Base, TimestampMixin):
    __tablename__ = "assessment_outcomes"
    __table_args__ = (
        UniqueConstraint("attempt_id", "target_type", "target_id", name="uq_assessment_outcome_target"),
        CheckConstraint("target_type IN ('capability','competency','skill')", name="ck_assessment_outcome_target_type"),
        CheckConstraint("demonstrated_level >= 1 AND demonstrated_level <= 5", name="ck_assessment_outcome_level"),
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_assessment_outcome_confidence"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    score: Mapped[int | None] = mapped_column(Integer)
    demonstrated_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    evidence_notes: Mapped[str | None] = mapped_column(Text)
    evidence_reference: Mapped[str | None] = mapped_column(String(1000))
    assessor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

class Certificate(Base, TimestampMixin):
    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("tenant_id", "verification_code", name="uq_cert_tenant_verification"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    verification_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

class ComplianceRequirement(Base, TimestampMixin):
    __tablename__ = "compliance_requirements"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    recurrence_days: Mapped[int | None] = mapped_column(Integer)
    due_days: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class ComplianceRequirementVersion(Base):
    __tablename__ = "compliance_requirement_versions"
    requirement_id: Mapped[UUID] = mapped_column(ForeignKey("compliance_requirements.id", ondelete="CASCADE"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ComplianceAssignment(Base, TimestampMixin):
    __tablename__ = "compliance_assignments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[UUID] = mapped_column(ForeignKey("compliance_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="assigned", nullable=False)

class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidence"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id: Mapped[UUID] = mapped_column(ForeignKey("compliance_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ComplianceException(Base):
    __tablename__ = "compliance_exceptions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id: Mapped[UUID] = mapped_column(ForeignKey("compliance_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="requested", nullable=False)
    requested_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Skill(Base, TimestampMixin):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_skill_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(120))

class CapabilityCategory(Base, TimestampMixin):
    __tablename__ = "capability_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_capability_category_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class ProficiencyLevel(Base):
    __tablename__ = "proficiency_levels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "level", name="uq_proficiency_level_tenant_level"),
        CheckConstraint("level >= 1 AND level <= 5", name="ck_proficiency_level_range"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)


class StrategicObjective(Base, TimestampMixin):
    __tablename__ = "strategic_objectives"
    __table_args__ = (
        UniqueConstraint("tenant_id", "objective", name="uq_strategic_objective_tenant_name"),
        CheckConstraint("priority >= 1 AND priority <= 5", name="ck_strategic_objective_priority"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    business_unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("org_units.id", ondelete="SET NULL"), index=True)
    objective: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    strategic_category: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StrategicObjectiveCapability(Base):
    __tablename__ = "strategic_objective_capabilities"
    __table_args__ = (
        CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_objective_capability_required_level"),
        CheckConstraint("weight >= 1 AND weight <= 100", name="ck_objective_capability_weight"),
    )
    objective_id: Mapped[UUID] = mapped_column(ForeignKey("strategic_objectives.id", ondelete="CASCADE"), primary_key=True)
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True)
    required_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Competency(Base, TimestampMixin):
    __tablename__ = "competencies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_competency_tenant_code"),
        UniqueConstraint("tenant_id", "name", name="uq_competency_tenant_name"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="behavioral", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompetencyLevel(Base):
    __tablename__ = "competency_levels"
    __table_args__ = (
        UniqueConstraint("competency_id", "level", name="uq_competency_level"),
        CheckConstraint("level >= 1 AND level <= 5", name="ck_competency_level_range"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    behavioral_indicators: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class CapabilityCompetency(Base):
    __tablename__ = "capability_competencies"
    __table_args__ = (CheckConstraint("weight >= 1 AND weight <= 100", name="ck_capability_competency_weight"),)
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True)
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class RoleRequirement(Base, TimestampMixin):
    __tablename__ = "role_requirements"
    __table_args__ = (
        CheckConstraint(
            "((capability_id IS NOT NULL)::int + (competency_id IS NOT NULL)::int + (skill_id IS NOT NULL)::int) = 1",
            name="ck_role_requirement_single_target",
        ),
        CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_role_requirement_level"),
        CheckConstraint("weight >= 1 AND weight <= 100", name="ck_role_requirement_weight"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_id: Mapped[UUID | None] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), index=True)
    competency_id: Mapped[UUID | None] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    criticality: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Capability(Base, TimestampMixin):
    __tablename__ = "capabilities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_capability_tenant_code"),
        UniqueConstraint("tenant_id", "name", name="uq_capability_tenant_name"),
        CheckConstraint("level_min >= 1 AND level_min <= 5", name="ck_capability_level_min"),
        CheckConstraint("level_max >= 1 AND level_max <= 5", name="ck_capability_level_max"),
        CheckConstraint("level_min <= level_max", name="ck_capability_level_range"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("capability_categories.id", ondelete="SET NULL"), index=True)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    level_min: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    level_max: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    criticality: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    governance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

class CapabilityLevel(Base):
    __tablename__ = "capability_levels"
    __table_args__ = (UniqueConstraint("capability_id", "level", name="uq_capability_level"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    indicators: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

class CapabilitySkill(Base):
    __tablename__ = "capability_skills"
    __table_args__ = (UniqueConstraint("capability_id", "skill_id", name="uq_capability_skill"),)
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class UserSkill(Base, TimestampMixin):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evidence_source: Mapped[str | None] = mapped_column(String(80))

class CapabilityEvidence(Base, TimestampMixin):
    __tablename__ = "capability_evidence"
    __table_args__ = (
        Index("ix_capability_evidence_tenant_user", "tenant_id", "user_id"),
        Index("ix_capability_evidence_target", "tenant_id", "target_type", "target_id"),
        UniqueConstraint("tenant_id", "user_id", "target_type", "target_id", "source_type", "source_id", name="uq_capability_evidence_source_provenance"),
        CheckConstraint("demonstrated_level >= 1 AND demonstrated_level <= 5", name="ck_capability_evidence_level"),
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_capability_evidence_confidence"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(160))
    demonstrated_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assessor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)


class CapabilityGap(Base, TimestampMixin):
    __tablename__ = "capability_gaps"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "role_requirement_id", name="uq_capability_gap_assignment"),
        CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_capability_gap_required_level"),
        CheckConstraint("demonstrated_level IS NULL OR (demonstrated_level >= 1 AND demonstrated_level <= 5)", name="ck_capability_gap_demonstrated_level"),
        CheckConstraint("gap_value IS NULL OR gap_value >= 0", name="ck_capability_gap_value"),
        CheckConstraint("evidence_confidence >= 0 AND evidence_confidence <= 100", name="ck_capability_gap_confidence"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_requirement_id: Mapped[UUID] = mapped_column(ForeignKey("role_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    required_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    demonstrated_level: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    gap_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    criticality: Mapped[str] = mapped_column(String(20), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evidence_confidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    calculation_version: Mapped[str] = mapped_column(String(30), default="phase4.v1", nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AssessmentCompetency(Base):
    __tablename__ = "assessment_competencies"
    __table_args__ = (
        UniqueConstraint("assessment_id", "competency_id", name="uq_assessment_competency"),
        CheckConstraint("target_level >= 1 AND target_level <= 5", name="ck_assessment_competency_target_level"),
    )
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True)
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True)
    target_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class DevelopmentPlan(Base, TimestampMixin):
    __tablename__ = "development_plans"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    goals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

class DevelopmentMilestone(Base, TimestampMixin):
    __tablename__ = "development_milestones"
    __table_args__ = (UniqueConstraint("plan_id", "title", name="uq_development_milestone_plan_title"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("development_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

class DevelopmentFeedback(Base, TimestampMixin):
    __tablename__ = "development_feedback"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("development_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    strengths: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    next_steps: Mapped[str | None] = mapped_column(Text)

class DevelopmentIntervention(Base, TimestampMixin):
    __tablename__ = "development_interventions"
    __table_args__ = (
        Index("ix_development_interventions_tenant_user_status", "tenant_id", "user_id", "status"),
        Index("ix_development_interventions_assignee_status", "tenant_id", "assignee_id", "status"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("development_plans.id", ondelete="SET NULL"), index=True)
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey("development_recommendations.id", ondelete="SET NULL"), index=True)
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    intervention_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

class DevelopmentInteraction(Base, TimestampMixin):
    __tablename__ = "development_interactions"
    __table_args__ = (Index("ix_development_interactions_intervention_created", "intervention_id", "created_at"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_id: Mapped[UUID] = mapped_column(ForeignKey("development_interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    facilitator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

class DevelopmentEvidence(Base, TimestampMixin):
    __tablename__ = "development_evidence"
    __table_args__ = (Index("ix_development_evidence_intervention_observed", "intervention_id", "observed_at"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_id: Mapped[UUID] = mapped_column(ForeignKey("development_interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        Index("ix_notifications_user_category", "user_id", "category"),
        Index("ix_notifications_dedupe_key", "dedupe_key"),
        UniqueConstraint("tenant_id", "dedupe_key", name="uq_notifications_tenant_dedupe_key"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(60), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="system", server_default="system", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="normal", server_default="normal", nullable=False)
    action_href: Mapped[str | None] = mapped_column(String(320))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    dedupe_key: Mapped[str | None] = mapped_column(String(240))
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(100))
    request_id: Mapped[str | None] = mapped_column(String(80), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class AIProvider(Base, TimestampMixin):
    __tablename__ = "ai_providers"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_ai_provider_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(String(1000))
    secret_ref: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default="disabled", nullable=False)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_status: Mapped[str | None] = mapped_column(String(30))
    last_check_message: Mapped[str | None] = mapped_column(Text)

class AIModel(Base, TimestampMixin):
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("tenant_id", "model_key", name="uq_ai_model_tenant_key"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_key: Mapped[str] = mapped_column(String(180), nullable=False)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class AIPromptTemplate(Base, TimestampMixin):
    __tablename__ = "ai_prompt_templates"
    __table_args__ = (UniqueConstraint("tenant_id", "name", "version", name="uq_ai_prompt_tenant_name_version"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    purpose: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    system_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)

class AIGovernancePolicy(Base, TimestampMixin):
    __tablename__ = "ai_governance_policies"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_ai_policy_tenant"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_grounding: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    employment_decisioning_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_prompt_storage_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_response_storage_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_input_chars: Mapped[int] = mapped_column(Integer, default=4000, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    daily_token_budget: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    allowed_provider_types: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

class AIInteraction(Base):
    __tablename__ = "ai_interactions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str | None] = mapped_column(String(160))
    source_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_summary: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIInteractionReview(Base):
    __tablename__ = "ai_interaction_reviews"
    __table_args__ = (UniqueConstraint("interaction_id", name="uq_ai_review_interaction"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_id: Mapped[UUID] = mapped_column(ForeignKey("ai_interactions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FileObject(Base, TimestampMixin):
    __tablename__ = "file_objects"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending_scan", nullable=False)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Program(Base, TimestampMixin):
    __tablename__ = "programs"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_program_tenant_slug"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class ProgramCourse(Base):
    __tablename__ = "program_courses"
    program_id: Mapped[UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Cohort(Base, TimestampMixin):
    __tablename__ = "cohorts"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_cohort_tenant_code"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id: Mapped[UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)

class CohortMember(Base):
    __tablename__ = "cohort_members"
    cohort_id: Mapped[UUID] = mapped_column(ForeignKey("cohorts.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

class LearningPath(Base, TimestampMixin):
    __tablename__ = "learning_paths"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_learning_path_tenant_slug"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)

class LearningPathItem(Base):
    __tablename__ = "learning_path_items"
    path_id: Mapped[UUID] = mapped_column(ForeignKey("learning_paths.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prerequisite_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))

class LiveSession(Base, TimestampMixin):
    __tablename__ = "live_sessions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("live_session_id", "user_id", name="uq_attendance_session_user"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    live_session_id: Mapped[UUID] = mapped_column(ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="absent", nullable=False)
    marked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class CourseSkill(Base):
    __tablename__ = "course_skills"
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    target_proficiency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    required_proficiency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class Integration(Base, TimestampMixin):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("tenant_id", "provider", name="uq_integration_tenant_provider"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="configured", nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_status: Mapped[str | None] = mapped_column(String(30))
    last_check_message: Mapped[str | None] = mapped_column(Text)

class SavedReport(Base, TimestampMixin):
    __tablename__ = "saved_reports"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_saved_report_tenant_name"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class ReportSchedule(Base, TimestampMixin):
    __tablename__ = "report_schedules"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_report_id: Mapped[UUID] = mapped_column(ForeignKey("saved_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recipients: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

class ReportScheduleRun(Base, TimestampMixin):
    __tablename__ = "report_schedule_runs"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("report_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)
    output_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

class WebhookEndpoint(Base, TimestampMixin):
    __tablename__ = "webhook_endpoints"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    secret_encrypted: Mapped[str | None] = mapped_column(Text)
    secret_key_id: Mapped[str | None] = mapped_column(String(80))
    event_types: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class LearningStatement(Base):
    __tablename__ = "learning_statements"
    __table_args__ = (UniqueConstraint("tenant_id", "statement_id", name="uq_learning_statement_tenant_id"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_id: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    verb: Mapped[str] = mapped_column(String(500), nullable=False)
    object_id: Mapped[str] = mapped_column(String(1000), nullable=False)
    statement: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseEquivalency(Base, TimestampMixin):
    __tablename__ = "course_equivalencies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "course_id", "equivalent_course_id", name="uq_course_equivalency_tenant_pair"),
        CheckConstraint("course_id <> equivalent_course_id", name="ck_course_equivalency_distinct_courses"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    equivalent_course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    equivalency_type: Mapped[str] = mapped_column(String(40), default="full", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MarketingInquiry(Base, TimestampMixin):
    __tablename__ = "marketing_inquiries"
    __table_args__ = (Index("ix_marketing_inquiries_created_at", "created_at"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    work_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(160))
    message: Mapped[str | None] = mapped_column(String(1200))
    request_type: Mapped[str] = mapped_column(String(30), default="demo", nullable=False, index=True)
    plan_code: Mapped[str | None] = mapped_column(String(80), index=True)
    source: Mapped[str] = mapped_column(String(120), default="website", nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), index=True)
    country_name: Mapped[str | None] = mapped_column(String(120))
    organization_size: Mapped[str | None] = mapped_column(String(60))
    business_phone: Mapped[str | None] = mapped_column(String(80))
    primary_objective: Mapped[str | None] = mapped_column(String(180), index=True)
    evaluation_timeline: Mapped[str | None] = mapped_column(String(80))
    utm_source: Mapped[str | None] = mapped_column(String(120))
    utm_medium: Mapped[str | None] = mapped_column(String(120))
    utm_campaign: Mapped[str | None] = mapped_column(String(160))
    landing_path: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(24), default="new", nullable=False, index=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    crm_account_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_accounts.id", ondelete="SET NULL"), index=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SaaSPlan(Base, TimestampMixin):
    __tablename__ = "saas_plans"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    billing_model: Mapped[str] = mapped_column(String(40), default="per_user", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    monthly_price_minor: Mapped[int | None] = mapped_column(Integer)
    annual_price_minor: Mapped[int | None] = mapped_column(Integer)
    trial_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minimum_seats: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    maximum_seats: Mapped[int | None] = mapped_column(Integer)
    features: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    __table_args__ = (UniqueConstraint("ops_tenant_id", "code", name="uq_saas_plan_ops_code"),)


class SaaSOffer(Base, TimestampMixin):
    __tablename__ = "saas_offers"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("saas_plans.id", ondelete="SET NULL"), index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(30), default="percent", nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("ops_tenant_id", "code", name="uq_saas_offer_ops_code"),)


class CRMAccount(Base, TimestampMixin):
    __tablename__ = "crm_accounts"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    managed_tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("saas_plans.id", ondelete="SET NULL"), index=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), default="prospect", nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(30), default="lead", nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    website: Mapped[str | None] = mapped_column(String(500))
    employee_band: Mapped[str | None] = mapped_column(String(60))
    public_showcase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(1000))
    testimonial: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    __table_args__ = (UniqueConstraint("ops_tenant_id", "slug", name="uq_crm_account_ops_slug"),)


class CRMContact(Base, TimestampMixin):
    __tablename__ = "crm_contacts"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(180))
    phone: Mapped[str | None] = mapped_column(String(60))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class CRMTrial(Base, TimestampMixin):
    __tablename__ = "crm_trials"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("saas_plans.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False, index=True)
    seats: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class CRMSubscription(Base, TimestampMixin):
    __tablename__ = "crm_subscriptions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    managed_tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("saas_plans.id", ondelete="SET NULL"), index=True)
    offer_id: Mapped[UUID | None] = mapped_column(ForeignKey("saas_offers.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(20), default="annual", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    seats: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    list_price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renews_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_ref: Mapped[str | None] = mapped_column(String(160))


class CRMOpportunity(Base, TimestampMixin):
    __tablename__ = "crm_opportunities"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    stage: Mapped[str] = mapped_column(String(40), default="discovery", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    probability_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class CRMSalesActivity(Base, TimestampMixin):
    __tablename__ = "crm_sales_activities"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    activity_type: Mapped[str] = mapped_column(String(40), default="note", nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CRMContract(Base, TimestampMixin):
    __tablename__ = "crm_contracts"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_subscriptions.id", ondelete="SET NULL"), index=True)
    reference: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_value_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewal_terms: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("ops_tenant_id", "reference", name="uq_crm_contract_ops_reference"),)


class CRMInvoice(Base, TimestampMixin):
    __tablename__ = "crm_invoices"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_subscriptions.id", ondelete="SET NULL"), index=True)
    contract_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_contracts.id", ondelete="SET NULL"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_ref: Mapped[str | None] = mapped_column(String(180))
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("ops_tenant_id", "invoice_number", name="uq_crm_invoice_ops_number"),)


class CRMPayment(Base, TimestampMixin):
    __tablename__ = "crm_payments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("crm_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    method: Mapped[str | None] = mapped_column(String(60))
    reference: Mapped[str | None] = mapped_column(String(180))
    notes: Mapped[str | None] = mapped_column(Text)


class CRMTask(Base, TimestampMixin):
    __tablename__ = "crm_tasks"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), index=True)
    subscription_id: Mapped[UUID | None] = mapped_column(ForeignKey("crm_subscriptions.id", ondelete="CASCADE"), index=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    task_type: Mapped[str] = mapped_column(String(50), default="follow_up", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_key: Mapped[str | None] = mapped_column(String(180))
    __table_args__ = (UniqueConstraint("ops_tenant_id", "source_key", name="uq_crm_task_ops_source_key"),)


class CRMOnboardingItem(Base, TimestampMixin):
    __tablename__ = "crm_onboarding_items"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    managed_tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


class SaaSCertification(Base, TimestampMixin):
    __tablename__ = "saas_certifications"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ops_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    issuer: Mapped[str] = mapped_column(String(180), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_url: Mapped[str | None] = mapped_column(String(1000))
    display_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
class CapabilityRisk(Base, TimestampMixin):
    __tablename__ = "capability_risks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "capability_id", name="uq_capability_risk_tenant_capability"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_capability_risk_score"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    gap_severity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    criticality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    strategic_importance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    people_exposure_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    critical_role_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    evidence_confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    assessment_age_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    development_inactivity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    certification_expiry_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    concentration_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    compliance_impact_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    trend_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    affected_people: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    affected_roles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_roles_affected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    development_active_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assessment_age_days: Mapped[int | None] = mapped_column(Integer)
    certification_expiring_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calculation_version: Mapped[str] = mapped_column(String(30), nullable=False, default="phase5.v1")
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DevelopmentRecommendation(Base, TimestampMixin):
    __tablename__ = "development_recommendations"
    __table_args__ = (
        Index("ix_development_recommendations_tenant_user", "tenant_id", "user_id"),
        Index("ix_development_recommendations_gap", "tenant_id", "capability_gap_id"),
        UniqueConstraint("tenant_id", "user_id", "capability_gap_id", "intervention_type", "source_type", "source_id", name="uq_development_recommendation_target"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_development_recommendation_score"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_gap_id: Mapped[UUID] = mapped_column(ForeignKey("capability_gaps.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    timeframe_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="recommended", nullable=False)
    recommendation_version: Mapped[str] = mapped_column(String(30), default="phase6.v1", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
