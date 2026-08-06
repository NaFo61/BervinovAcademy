"""Доставка уведомлений: in-app + VK + Web Push."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def site_url(path: str = "") -> str:
    base = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    if not path:
        return base or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}" if base else path


def create_and_deliver(
    *,
    user,
    kind: str,
    title: str,
    body: str = "",
    conference=None,
    url: str = "",
    persist: bool = True,
    skip_vk: bool = False,
) -> Any:
    """Создать in-app уведомление (опционально) и поставить доставку в очередь."""
    note = None
    if persist:
        from communication.models import UserNotification

        note = UserNotification.objects.create(
            user=user,
            kind=kind,
            title=title,
            body=body or "",
            conference=conference,
        )

    try:
        from notify.tasks import deliver_outbound

        deliver_outbound.delay(
            user_id=user.pk,
            title=title,
            body=body or "",
            url=url or "",
            kind=kind,
            skip_vk=skip_vk,
        )
    except Exception:
        logger.exception(
            "Не удалось поставить deliver_outbound в очередь (user=%s)",
            getattr(user, "pk", None),
        )
    return note
