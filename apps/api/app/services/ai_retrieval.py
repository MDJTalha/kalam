from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Course,
    CourseModule,
    CourseSkill,
    Enrollment,
    Lesson,
    RoleSkillRequirement,
    Skill,
    User,
    UserRole,
    UserSkill,
)

_WORDS = re.compile(r"[a-zA-Z0-9]{2,}")
_SEMANTIC_ALIASES = {
    "manager": {"leader", "supervisor", "leadership"},
    "leader": {"manager", "leadership", "supervisor"},
    "coach": {"coaching", "mentor", "feedback", "development"},
    "coaching": {"mentor", "mentoring", "feedback", "development"},
    "mentor": {"coaching", "mentoring", "development"},
    "compliance": {"mandatory", "requirement", "required", "policy"},
    "required": {"mandatory", "requirement", "compliance"},
    "communication": {"communicate", "conversation", "feedback"},
    "feedback": {"coaching", "communication", "conversation"},
}


@dataclass(frozen=True)
class RetrievedSource:
    citation_id: str
    lesson_id: str
    course_id: str
    course_title: str
    lesson_title: str
    chunk_index: int
    text: str
    score: float


def _terms(value: str) -> set[str]:
    return {item.lower() for item in _WORDS.findall(value) if item.lower() not in {"the", "and", "for", "with", "from", "that", "this"}}


def _expanded_terms(value: str) -> set[str]:
    base = _terms(value)
    expanded = set(base)
    for term in base:
        expanded.update(_SEMANTIC_ALIASES.get(term, set()))
    return expanded


def lesson_text(lesson: Lesson) -> str:
    content = lesson.content or {}
    if isinstance(content, dict):
        parts = [lesson.title]
        for key in ("text", "body", "description", "html", "content"):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        return "\n".join(parts)
    return lesson.title


def _chunks(text: str, *, size: int = 1800, overlap: int = 250) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    if len(compact) <= size:
        return [compact]
    result: list[str] = []
    start = 0
    while start < len(compact):
        end = min(start + size, len(compact))
        result.append(compact[start:end])
        if end >= len(compact):
            break
        start = max(end - overlap, start + 1)
    return result


def _score(question_terms: set[str], chunk: str, title: str) -> float:
    chunk_terms = _expanded_terms(chunk)
    title_terms = _expanded_terms(title)
    overlap = len(question_terms & chunk_terms)
    title_overlap = len(question_terms & title_terms)
    return float(overlap) + (2.0 * title_overlap)


async def retrieve_authorized_sources(
    user: User,
    db: AsyncSession,
    question: str,
    course_id: str | None = None,
    *,
    top_k: int = 8,
    max_context_chars: int = 18000,
) -> list[RetrievedSource]:
    query = (
        select(Lesson, Course)
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .join(Course, Course.id == CourseModule.course_id)
        .join(Enrollment, (Enrollment.course_id == Course.id) & (Enrollment.user_id == user.id))
        .where(
            Course.tenant_id == user.tenant_id,
            Course.status == "published",
            Enrollment.tenant_id == user.tenant_id,
            Enrollment.status.in_(["active", "completed"]),
        )
    )
    if course_id:
        query = query.where(Course.id == course_id)
    result = await db.execute(query.order_by(Course.title, CourseModule.position, Lesson.position))
    rows = result.all()
    if not rows:
        return []

    question_terms = _expanded_terms(question)
    candidates: list[RetrievedSource] = []
    for lesson, course in rows:
        for chunk_index, chunk in enumerate(_chunks(lesson_text(lesson))):
            score = _score(question_terms, chunk, lesson.title)
            candidates.append(
                RetrievedSource(
                    citation_id="",
                    lesson_id=str(lesson.id),
                    course_id=str(course.id),
                    course_title=course.title,
                    lesson_title=lesson.title,
                    chunk_index=chunk_index,
                    text=chunk,
                    score=score,
                )
            )

    candidates.sort(key=lambda item: (-item.score, item.course_title.lower(), item.lesson_title.lower(), item.chunk_index))
    relevant = [item for item in candidates if item.score > 0]
    candidate_pool = relevant if relevant else candidates[:1]
    selected: list[RetrievedSource] = []
    used_chars = 0
    for item in candidate_pool[: max(top_k * 2, top_k)]:
        if len(selected) >= top_k:
            break
        citation = f"S{len(selected) + 1}"
        enriched = RetrievedSource(**{**item.__dict__, "citation_id": citation})
        addition = len(f"[{citation}] {enriched.course_title} — {enriched.lesson_title}\n{enriched.text}\n\n")
        if selected and used_chars + addition > max_context_chars:
            continue
        selected.append(enriched)
        used_chars += addition
    return selected


