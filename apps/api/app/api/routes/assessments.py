from secrets import token_urlsafe
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import Assessment, AssessmentAttempt, Certificate, Course, Enrollment, Question, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.notifications import create_notification

router = APIRouter()

class AssessmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    course_id: UUID | None = None
    passing_score: int = Field(default=70, ge=0, le=100)
    max_attempts: int | None = Field(default=None, ge=1)
    time_limit_minutes: int | None = Field(default=None, ge=1)

class QuestionCreate(BaseModel):
    question_type: str = Field(default="single_choice")
    prompt: str = Field(min_length=3)
    options: list = Field(default_factory=list)
    answer_key: dict
    points: int = Field(default=1, ge=1)
    position: int = Field(ge=1)

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
    result = await db.execute(
        select(Assessment)
        .where(Assessment.tenant_id == user.tenant_id)
        .order_by(Assessment.title.asc())
    )
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "course_id": str(item.course_id) if item.course_id else None,
            "passing_score": item.passing_score,
            "max_attempts": item.max_attempts,
            "time_limit_minutes": item.time_limit_minutes,
        }
        for item in result.scalars().all()
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
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
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
    assessment = await db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.tenant_id == user.tenant_id,
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    attempts_count = await db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
        )
    )
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
    assessment = await db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.tenant_id == user.tenant_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    attempts_count = await db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
        )
    )

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


@router.get("/{assessment_id}/attempts")
async def list_attempts(
    assessment_id: UUID,
    user: User = Depends(require_permission("assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.tenant_id == user.tenant_id,
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await db.execute(
        select(AssessmentAttempt, User)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(AssessmentAttempt.assessment_id == assessment.id)
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
    user: User = Depends(require_permission("assessments.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AssessmentAttempt, Assessment)
        .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
        .where(
            AssessmentAttempt.id == attempt_id,
            Assessment.tenant_id == user.tenant_id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")

    attempt, assessment = row
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
