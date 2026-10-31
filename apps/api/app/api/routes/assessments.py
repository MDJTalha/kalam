from secrets import token_urlsafe
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import false, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, user_has_permission
from app.db.models import Assessment, AssessmentAttempt, AuditLog, Certificate, Course, Enrollment, LiveSession, Question, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()

async def ensure_editable(db: AsyncSession, assessment_id: UUID):
    count = await db.scalar(select(func.count(AssessmentAttempt.id)).where(AssessmentAttempt.assessment_id == assessment_id))
    if count:
        raise HTTPException(status_code=409, detail="This assessment has attempts. Clone it to revise its questions.")


async def _assessment_scope(
    assessment: Assessment,
    user: User,
    db: AsyncSession,
) -> str | None:
    """Resolve an assessment to administrator, assigned instructor, or enrolled learner scope."""
    if await user_has_permission(user, db, "assessments.manage"):
        return "manage"
    if assessment.course_id is None:
        return None
    if await user_has_permission(user, db, "assessments.grade_assigned"):
        assigned_session = await db.scalar(
            select(LiveSession.id).where(
                LiveSession.tenant_id == user.tenant_id,
                LiveSession.course_id == assessment.course_id,
                LiveSession.instructor_id == user.id,
            ).limit(1)
        )
        if assigned_session is not None:
            return "grade"
    if await user_has_permission(user, db, "learning.access"):
        enrolled = await db.scalar(
            select(Enrollment.id).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.course_id == assessment.course_id,
                Enrollment.user_id == user.id,
                Enrollment.status.notin_(("rejected", "cancelled")),
            ).limit(1)
        )
        if enrolled is not None:
            return "learner"
    return None


async def _get_assessment_with_scope(
    assessment_id: UUID,
    user: User,
    db: AsyncSession,
) -> tuple[Assessment, str]:
    assessment = await db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.tenant_id == user.tenant_id,
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    scope = await _assessment_scope(assessment, user, db)
    if scope is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment, scope

class AssessmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    course_id: UUID | None = None
    passing_score: int = Field(default=70, ge=0, le=100)
    max_attempts: int | None = Field(default=None, ge=1)
    time_limit_minutes: int | None = Field(default=None, ge=1)
    assessment_type: str = Field(default="knowledge_test", pattern="^(self|manager|assessor|360|knowledge_test|practical|evidence_review)$")
    measurement_method: str = Field(default="score_based", pattern="^(score_based|level_based|review_based|360_aggregate)$")
    validity_days: int | None = Field(default=None, ge=1)
    reassessment_interval_days: int | None = Field(default=None, ge=1)
    instructions: str | None = Field(default=None, max_length=4000)

class QuestionCreate(BaseModel):
    question_type: str = Field(default="single_choice")
    prompt: str = Field(min_length=3)
    options: list = Field(default_factory=list)
    answer_key: dict
    points: int = Field(default=1, ge=1)
    position: int = Field(ge=1)

    @model_validator(mode="after")
    def valid_answers(self):
        if self.question_type not in ("single_choice", "multiple_choice"):
            raise ValueError("Unsupported question type")
        if len(self.options) < 2 or not all(isinstance(option, str) and option.strip() for option in self.options):
            raise ValueError("Provide at least two nonempty options")
        if len(set(self.options)) != len(self.options):
            raise ValueError("Options must be unique")
        correct = self.answer_key.get("correct")
        if self.question_type == "single_choice" and (not isinstance(correct, str) or correct not in self.options):
            raise ValueError("Choose one correct option from the options")
        if self.question_type == "multiple_choice" and (not isinstance(correct, list) or not correct or any(option not in self.options for option in correct) or len(set(correct)) != len(correct)):
            raise ValueError("Choose distinct correct options from the options")
        return self

class SubmitAttempt(BaseModel):
    attempt_id: UUID | None = None
    answers: dict[str, object] = Field(default_factory=dict)

class ManualGrade(BaseModel):
    score: int = Field(ge=0, le=100)
    passed: bool
    feedback: str | None = Field(default=None, max_length=4000)
    reason: str = Field(min_length=3, max_length=2000)

class AssessmentResult(BaseModel):
    attempt_id: UUID
    score: int
    passed: bool
    feedback: str | None = None
    certificate_id: UUID | None = None

