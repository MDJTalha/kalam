from __future__ import annotations

import os
import httpx

BASE = os.getenv("CORPLMS_API", "http://127.0.0.1:8000/api/v1")
PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "DemoOnly!1234")
TENANT = os.getenv("SEED_TENANT_SLUG", "demo-corporation")

def login(client: httpx.Client, email: str) -> None:
    response = client.post(f"{BASE}/auth/login", json={"tenant_slug": TENANT, "email": email, "password": PASSWORD})
    response.raise_for_status()

def must(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

with httpx.Client() as public:
    health = public.get(f"{BASE}/health")
    health.raise_for_status()
    must(health.json()["status"] == "ok", "health failed")

with httpx.Client() as admin:
    login(admin, "admin@demo.corp")
    me = admin.get(f"{BASE}/auth/me")
    me.raise_for_status()
    must(me.json()["email"] == "admin@demo.corp", "admin identity failed")

    people = admin.get(f"{BASE}/people")
    people.raise_for_status()
    must(len(people.json()) >= 4, "expected demo people")

    existing_courses = admin.get(f"{BASE}/courses")
    existing_courses.raise_for_status()
    existing = next((item for item in existing_courses.json() if item["slug"] == "smoke-test-course"), None)
    if existing:
        course_id = existing["id"]
    else:
        course = admin.post(
            f"{BASE}/courses",
            json={
                "title": "Smoke Test Course",
                "slug": "smoke-test-course",
                "description": "Automated integration-test course.",
                "estimated_minutes": 10,
            },
        )
        course.raise_for_status()
        course_id = course.json()["id"]

    module = admin.post(
        f"{BASE}/courses/{course_id}/modules",
        json={"title": "Smoke Module", "position": 1},
    )
    module.raise_for_status()
    module_id = module.json()["id"]

    lesson = admin.post(
        f"{BASE}/courses/{course_id}/modules/{module_id}/lessons",
        json={
            "title": "Smoke Lesson",
            "content_type": "rich_text",
            "content": {"body": "Automated test content."},
            "position": 1,
        },
    )
    lesson.raise_for_status()
    lesson_id = lesson.json()["id"]

    published = admin.post(f"{BASE}/courses/{course_id}/publish")
    published.raise_for_status()
    must(published.json()["status"] == "published", "publish failed")

with httpx.Client() as learner:
    login(learner, "learner@demo.corp")
    courses = learner.get(f"{BASE}/courses")
    courses.raise_for_status()
    must(course_id in {item["id"] for item in courses.json()}, "published course not visible")

    enrollment = learner.post(f"{BASE}/courses/{course_id}/enroll")
    enrollment.raise_for_status()
    enrollment_id = enrollment.json()["id"]

    completed = learner.post(
        f"{BASE}/courses/my/enrollments/{enrollment_id}/lessons/{lesson_id}/complete"
    )
    completed.raise_for_status()
    must(completed.json()["status"] == "completed", "lesson/course completion failed")

with httpx.Client() as admin:
    login(admin, "admin@demo.corp")
    assessment = admin.post(
        f"{BASE}/assessments",
        json={
            "title": "Smoke Assessment",
            "course_id": course_id,
            "passing_score": 70,
            "max_attempts": 2,
        },
    )
    assessment.raise_for_status()
    assessment_id = assessment.json()["id"]

    question = admin.post(
        f"{BASE}/assessments/{assessment_id}/questions",
        json={
            "question_type": "single_choice",
            "prompt": "Which action is responsible?",
            "options": ["Report the concern", "Ignore it"],
            "answer_key": {"correct": "Report the concern"},
            "points": 1,
            "position": 1,
        },
    )
    question.raise_for_status()
    question_id = question.json()["id"]

with httpx.Client() as learner:
    login(learner, "learner@demo.corp")
    detail = learner.get(f"{BASE}/assessments/{assessment_id}")
    detail.raise_for_status()
    visible = detail.json()["questions"][0]
    must("answer_key" not in visible, "assessment leaked answer key")

    submission = learner.post(
        f"{BASE}/assessments/{assessment_id}/submit",
        json={"answers": {question_id: "Report the concern"}},
    )
    submission.raise_for_status()
    result = submission.json()
    must(result["passed"] is True, "assessment should pass")
    must(result["certificate_id"] is not None, "certificate should be issued")

    certificates = learner.get(f"{BASE}/certificates/my")
    certificates.raise_for_status()
    certificate = next(item for item in certificates.json() if item["id"] == result["certificate_id"])

with httpx.Client() as public:
    verification = public.get(f"{BASE}/certificates/verify/{certificate['verification_code']}")
    verification.raise_for_status()
    must(verification.json()["valid"] is True, "certificate verification failed")

print("SMOKE TEST PASSED")
print(f"course_id={course_id}")
print(f"assessment_id={assessment_id}")
print(f"certificate_id={certificate['id']}")
