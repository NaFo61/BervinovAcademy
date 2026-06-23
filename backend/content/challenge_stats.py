"""Статистика задач с кодом по курсу."""

from __future__ import annotations

from django.db.models import Count, Q, Sum

from content.models import CodingChallenge, Course


def _challenges_for_course(course: Course):
    module_ids = list(
        course.modules.filter(is_active=True).values_list("id", flat=True)
    )
    exam_ids = list(
        course.exams.filter(is_active=True).values_list("id", flat=True)
    )
    return CodingChallenge.objects.filter(is_active=True).filter(
        Q(module_id__in=module_ids)
        | Q(exam_id__in=exam_ids)
        | Q(
            course_id=course.id,
            module__isnull=True,
            exam__isnull=True,
        )
    )


def get_course_challenge_stats(course: Course) -> dict:
    qs = _challenges_for_course(course)
    agg = qs.aggregate(total=Count("id"), total_points=Sum("points"))
    by_difficulty = {
        row["difficulty"]: row["count"]
        for row in qs.values("difficulty").annotate(count=Count("id"))
    }
    by_module = (
        qs.filter(module__isnull=False)
        .values("module__public_id", "module__title", "module__order_index")
        .annotate(count=Count("id"))
        .order_by("module__order_index", "module__title")
    )
    return {
        "course_public_id": str(course.public_id),
        "course_slug": course.slug,
        "course_title": course.title,
        "total_challenges": agg["total"] or 0,
        "total_points": agg["total_points"] or 0,
        "by_difficulty": by_difficulty,
        "by_module": [
            {
                "module_public_id": str(row["module__public_id"]),
                "module_title": row["module__title"],
                "count": row["count"],
            }
            for row in by_module
        ],
    }
