"""Валидация и хелперы родительского контейнера урока (модуль / КР / курс)."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from content.container_lessons import (
    container_from_instance,
    next_order_in_container,
    order_index_conflict,
    shift_orders_after_delete,
)


def validate_lesson_parent(instance):
    module_id = getattr(instance, "module_id", None)
    exam_id = getattr(instance, "exam_id", None)
    course_id = getattr(instance, "course_id", None)

    if module_id or exam_id:
        return
    if course_id:
        return
    raise ValidationError(
        _(
            "Урок должен принадлежать ровно одному контейнеру: модуль, КР или курс."
        )
    )


def validate_lesson_order_index(instance):
    from content.container_lessons import container_from_instance

    kind, container_id = container_from_instance(instance)
    if not kind:
        return
    if order_index_conflict(
        kind,
        container_id,
        instance.order_index,
        exclude_model=instance.__class__,
        exclude_pk=instance.pk,
    ):
        raise ValidationError(
            {
                "order_index": _(
                    "Позиция %(pos)d уже занята другим уроком в этом контейнере"
                )
                % {"pos": instance.order_index}
            }
        )


def save_lesson_order(instance):
    kind, container_id = container_from_instance(instance)
    if not kind or not instance._state.adding:
        return
    if order_index_conflict(kind, container_id, instance.order_index):
        instance.order_index = next_order_in_container(kind, container_id)


def delete_lesson_with_order_shift(instance):
    from django.db import models

    kind, container_id = container_from_instance(instance)
    deleted_index = instance.order_index
    models.Model.delete(instance)
    if kind and container_id:
        shift_orders_after_delete(kind, container_id, deleted_index)


def sync_coding_challenge_course(instance):
    """Денormalize course_id на CodingChallenge из родителя."""
    if instance.module_id:
        instance.course_id = instance.module.course_id
    elif instance.exam_id:
        instance.course_id = instance.exam.course_id
    elif instance.course_id:
        pass