@router.get("")
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    can_manage = await user_has_permission(user, db, "assessments.manage")
    can_grade_assigned = await user_has_permission(user, db, "assessments.grade_assigned")
    can_learn = await user_has_permission(user, db, "learning.access")
    if not (can_manage or can_grade_assigned or can_learn):
        raise HTTPException(status_code=403, detail="Assessment access is restricted")
    stmt = (
        select(Assessment, Course.title, func.count(Question.id))
        .outerjoin(Course, Course.id == Assessment.course_id)
        .outerjoin(Question, Question.assessment_id == Assessment.id)
        .where(Assessment.tenant_id == user.tenant_id)
    )
    if not can_manage:
        if not can_grade_assigned:
            stmt = stmt.where(Assessment.active.is_(True))
        accessible_course_ids: set[UUID] = set()
        if can_grade_assigned:
            assigned_courses = await db.execute(
                select(LiveSession.course_id).where(
                    LiveSession.tenant_id == user.tenant_id,
                    LiveSession.instructor_id == user.id,
                ).distinct()
            )
            accessible_course_ids.update(assigned_courses.scalars().all())
        if can_learn:
            enrolled_courses = await db.execute(
                select(Enrollment.course_id).where(
                    Enrollment.tenant_id == user.tenant_id,
                    Enrollment.user_id == user.id,
                    Enrollment.status.notin_(("rejected", "cancelled")),
                ).distinct()
            )
            accessible_course_ids.update(enrolled_courses.scalars().all())
        stmt = stmt.where(Assessment.course_id.in_(accessible_course_ids)) if accessible_course_ids else stmt.where(false())
    result = await db.execute(
        stmt.group_by(Assessment.id, Course.title).order_by(Assessment.title.asc())
    )
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "course_id": str(item.course_id) if item.course_id else None,
            "course_title": course_title,
            "question_count": question_count,
            "passing_score": item.passing_score,
            "max_attempts": item.max_attempts,
            "time_limit_minutes": item.time_limit_minutes,
            "assessment_type": item.assessment_type,
            "measurement_method": item.measurement_method,
            "validity_days": item.validity_days,
            "reassessment_interval_days": item.reassessment_interval_days,
            "active": item.active,
        }
        for item, course_title, question_count in result.all()
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    user: User = Depends(require_permission("assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    if payload.course_id:
        course = await db.scalar(select(Course).where(Course.id == payload.course_id, Course.tenant_id == user.tenant_id))
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
    assessment = Assessment(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(assessment)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.created", entity_type="assessment", entity_id=str(assessment.id))
    await db.commit()
    return {"id": str(assessment.id), "title": assessment.title}

@router.post("/{assessment_id}/questions", status_code=status.HTTP_201_CREATED)
async def create_question(
    assessment_id: UUID,
    payload: QuestionCreate,
    user: User = Depends(require_permission("assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    await ensure_editable(db, assessment.id)
    question = Question(assessment_id=assessment.id, **payload.model_dump())
    db.add(question)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.question.created", entity_type="question", entity_id=str(question.id))
    await db.commit()
    return {"id": str(question.id), "position": question.position}

@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope == "learner" and not assessment.active:
        raise HTTPException(status_code=404, detail="Assessment not found")
    questions = await db.execute(
        select(Question.id, Question.question_type, Question.prompt, Question.options, Question.points, Question.position)
        .where(Question.assessment_id == assessment.id)
        .order_by(Question.position.asc())
    )
    return {
        "id": str(assessment.id),
        "title": assessment.title,
        "passing_score": assessment.passing_score,
        "max_attempts": assessment.max_attempts,
        "time_limit_minutes": assessment.time_limit_minutes,
        "questions": [
            {
                "id": str(q.id),
                "question_type": q.question_type,
                "prompt": q.prompt,
                "options": q.options,
                "points": q.points,
                "position": q.position,
            }
            for q in questions.all()
        ],
    }

def grade(question: Question, answer: object) -> float:
    expected = question.answer_key.get("correct")
    if question.question_type == "multiple_choice":
        return 1.0 if sorted(answer if isinstance(answer, list) else []) == sorted(expected or []) else 0.0
    return 1.0 if answer == expected else 0.0


@router.post("/{assessment_id}/start", status_code=status.HTTP_201_CREATED)
async def start_assessment(
    assessment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope != "learner":
        raise HTTPException(status_code=403, detail="Only enrolled learners can start this assessment")
    if not assessment.active:
        raise HTTPException(status_code=409, detail="This assessment is no longer active")

    question_count = await db.scalar(select(func.count(Question.id)).where(Question.assessment_id == assessment.id))
    if not question_count:
        raise HTTPException(status_code=422, detail="Assessment has no questions")
    attempts_count = await db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
        )
    )
    pending = await db.scalar(select(AssessmentAttempt).where(
        AssessmentAttempt.assessment_id == assessment.id,
        AssessmentAttempt.user_id == user.id,
        AssessmentAttempt.submitted_at.is_(None),
    ).order_by(AssessmentAttempt.started_at.desc()))
    if pending is not None:
        return {"attempt_id": str(pending.id), "attempt_number": pending.attempt_number,
                "started_at": pending.started_at, "time_limit_minutes": assessment.time_limit_minutes}
    if assessment.max_attempts is not None and (attempts_count or 0) >= assessment.max_attempts:
        raise HTTPException(status_code=422, detail="Maximum assessment attempts reached")

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        user_id=user.id,
        attempt_number=(attempts_count or 0) + 1,
    )
    db.add(attempt)
    await db.flush()
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="assessment.started",
        entity_type="assessment_attempt",
        entity_id=str(attempt.id),
    )
    await db.commit()
    return {
        "attempt_id": str(attempt.id),
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "time_limit_minutes": assessment.time_limit_minutes,
    }


@router.post("/{assessment_id}/submit", response_model=AssessmentResult)
async def submit_assessment(
    assessment_id: UUID,
    payload: SubmitAttempt,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope != "learner":
        raise HTTPException(status_code=403, detail="Only enrolled learners can submit this assessment")
    if not assessment.active:
        raise HTTPException(status_code=409, detail="This assessment is no longer active")
    attempts_count = await db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
        )
    )

    if assessment.time_limit_minutes and payload.attempt_id is None:
        raise HTTPException(status_code=422, detail="A started attempt is required for a timed assessment")
    if payload.attempt_id:
        attempt = await db.scalar(
            select(AssessmentAttempt).where(
                AssessmentAttempt.id == payload.attempt_id,
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.user_id == user.id,
            )
        )
        if attempt is None:
            raise HTTPException(status_code=404, detail="Assessment attempt not found")
        if attempt.submitted_at is not None:
            raise HTTPException(status_code=409, detail="Assessment attempt has already been submitted")
        if (
            assessment.time_limit_minutes
            and attempt.started_at + timedelta(minutes=assessment.time_limit_minutes) < datetime.now(timezone.utc)
        ):
            attempt.answers = payload.answers
            attempt.score = 0
            attempt.passed = False
            attempt.feedback = "Attempt exceeded the configured time limit."
            attempt.submitted_at = datetime.now(timezone.utc)
            await audit(
                db,
                tenant_id=user.tenant_id,
                actor_id=user.id,
                action="assessment.time_limit_exceeded",
                entity_type="assessment_attempt",
                entity_id=str(attempt.id),
            )
            await db.commit()
            return AssessmentResult(
                attempt_id=attempt.id,
                score=0,
                passed=False,
                feedback=attempt.feedback,
                certificate_id=None,
            )
    else:
        if assessment.max_attempts is not None and (attempts_count or 0) >= assessment.max_attempts:
            raise HTTPException(status_code=422, detail="Maximum assessment attempts reached")
        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            user_id=user.id,
            attempt_number=(attempts_count or 0) + 1,
        )
        db.add(attempt)
        await db.flush()

    questions_result = await db.execute(select(Question).where(Question.assessment_id == assessment.id))
    questions = list(questions_result.scalars().all())
    if not questions:
        raise HTTPException(status_code=422, detail="Assessment has no questions")

    total_points = sum(q.points for q in questions)
    scored = sum(q.points * grade(q, payload.answers.get(str(q.id))) for q in questions)
    score = round((scored / total_points) * 100) if total_points else 0
    passed = score >= assessment.passing_score

    attempt.answers = payload.answers
    attempt.score = score
    attempt.passed = passed
    attempt.submitted_at = datetime.now(timezone.utc)

    certificate_id = None
    if passed and assessment.course_id:
        enrollment = await db.scalar(select(Enrollment).where(
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.user_id == user.id,
            Enrollment.course_id == assessment.course_id,
            Enrollment.status == "completed",
        ))
        existing_cert = await db.scalar(select(Certificate).where(
            Certificate.tenant_id == user.tenant_id,
            Certificate.user_id == user.id,
            Certificate.course_id == assessment.course_id,
            Certificate.revoked_at.is_(None),
        ))
        if enrollment and existing_cert is None:
            certificate = Certificate(
                tenant_id=user.tenant_id,
                user_id=user.id,
                course_id=assessment.course_id,
                verification_code=token_urlsafe(24),
            )
            db.add(certificate)
            await db.flush()
            certificate_id = certificate.id
            await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="certificate.issued", entity_type="certificate", entity_id=str(certificate.id))
            await create_notification(
                db,
                tenant_id=user.tenant_id,
                user_id=user.id,
                notification_type="credential.issued",
                title="Certificate issued",
                body="Your assessment result qualified you for a learning credential.",
            )
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.submitted", entity_type="assessment_attempt", entity_id=str(attempt.id), metadata={"score": score, "passed": passed})
    await db.commit()
    return AssessmentResult(
        attempt_id=attempt.id,
        score=score,
        passed=passed,
        feedback=attempt.feedback,
        certificate_id=certificate_id,
    )


