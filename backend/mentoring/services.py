"""Агрегация статистики для панели ментора."""

from __future__ import annotations

from content.models import Course
from education.models import Enrollment
from progress.models import (
    CodeSubmission,
    UserAnswerCheckBox,
    UserAnswerRadio,
)
from progress.stats import get_course_progress_detail


def build_courses_overview() -> list[dict]:
    results = []
    for course in Course.objects.filter(is_active=True).order_by("title"):
        enrollments = Enrollment.objects.filter(course=course)
        percents = []
        for enrollment in enrollments.select_related("user"):
            detail = get_course_progress_detail(enrollment.user, course)
            percents.append(detail["percent"])

        results.append(
            {
                "course_public_id": str(course.public_id),
                "course_title": course.title,
                "course_slug": course.slug,
                "students_count": enrollments.count(),
                "active_count": enrollments.filter(
                    status=Enrollment.Status.ACTIVE
                ).count(),
                "completed_count": enrollments.filter(
                    status=Enrollment.Status.COMPLETED
                ).count(),
                "avg_percent": (
                    round(sum(percents) / len(percents)) if percents else 0
                ),
            }
        )
    return results


def build_course_students(course: Course) -> list[dict]:
    rows = []
    enrollments = (
        Enrollment.objects.filter(course=course)
        .select_related("user")
        .order_by("-last_activity_at")
    )
    for enrollment in enrollments:
        user = enrollment.user
        detail = get_course_progress_detail(user, course)
        rows.append(
            {
                "user_public_id": str(user.public_id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
                "enrollment_status": enrollment.status,
                "percent": detail["percent"],
                "completed_steps": detail["completed_steps"],
                "total_steps": detail["total_steps"],
                "started_at": enrollment.started_at.isoformat(),
                "last_activity_at": enrollment.last_activity_at.isoformat(),
            }
        )
    return rows


def _student_brief(user) -> dict:
    return {
        "public_id": str(user.public_id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
    }


def build_code_submissions_payload(
    *,
    course_public_id: str | None = None,
    user_public_id: str | None = None,
    challenge_public_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    qs = CodeSubmission.objects.select_related(
        "user",
        "challenge",
        "challenge__module",
        "challenge__module__course",
    ).order_by("-submitted_at")

    if course_public_id:
        qs = qs.filter(challenge__module__course__public_id=course_public_id)
    if user_public_id:
        qs = qs.filter(user__public_id=user_public_id)
    if challenge_public_id:
        qs = qs.filter(challenge__public_id=challenge_public_id)

    rows = []
    for sub in qs[:limit]:
        course = (
            sub.challenge.module.course if sub.challenge.module_id else None
        )
        module = sub.challenge.module if sub.challenge.module_id else None
        rows.append(
            {
                "public_id": str(sub.public_id),
                "student": _student_brief(sub.user),
                "course_public_id": str(course.public_id) if course else None,
                "course_title": course.title if course else None,
                "module_public_id": str(module.public_id) if module else None,
                "challenge_public_id": str(sub.challenge.public_id),
                "challenge_title": sub.challenge.title,
                "code": sub.code,
                "status": sub.status,
                "tests_passed": sub.tests_passed,
                "total_tests": sub.total_tests,
                "test_results": sub.test_results or {},
                "error_message": sub.error_message,
                "submitted_at": sub.submitted_at.isoformat(),
                "completed_at": (
                    sub.completed_at.isoformat() if sub.completed_at else None
                ),
            }
        )
    return rows


def build_quiz_answers_payload(
    *,
    course_public_id: str | None = None,
    user_public_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    radio_qs = UserAnswerRadio.objects.select_related(
        "user",
        "question",
        "question__module",
        "question__module__course",
        "selected_answer",
    ).order_by("-created_at")
    checkbox_qs = (
        UserAnswerCheckBox.objects.select_related(
            "user",
            "question",
            "question__module",
            "question__module__course",
        )
        .prefetch_related("selected_answers")
        .order_by("-created_at")
    )

    if course_public_id:
        radio_qs = radio_qs.filter(
            question__module__course__public_id=course_public_id
        )
        checkbox_qs = checkbox_qs.filter(
            question__module__course__public_id=course_public_id
        )
    if user_public_id:
        radio_qs = radio_qs.filter(user__public_id=user_public_id)
        checkbox_qs = checkbox_qs.filter(user__public_id=user_public_id)

    rows = []
    for ans in radio_qs[:limit]:
        course = ans.question.module.course
        module = ans.question.module
        rows.append(
            {
                "kind": "radio",
                "public_id": str(ans.public_id),
                "student": _student_brief(ans.user),
                "course_public_id": str(course.public_id),
                "course_title": course.title,
                "module_public_id": str(module.public_id),
                "question_public_id": str(ans.question.public_id),
                "question_title": ans.question.title,
                "selected_answer": ans.selected_answer.text,
                "is_correct": ans.is_correct,
                "points_earned": ans.points_earned,
                "created_at": ans.created_at.isoformat(),
            }
        )
    for ans in checkbox_qs[:limit]:
        course = ans.question.module.course
        module = ans.question.module
        selected = list(ans.selected_answers.values_list("text", flat=True))
        rows.append(
            {
                "kind": "checkbox",
                "public_id": str(ans.public_id),
                "student": _student_brief(ans.user),
                "course_public_id": str(course.public_id),
                "course_title": course.title,
                "module_public_id": str(module.public_id),
                "question_public_id": str(ans.question.public_id),
                "question_title": ans.question.title,
                "selected_answers": selected,
                "is_correct": ans.is_correct,
                "points_earned": ans.points_earned,
                "created_at": ans.created_at.isoformat(),
            }
        )

    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows[:limit]


def build_challenge_detail_for_mentor(challenge) -> dict:
    course = challenge.course
    module = challenge.module
    test_cases = challenge.test_cases.order_by("order_index")
    return {
        "public_id": str(challenge.public_id),
        "title": challenge.title,
        "description": challenge.description,
        "instructions": challenge.instructions,
        "course_public_id": str(course.public_id) if course else None,
        "course_title": course.title if course else None,
        "module_public_id": str(module.public_id) if module else None,
        "module_title": module.title if module else None,
        "difficulty": challenge.difficulty,
        "points": challenge.points,
        "test_cases": [
            {
                "public_id": str(tc.public_id),
                "order_index": tc.order_index,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden,
            }
            for tc in test_cases
        ],
    }
