"""Обратная совместимость — делегирует в container_lessons."""

from content.container_lessons import (
    CONTAINER_MODULE,
    max_order_in_container,
    next_order_in_container,
)
from content.container_lessons import (
    order_index_conflict as _order_index_conflict,
)
from content.container_lessons import (
    shift_orders_after_delete as _shift_orders_after_delete,
)


def max_order_in_module(module_id):
    return max_order_in_container(CONTAINER_MODULE, module_id)


def next_order_in_module(module_id):
    return next_order_in_container(CONTAINER_MODULE, module_id)


def shift_orders_after_delete(module_id, deleted_index):
    _shift_orders_after_delete(CONTAINER_MODULE, module_id, deleted_index)


def order_index_conflict(
    module_id, order_index, exclude_model=None, exclude_pk=None
):
    return _order_index_conflict(
        CONTAINER_MODULE,
        module_id,
        order_index,
        exclude_model=exclude_model,
        exclude_pk=exclude_pk,
    )