@router.get("/attempts/{attempt_id}/detail")
async def attempt_detail(
    attempt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AssessmentAttempt, Assessment, User)
        .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(
            AssessmentAttempt.id == attempt_id,
            Assessment.tenant_id == user.tenant_id,
            User.tenant_id == user.tenant_id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")

    attempt, assessment, learner = row
    scope = await _assessment_scope(assessment, user, db)
    if scope not in {"manage", "grade"} or attempt.submitted_at is None:
        raise HTTPException(status_code=404, detail="Submitted assessment attempt not found")
    questions_result = await db.execute(
        select(Question)
        .where(Question.assessment_id == assessment.id)
        .order_by(Question.position.asc())
    )
    questions = list(questions_result.scalars().all())

    audit_result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.entity_type == "assessment_attempt",
            AuditLog.entity_id == str(attempt.id),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )

    answer_rows = []
    for question in questions:
        answer = attempt.answers.get(str(question.id))
        answered = str(question.id) in attempt.answers
        answer_rows.append({
            "question_id": str(question.id),
            "position": question.position,
            "prompt": question.prompt,
            "question_type": question.question_type,
            "points": question.points,
            "answer": answer,
            "answered": answered,
            "correct": grade(question, answer) == 1.0 if answered else False,
        })

    return {
        "id": str(attempt.id),
        "assessment_id": str(assessment.id),
        "assessment_title": assessment.title,
        "learner": {
            "id": str(learner.id),
            "name": f"{learner.first_name} {learner.last_name}",
            "email": learner.email,
            "employee_number": learner.employee_number,
            "job_title": learner.job_title,
        },
        "attempt_number": attempt.attempt_number,
        "score": attempt.score,
        "passed": attempt.passed,
        "feedback": attempt.feedback,
        "grade_override": attempt.grade_override,
        "grade_override_reason": attempt.grade_override_reason,
        "graded_by": str(attempt.graded_by) if attempt.graded_by else None,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "questions": answer_rows,
        "audit_events": [
            {
                "id": str(event.id),
                "action": event.action,
                "actor_id": str(event.actor_id) if event.actor_id else None,
                "summary": event.summary,
                "metadata": event.record_metadata,
                "created_at": event.created_at,
            }
            for event in audit_result.scalars().all()
        ],
    }


