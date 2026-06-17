"""Подсчёт прогресса пользователя для профиля и достижений."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from content.models import (
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
)

from .models import (
    CodeSubmission,
    UserAnswerCheckBox,
    UserAnswerRadio,
    UserLessonTheoryRead,
)


def _distinct_coding_solved(user) -> int:
    return (
        CodeSubmission.objects.filter(
            user=user,
            status=CodeSubmission.STATUS_COMPLETED,
        )
        .values("challenge_id")
        .distinct()
        .count()
    )


def _distinct_radio_solved(user) -> int:
    return (
        UserAnswerRadio.objects.filter(user=user, is_correct=True)
        .values("question_id")
        .distinct()
        .count()
    )


def _distinct_checkbox_solved(user) -> int:
    return (
        UserAnswerCheckBox.objects.filter(user=user, is_correct=True)
        .values("question_id")
        .distinct()
        .count()
    )


def _theories_read(user) -> int:
    return UserLessonTheoryRead.objects.filter(user=user).count()


def _activity_dates(user) -> set:
    dates: set = set()
    for row in UserAnswerRadio.objects.filter(
        user=user, is_correct=True
    ).dates("created_at", "day"):
        dates.add(row)
    for row in UserAnswerCheckBox.objects.filter(
        user=user, is_correct=True
    ).dates("created_at", "day"):
        dates.add(row)
    for row in CodeSubmission.objects.filter(
        user=user,
        status=CodeSubmission.STATUS_COMPLETED,
        completed_at__isnull=False,
    ).dates("completed_at", "day"):
        dates.add(row)
    for row in UserLessonTheoryRead.objects.filter(user=user).dates(
        "read_at", "day"
    ):
        dates.add(row)
    return dates


def compute_streak_days(user) -> int:
    dates = _activity_dates(user)
    if not dates:
        return 0

    today = timezone.localdate()
    if today in dates:
        cursor = today
    elif (today - timedelta(days=1)) in dates:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _course_lesson_counts(course: Course) -> dict[str, int]:
    module_ids = list(
        course.modules.filter(is_active=True).values_list("id", flat=True)
    )
    exam_ids = list(
        course.exams.filter(is_active=True).values_list("id", flat=True)
    )

    theory = (
        LessonTheory.objects.filter(is_active=True)
        .filter(
            Q(module_id__in=module_ids)
            | Q(exam_id__in=exam_ids)
            | Q(course_id=course.id, module__isnull=True, exam__isnull=True)
        )
        .count()
    )
    radio = (
        LessonRadioQuestion.objects.filter(is_active=True)
        .filter(
            Q(module_id__in=module_ids)
            | Q(exam_id__in=exam_ids)
            | Q(course_id=course.id, module__isnull=True, exam__isnull=True)
        )
        .count()
    )
    checkbox = (
        LessonCheckBoxQuestion.objects.filter(is_active=True)
        .filter(
            Q(module_id__in=module_ids)
            | Q(exam_id__in=exam_ids)
            | Q(course_id=course.id, module__isnull=True, exam__isnull=True)
        )
        .count()
    )
    coding = (
        CodingChallenge.objects.filter(is_active=True)
        .filter(
            Q(module_id__in=module_ids)
            | Q(exam_id__in=exam_ids)
            | Q(course_id=course.id, module__isnull=True, exam__isnull=True)
        )
        .count()
    )
    return {
        "theory": theory,
        "radio": radio,
        "checkbox": checkbox,
        "coding": coding,
        "total": theory + radio + checkbox + coding,
    }


def _course_done_counts(user, course: Course) -> int:
    module_ids = list(
        course.modules.filter(is_active=True).values_list("id", flat=True)
    )
    exam_ids = list(
        course.exams.filter(is_active=True).values_list("id", flat=True)
    )
    if not module_ids and not exam_ids:
        pass

    theory_filter = Q(lesson__is_active=True) & (
        Q(lesson__module_id__in=module_ids)
        | Q(lesson__exam_id__in=exam_ids)
        | Q(
            lesson__course_id=course.id,
            lesson__module__isnull=True,
            lesson__exam__isnull=True,
        )
    )
    theory_done = (
        UserLessonTheoryRead.objects.filter(user=user)
        .filter(theory_filter)
        .count()
    )

    radio_filter = Q(is_correct=True, question__is_active=True) & (
        Q(question__module_id__in=module_ids)
        | Q(question__exam_id__in=exam_ids)
        | Q(
            question__course_id=course.id,
            question__module__isnull=True,
            question__exam__isnull=True,
        )
    )
    radio_done = (
        UserAnswerRadio.objects.filter(user=user)
        .filter(radio_filter)
        .values("question_id")
        .distinct()
        .count()
    )
    checkbox_filter = Q(is_correct=True, question__is_active=True) & (
        Q(question__module_id__in=module_ids)
        | Q(question__exam_id__in=exam_ids)
        | Q(
            question__course_id=course.id,
            question__module__isnull=True,
            question__exam__isnull=True,
        )
    )
    checkbox_done = (
        UserAnswerCheckBox.objects.filter(user=user)
        .filter(checkbox_filter)
        .values("question_id")
        .distinct()
        .count()
    )
    coding_filter = Q(
        status=CodeSubmission.STATUS_COMPLETED, challenge__is_active=True
    ) & (
        Q(challenge__module_id__in=module_ids)
        | Q(challenge__exam_id__in=exam_ids)
        | Q(
            challenge__course_id=course.id,
            challenge__module__isnull=True,
            challenge__exam__isnull=True,
        )
    )
    coding_done = (
        CodeSubmission.objects.filter(user=user)
        .filter(coding_filter)
        .values("challenge_id")
        .distinct()
        .count()
    )
    return theory_done + radio_done + checkbox_done + coding_done


def count_courses_completed(user) -> int:
    completed = 0
    for course in Course.objects.filter(is_active=True).only("id"):
        counts = _course_lesson_counts(course)
        if counts["total"] == 0:
            continue
        if _course_done_counts(user, course) >= counts["total"]:
            completed += 1
    return completed


def get_user_progress_stats(user) -> dict[str, int]:
    coding = _distinct_coding_solved(user)
    radio = _distinct_radio_solved(user)
    checkbox = _distinct_checkbox_solved(user)
    theories = _theories_read(user)
    quizzes = radio + checkbox

    return {
        "tasks_solved": coding + radio + checkbox,
        "coding_solved": coding,
        "quizzes_solved": quizzes,
        "radio_solved": radio,
        "checkbox_solved": checkbox,
        "theories_read": theories,
        "courses_completed": count_courses_completed(user),
        "streak_days": compute_streak_days(user),
    }


def _lesson_key(step_type: str, public_id) -> str:
    return f"{step_type}-{public_id}"


def build_completed_lesson_keys(user, course: Course) -> set[str]:
    """Ключи пройденных шагов курса (формат фронта: theory-uuid, radio-uuid, …)."""
    module_ids = list(
        course.modules.filter(is_active=True).values_list("id", flat=True)
    )
    exam_ids = list(
        course.exams.filter(is_active=True).values_list("id", flat=True)
    )
    if not module_ids and not exam_ids and not course.id:
        return set()

    keys: set[str] = set()
    theory_q = Q(lesson__is_active=True) & (
        Q(lesson__module_id__in=module_ids)
        | Q(lesson__exam_id__in=exam_ids)
        | Q(
            lesson__course_id=course.id,
            lesson__module__isnull=True,
            lesson__exam__isnull=True,
        )
    )
    for row in (
        UserLessonTheoryRead.objects.filter(user=user)
        .filter(theory_q)
        .values_list("lesson__public_id", flat=True)
    ):
        keys.add(_lesson_key("theory", row))

    radio_q = Q(is_correct=True, question__is_active=True) & (
        Q(question__module_id__in=module_ids)
        | Q(question__exam_id__in=exam_ids)
        | Q(
            question__course_id=course.id,
            question__module__isnull=True,
            question__exam__isnull=True,
        )
    )
    for row in (
        UserAnswerRadio.objects.filter(user=user)
        .filter(radio_q)
        .values_list("question__public_id", flat=True)
        .distinct()
    ):
        keys.add(_lesson_key("radio", row))

    checkbox_q = Q(is_correct=True, question__is_active=True) & (
        Q(question__module_id__in=module_ids)
        | Q(question__exam_id__in=exam_ids)
        | Q(
            question__course_id=course.id,
            question__module__isnull=True,
            question__exam__isnull=True,
        )
    )
    for row in (
        UserAnswerCheckBox.objects.filter(user=user)
        .filter(checkbox_q)
        .values_list("question__public_id", flat=True)
        .distinct()
    ):
        keys.add(_lesson_key("checkbox", row))

    coding_q = Q(
        status=CodeSubmission.STATUS_COMPLETED, challenge__is_active=True
    ) & (
        Q(challenge__module_id__in=module_ids)
        | Q(challenge__exam_id__in=exam_ids)
        | Q(
            challenge__course_id=course.id,
            challenge__module__isnull=True,
            challenge__exam__isnull=True,
        )
    )
    for row in (
        CodeSubmission.objects.filter(user=user)
        .filter(coding_q)
        .values_list("challenge__public_id", flat=True)
        .distinct()
    ):
        keys.add(_lesson_key("coding", row))

    return keys


def get_course_progress_detail(user, course: Course) -> dict:
    counts = _course_lesson_counts(course)
    total = counts["total"]
    done = _course_done_counts(user, course) if total else 0
    percent = round(100 * done / total) if total else 0
    completed_keys = sorted(build_completed_lesson_keys(user, course))

    from exams.services import get_course_exam_summary

    return {
        "course_public_id": str(course.public_id),
        "course_title": course.title,
        "total_steps": total,
        "completed_steps": done,
        "percent": percent,
        "completed": completed_keys,
        "breakdown": {
            "theory": counts["theory"],
            "radio": counts["radio"],
            "checkbox": counts["checkbox"],
            "coding": counts["coding"],
        },
        "exams": get_course_exam_summary(user, course),
    }


def get_daily_activity_counts(user, days: int = 30) -> list[dict]:
    """Активность по дням за последние ``days`` дней (для графика профиля)."""
    from collections import defaultdict

    counts: dict = defaultdict(int)

    for dt in UserAnswerRadio.objects.filter(
        user=user, is_correct=True
    ).values_list("created_at", flat=True):
        counts[timezone.localtime(dt).date()] += 1

    for dt in UserAnswerCheckBox.objects.filter(
        user=user, is_correct=True
    ).values_list("created_at", flat=True):
        counts[timezone.localtime(dt).date()] += 1

    for dt in CodeSubmission.objects.filter(
        user=user,
        status=CodeSubmission.STATUS_COMPLETED,
        completed_at__isnull=False,
    ).values_list("completed_at", flat=True):
        counts[timezone.localtime(dt).date()] += 1

    for dt in UserLessonTheoryRead.objects.filter(user=user).values_list(
        "read_at", flat=True
    ):
        counts[timezone.localtime(dt).date()] += 1

    today = timezone.localdate()
    result = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        result.append(
            {
                "date": day.isoformat(),
                "label": f"{day.day}.{day.month}",
                "count": counts.get(day, 0),
            }
        )
    return result


def build_activity_payload(user) -> dict:
    days = get_daily_activity_counts(user)
    total_month = sum(row["count"] for row in days)
    return {
        "last_30_days": days,
        "total_month": total_month,
    }