async def retrieve_capability_sources(
    user: User,
    db: AsyncSession,
    *,
    top_k: int = 8,
) -> list[RetrievedSource]:
    role_ids = list(
        (
            await db.scalars(
                select(UserRole.role_id).where(UserRole.user_id == user.id)
            )
        ).all()
    )
    if not role_ids:
        return []

    requirement_rows = (
        await db.execute(
            select(RoleSkillRequirement, Skill)
            .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
            .where(
                RoleSkillRequirement.role_id.in_(role_ids),
                Skill.tenant_id == user.tenant_id,
            )
        )
    ).all()
    if not requirement_rows:
        return []

    current_rows = (
        await db.execute(
            select(UserSkill.skill_id, UserSkill.proficiency).where(UserSkill.user_id == user.id)
        )
    ).all()
    current_by_skill = {skill_id: proficiency for skill_id, proficiency in current_rows}

    required_by_skill: dict[object, tuple[Skill, int]] = {}
    for requirement, skill in requirement_rows:
        existing = required_by_skill.get(skill.id)
        if not existing or requirement.required_proficiency > existing[1]:
            required_by_skill[skill.id] = (skill, requirement.required_proficiency)

    sources: list[RetrievedSource] = []
    for skill_id, (skill, required) in sorted(required_by_skill.items(), key=lambda item: item[1][0].name.lower()):
        current = int(current_by_skill.get(skill_id, 0))
        gap = max(required - current, 0)
        if gap <= 0:
            continue
        course_rows = (
            await db.execute(
                select(Course, CourseSkill)
                .join(CourseSkill, CourseSkill.course_id == Course.id)
                .where(
                    Course.tenant_id == user.tenant_id,
                    Course.status == "published",
                    Course.visibility == "tenant",
                    CourseSkill.skill_id == skill_id,
                )
                .order_by(CourseSkill.target_proficiency.desc(), Course.title)
                .limit(5)
            )
        ).all()
        course_labels = [f"{course.title} (target {mapping.target_proficiency})" for course, mapping in course_rows]
        primary_course = course_rows[0][0] if course_rows else None
        citation_id = f"S{len(sources) + 1}"
        text = (
            f"Skill: {skill.name}. Current proficiency: {current}. Required proficiency: {required}. "
            f"Gap: {gap}. Published tenant-visible learning options: "
            + (", ".join(course_labels) if course_labels else "none currently mapped")
            + ". This evidence is advisory learning-development context and must not be used as an employment decision."
        )
        sources.append(
            RetrievedSource(
                citation_id=citation_id,
                lesson_id=str(skill.id),
                course_id=str(primary_course.id) if primary_course else "",
                course_title=primary_course.title if primary_course else "Capability profile",
                lesson_title=f"Skill gap: {skill.name}",
                chunk_index=0,
                text=text,
                score=float(gap),
            )
        )
        if len(sources) >= top_k:
            break
    return sources


def build_grounded_context(sources: list[RetrievedSource]) -> str:
    blocks = []
    for source in sources:
        blocks.append(
            f"[{source.citation_id}] COURSE={source.course_title} | LESSON={source.lesson_title}\n"
            "UNTRUSTED_REFERENCE_CONTENT:\n"
            f"{source.text}"
        )
    return "\n\n---\n\n".join(blocks)
def public_sources(sources: list[RetrievedSource]) -> list[dict]:
    return [
        {
            "citation_id": source.citation_id,
            "lesson_id": source.lesson_id,
            "course_id": source.course_id,
            "course_title": source.course_title,
            "lesson_title": source.lesson_title,
            "chunk_index": source.chunk_index,
            "score": round(source.score, 3),
        }
        for source in sources
    ]