@router.get("/{assessment_id}/attempts")
async def list_attempts(
    assessment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope not in {"manage", "grade"}:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await db.execute(
        select(AssessmentAttempt, User)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(AssessmentAttempt.assessment_id == assessment.id)
        .where(User.tenant_id == user.tenant_id)
        .order_by(AssessmentAttempt.started_at.desc())
    )
    return [
        {
            "id": str(attempt.id),
            "learner_id": str(attempt.user_id),
            "learner": f"{person.first_name} {person.last_name}",
            "attempt_number": attempt.attempt_number,
            "score": attempt.score,
            "passed": attempt.passed,
            "feedback": attempt.feedback,
            "grade_override": attempt.grade_override,
            "started_at": attempt.started_at,
            "submitted_at": attempt.submitted_at,
        }
        for attempt, person in result.all()
    ]


@router.patch("/attempts/{attempt_id}/grade", response_model=AssessmentResult)
async def override_grade(
    attempt_id: UUID,
    payload: ManualGrade,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AssessmentAttempt, Assessment)
        .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(
            AssessmentAttempt.id == attempt_id,
            Assessment.tenant_id == user.tenant_id,
            User.tenant_id == user.tenant_id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")

    attempt, assessment = row
    scope = await _assessment_scope(assessment, user, db)
    if scope not in {"manage", "grade"}:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.user_id == user.id:
        raise HTTPException(status_code=403, detail="Reviewers cannot override their own assessment result")
    if attempt.submitted_at is None:
        raise HTTPException(status_code=409, detail="Only submitted assessment attempts can be graded")
    attempt.score = payload.score
    attempt.passed = payload.passed
    attempt.feedback = payload.feedback
    attempt.graded_by = user.id
    attempt.grade_override = True
    attempt.grade_override_reason = payload.reason

    certificate_id = None
    if payload.passed and assessment.course_id:
        enrollment = await db.scalar(
            select(Enrollment).where(
                Enrollment.tenant_id == user.tenant_id,
                Enrollment.user_id == attempt.user_id,
                Enrollment.course_id == assessment.course_id,
                Enrollment.status == "completed",
            )
        )
        existing_cert = await db.scalar(
            select(Certificate).where(
                Certificate.tenant_id == user.tenant_id,
                Certificate.user_id == attempt.user_id,
                Certificate.course_id == assessment.course_id,
                Certificate.revoked_at.is_(None),
            )
        )
        if enrollment and existing_cert is None:
            certificate = Certificate(
                tenant_id=user.tenant_id,
                user_id=attempt.user_id,
                course_id=assessment.course_id,
                verification_code=token_urlsafe(24),
            )
            db.add(certificate)
            await db.flush()
            certificate_id = certificate.id
            await audit(
                db,
                tenant_id=user.tenant_id,
                actor_id=user.id,
                action="certificate.issued",
                entity_type="certificate",
                entity_id=str(certificate.id),
                metadata={"reason": "manual_grade_override"},
            )

    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="assessment.grade.overridden",
        entity_type="assessment_attempt",
        entity_id=str(attempt.id),
        metadata={"score": payload.score, "passed": payload.passed, "reason": payload.reason},
    )
    await db.commit()
    return AssessmentResult(
        attempt_id=attempt.id,
        score=attempt.score,
        passed=attempt.passed,
        feedback=attempt.feedback,
        certificate_id=certificate_id,
    )

class QuestionReorder(BaseModel):
    question_ids: list[UUID] = Field(min_length=1)

class QuestionUpdate(BaseModel):
    question_type: str | None = None
    prompt: str | None = Field(default=None, min_length=3)
    options: list | None = None
    answer_key: dict | None = None
    points: int | None = Field(default=None, ge=1)
    position: int | None = Field(default=None, ge=1)

@router.patch('/questions/{question_id}')
async def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    user: User = Depends(require_permission('assessments.manage')),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Question, Assessment)
        .join(Assessment, Assessment.id == Question.assessment_id)
        .where(Question.id == question_id, Assessment.tenant_id == user.tenant_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail='Question not found')
    question, assessment = row
    await ensure_editable(db, assessment.id)
    changes = payload.model_dump(exclude_unset=True)
    QuestionCreate(**{**{"question_type": question.question_type, "prompt": question.prompt, "options": question.options, "answer_key": question.answer_key, "points": question.points, "position": question.position}, **changes})
    for key, value in changes.items():
        setattr(question, key, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action='assessment.question.updated', entity_type='question', entity_id=str(question.id), metadata={'fields': sorted(changes.keys())})
    await db.commit()
    return {'id': str(question.id), 'position': question.position}

