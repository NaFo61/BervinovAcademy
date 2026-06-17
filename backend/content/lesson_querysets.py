"""Фильтры queryset для публичного API уроков (модуль, КР, курс)."""

from django.db.models import Q


def public_lesson_parent_q() -> Q:
    """Уроки из активного модуля, КР или уровня курса."""
    module_q = Q(
        module__isnull=False,
        module__is_active=True,
        module__course__is_active=True,
    )
    exam_q = Q(
        exam__isnull=False,
        exam__is_active=True,
        exam__course__is_active=True,
    )
    course_q = Q(
        module__isnull=True,
        exam__isnull=True,
        course__isnull=False,
        course__is_active=True,
    )
    return module_q | exam_q | course_q
