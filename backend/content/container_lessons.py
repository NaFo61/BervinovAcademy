"""Общий порядок уроков в контейнере: модуль, КР или курс."""

from __future__ import annotations

from django.db.models import F, Max

CONTAINER_MODULE = "module"
CONTAINER_EXAM = "exam"
CONTAINER_COURSE = "course"


def _lesson_models():
    from content.models import (
        CodingChallenge,
        LessonCheckBoxQuestion,
        LessonRadioQuestion,
        LessonTheory,
    )

    return (
        LessonTheory,
        LessonRadioQuestion,
        LessonCheckBoxQuestion,
        CodingChallenge,
    )


def _filter_kwargs(container_kind: str, container_id: int) -> dict:
    if container_kind == CONTAINER_MODULE:
        return {"module_id": container_id}
    if container_kind == CONTAINER_EXAM:
        return {"exam_id": container_id}
    if container_kind == CONTAINER_COURSE:
        return {
            "course_id": container_id,
            "module__isnull": True,
            "exam__isnull": True,
        }
    raise ValueError(f"Unknown container kind: {container_kind}")


def container_from_instance(instance) -> tuple[str, int] | tuple[None, None]:
    if instance.module_id:
        return CONTAINER_MODULE, instance.module_id
    if getattr(instance, "exam_id", None):
        return CONTAINER_EXAM, instance.exam_id
    if getattr(instance, "course_id", None) and not instance.module_id:
        if hasattr(instance, "exam_id") and instance.exam_id:
            return None, None
        return CONTAINER_COURSE, instance.course_id
    return None, None


def max_order_in_container(container_kind: str, container_id: int) -> int:
    maximum = 0
    filters = _filter_kwargs(container_kind, container_id)
    for model in _lesson_models():
        val = model.objects.filter(**filters).aggregate(m=Max("order_index"))[
            "m"
        ]
        if val and val > maximum:
            maximum = val
    return maximum


def next_order_in_container(container_kind: str, container_id: int) -> int:
    return max_order_in_container(container_kind, container_id) + 1


def shift_orders_after_delete(
    container_kind: str, container_id: int, deleted_index: int
):
    filters = _filter_kwargs(container_kind, container_id)
    for model in _lesson_models():
        model.objects.filter(**filters, order_index__gt=deleted_index).update(
            order_index=F("order_index") - 1
        )


def order_index_conflict(
    container_kind: str,
    container_id: int,
    order_index: int,
    exclude_model=None,
    exclude_pk=None,
) -> bool:
    filters = _filter_kwargs(container_kind, container_id)
    filters["order_index"] = order_index
    for model in _lesson_models():
        qs = model.objects.filter(**filters)
        if exclude_model is model and exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if qs.exists():
            return True
    return False


def iter_container_lessons(container, active_only: bool = False):
    """Уроки контейнера в порядке order_index: (type, instance)."""
    from content.models import Exam, Module

    if isinstance(container, Module):
        kind = CONTAINER_MODULE
    elif isinstance(container, Exam):
        kind = CONTAINER_EXAM
    else:
        kind = CONTAINER_COURSE

    items = []
    if kind == CONTAINER_MODULE:
        theories = container.lessons_theories.all()
        radios = container.lessons_radio_questions.all()
        checkboxes = container.lessons_checkbox_questions.all()
        challenges = container.challenges.all()
    elif kind == CONTAINER_EXAM:
        theories = container.lessons_theories.all()
        radios = container.lessons_radio_questions.all()
        checkboxes = container.lessons_checkbox_questions.all()
        challenges = container.challenges.all()
    else:
        from content.models import CodingChallenge

        theories = container.course_lessons_theories.all()
        radios = container.course_lessons_radio_questions.all()
        checkboxes = container.course_lessons_checkbox_questions.all()
        challenges = CodingChallenge.objects.filter(
            course_id=container.id,
            module__isnull=True,
            exam__isnull=True,
        )

    if active_only:
        theories = theories.filter(is_active=True)
        radios = radios.filter(is_active=True)
        checkboxes = checkboxes.filter(is_active=True)
        challenges = challenges.filter(is_active=True)

    for obj in theories:
        items.append(("theory", obj))
    for obj in radios:
        items.append(("radio", obj))
    for obj in checkboxes:
        items.append(("checkbox", obj))
    for obj in challenges:
        items.append(("coding", obj))
    items.sort(key=lambda pair: (pair[1].order_index, pair[0]))
    return items


def iter_module_lessons(module, active_only: bool = False):
    """Обратная совместимость."""
    return iter_container_lessons(module, active_only=active_only)