@router.delete('/questions/{question_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: UUID,
    user: User = Depends(require_permission('assessments.manage')),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Question, Assessment)
        .join(Assessment, Assessment.id == Question.assessment_id)
        .where(Question.id == question_id, Assessment.tenant_id == user.tenant_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail='Question not found')
    question, assessment = row
    await ensure_editable(db, assessment.id)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action='assessment.question.deleted', entity_type='question', entity_id=str(question.id))
    await db.delete(question)
    await db.commit()

@router.post('/{assessment_id}/questions/reorder')
async def reorder_questions(
    assessment_id: UUID,
    payload: QuestionReorder,
    user: User = Depends(require_permission('assessments.manage')),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail='Assessment not found')
    await ensure_editable(db, assessment.id)
    result = await db.execute(select(Question).where(Question.assessment_id == assessment.id))
    questions = {q.id: q for q in result.scalars().all()}
    if set(payload.question_ids) != set(questions) or len(payload.question_ids) != len(questions):
        raise HTTPException(status_code=422, detail='question_ids must contain every question exactly once')
    for position, question_id in enumerate(payload.question_ids, start=1):
        questions[question_id].position = position
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action='assessment.questions.reordered', entity_type='assessment', entity_id=str(assessment.id), metadata={'count': len(payload.question_ids)})
    await db.commit()
    return {'assessment_id': str(assessment.id), 'question_ids': [str(q) for q in payload.question_ids]}

