"""Access rules for lesson content (anti-scraping)."""

from __future__ import annotations

from django.db.models import Q, QuerySet


def user_is_staff_editor(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_admin", False) or getattr(
        user, "is_superuser", False
    ):
        return True
    return getattr(user, "role", None) in ("admin", "mentor")


def lesson_access_q(user) -> Q:
    """
    Students: only lessons of courses they are enrolled in
    (or exam with an attempt). Mentors/admins: unrestricted.
    """
    if user_is_staff_editor(user):
        return Q()

    from exams.models import ExamAttempt

    from education.models import Enrollment

    enrolled_ids = list(
        Enrollment.objects.filter(
            user=user,
            status__in=(
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ),
        ).values_list("course_id", flat=True)
    )
    attempt_exam_ids = list(
        ExamAttempt.objects.filter(user=user).values_list("exam_id", flat=True)
    )

    module_ok = Q(module__course_id__in=enrolled_ids)
    course_ok = Q(
        module__isnull=True,
        exam__isnull=True,
        course_id__in=enrolled_ids,
    )
    exam_ok = Q(exam__course_id__in=enrolled_ids) | Q(
        exam_id__in=attempt_exam_ids
    )
    return module_ok | course_ok | exam_ok


def filter_lessons_for_user(queryset: QuerySet, user) -> QuerySet:
    if user_is_staff_editor(user):
        return queryset
    return queryset.filter(lesson_access_q(user))
