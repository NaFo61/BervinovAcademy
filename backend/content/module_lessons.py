"""Общий порядок уроков внутри модуля (теория, radio, checkbox, код)."""

from django.db.models import F, Max


def _module_lesson_models():
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


def max_order_in_module(module_id):
    """Максимальный order_index среди всех типов уроков в модуле."""
    maximum = 0
    for model in _module_lesson_models():
        val = model.objects.filter(module_id=module_id).aggregate(
            m=Max("order_index")
        )["m"]
        if val and val > maximum:
            maximum = val
    return maximum


def next_order_in_module(module_id):
    return max_order_in_module(module_id) + 1


def shift_orders_after_delete(module_id, deleted_index):
    """Сдвинуть order_index у всех уроков модуля после удаления позиции."""
    for model in _module_lesson_models():
        model.objects.filter(
            module_id=module_id, order_index__gt=deleted_index
        ).update(order_index=F("order_index") - 1)


def order_index_conflict(
    module_id, order_index, exclude_model=None, exclude_pk=None
):
    """Проверить, занят ли order_index другим уроком в модуле."""
    for model in _module_lesson_models():
        qs = model.objects.filter(module_id=module_id, order_index=order_index)
        if exclude_model is model and exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if qs.exists():
            return True
    return False


def iter_module_lessons(module, active_only=False):
    """Уроки модуля в порядке order_index: (type, instance)."""
    items = []
    theories = module.lessons_theories.all()
    radios = module.lessons_radio_questions.all()
    checkboxes = module.lessons_checkbox_questions.all()
    challenges = module.challenges.all()
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