@router.get('/{assessment_id}/question-analytics')
async def question_analytics(
    assessment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope not in {"manage", "grade"}:
        raise HTTPException(status_code=404, detail='Assessment not found')
    q_result = await db.execute(select(Question).where(Question.assessment_id == assessment.id).order_by(Question.position.asc()))
    questions = list(q_result.scalars().all())
    a_result = await db.execute(
        select(AssessmentAttempt)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.submitted_at.is_not(None),
            User.tenant_id == user.tenant_id,
        )
    )
    attempts = list(a_result.scalars().all())
    rows = []
    for question in questions:
        correct = 0
        answered = 0
        for attempt in attempts:
            if str(question.id) not in attempt.answers:
                continue
            answered += 1
            if grade(question, attempt.answers.get(str(question.id))) == 1.0:
                correct += 1
        rows.append({'question_id': str(question.id), 'position': question.position, 'prompt': question.prompt, 'attempts': len(attempts), 'answered': answered, 'correct': correct, 'correct_rate': round((correct / answered) * 100, 1) if answered else 0})
    return {'assessment_id': str(assessment.id), 'submitted_attempts': len(attempts), 'questions': rows}

@router.get('/{assessment_id}/analytics')
async def assessment_analytics(
    assessment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope not in {"manage", "grade"}:
        raise HTTPException(status_code=404, detail='Assessment not found')
    result = await db.execute(
        select(AssessmentAttempt)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(
            AssessmentAttempt.assessment_id == assessment.id,
            User.tenant_id == user.tenant_id,
        )
        .order_by(AssessmentAttempt.started_at.asc())
    )
    attempts = list(result.scalars().all())
    submitted = [a for a in attempts if a.submitted_at is not None]
    passed = [a for a in submitted if a.passed is True]
    scores = [a.score for a in submitted if a.score is not None]
    return {
        'assessment_id': str(assessment.id),
        'attempts': len(attempts),
        'submitted_attempts': len(submitted),
        'passed_attempts': len(passed),
        'failed_attempts': len([a for a in submitted if a.passed is False]),
        'pass_rate': round((len(passed) / len(submitted)) * 100, 1) if submitted else 0,
        'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
        'highest_score': max(scores) if scores else None,
        'lowest_score': min(scores) if scores else None,
        'overrides': len([a for a in submitted if a.grade_override]),
        'score_distribution': {
            '0_49': len([s for s in scores if s < 50]),
            '50_69': len([s for s in scores if 50 <= s < 70]),
            '70_79': len([s for s in scores if 70 <= s < 80]),
            '80_89': len([s for s in scores if 80 <= s < 90]),
            '90_100': len([s for s in scores if s >= 90]),
        },
    }

@router.get("/{assessment_id}/my-attempts")
async def my_assessment_attempts(assessment_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    assessment, scope = await _get_assessment_with_scope(assessment_id, user, db)
    if scope != "learner":
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(select(AssessmentAttempt).where(
        AssessmentAttempt.assessment_id == assessment.id,
        AssessmentAttempt.user_id == user.id,
    ).order_by(AssessmentAttempt.attempt_number.desc()))
    return [{"id": str(item.id), "attempt_number": item.attempt_number, "started_at": item.started_at,
             "submitted_at": item.submitted_at, "score": item.score, "passed": item.passed,
             "feedback": item.feedback} for item in result.scalars().all()]

@router.get("/{assessment_id}/editor")
async def assessment_editor(assessment_id: UUID, user: User = Depends(require_permission("assessments.manage")), db: AsyncSession = Depends(get_db)):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(select(Question).where(Question.assessment_id == assessment.id).order_by(Question.position))
    attempts = await db.scalar(select(func.count(AssessmentAttempt.id)).where(AssessmentAttempt.assessment_id == assessment.id))
    return {"id": str(assessment.id), "title": assessment.title, "passing_score": assessment.passing_score,
            "max_attempts": assessment.max_attempts, "time_limit_minutes": assessment.time_limit_minutes,
            "locked": bool(attempts),
            "questions": [{"id": str(q.id), "question_type": q.question_type, "prompt": q.prompt,
                           "options": q.options, "answer_key": q.answer_key,
                           "points": q.points, "position": q.position} for q in result.scalars().all()]}

@router.post("/{assessment_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_assessment(assessment_id: UUID, user: User = Depends(require_permission("assessments.manage")), db: AsyncSession = Depends(get_db)):
    original = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if original is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    copy = Assessment(tenant_id=user.tenant_id, title=f"{original.title} (revision)", course_id=original.course_id,
                      passing_score=original.passing_score, max_attempts=original.max_attempts,
                      time_limit_minutes=original.time_limit_minutes, assessment_type=original.assessment_type,
                      measurement_method=original.measurement_method, validity_days=original.validity_days,
                      reassessment_interval_days=original.reassessment_interval_days, instructions=original.instructions)
    db.add(copy)
    await db.flush()
    questions = (await db.execute(select(Question).where(Question.assessment_id == original.id).order_by(Question.position))).scalars().all()
    for question in questions:
        db.add(Question(assessment_id=copy.id, question_type=question.question_type, prompt=question.prompt,
                        options=question.options, answer_key=question.answer_key, points=question.points,
                        position=question.position))
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.cloned", entity_type="assessment",
                entity_id=str(copy.id), metadata={"source_assessment_id": str(original.id), "questions": len(questions)})
    await db.commit()
    return {"id": str(copy.id), "title": copy.title}

class AssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    passing_score: int | None = Field(default=None, ge=0, le=100)
    max_attempts: int | None = Field(default=None, ge=1)
    time_limit_minutes: int | None = Field(default=None, ge=1)
    assessment_type: str | None = Field(default=None, pattern="^(self|manager|assessor|360|knowledge_test|practical|evidence_review)$")
    measurement_method: str | None = Field(default=None, pattern="^(score_based|level_based|review_based|360_aggregate)$")
    validity_days: int | None = Field(default=None, ge=1)
    reassessment_interval_days: int | None = Field(default=None, ge=1)
    instructions: str | None = Field(default=None, max_length=4000)

@router.patch("/{assessment_id}")
async def update_assessment(assessment_id: UUID, payload: AssessmentUpdate, user: User = Depends(require_permission("assessments.manage")), db: AsyncSession = Depends(get_db)):
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    await ensure_editable(db, assessment.id)
    values = payload.model_dump(exclude_unset=True)
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=422, detail="Use explicit values for assessment controls")
    before = {key: getattr(assessment, key) for key in values}
    for key, value in values.items():
        setattr(assessment, key, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="assessment.updated", entity_type="assessment", entity_id=str(assessment.id), metadata={"before": before, "after": values})
    await db.commit()
    return {"id": str(assessment.id), "title": assessment.title, "passing_score": assessment.passing_score,
            "max_attempts": assessment.max_attempts, "time_limit_minutes": assessment.time_limit_minutes}
