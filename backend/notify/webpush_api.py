"""Web Push через pywebpush."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def vapid_public_key() -> str:
    return (getattr(settings, "VAPID_PUBLIC_KEY", "") or "").strip()


def is_configured() -> bool:
    return bool(
        vapid_public_key()
        and (getattr(settings, "VAPID_PRIVATE_KEY", "") or "").strip()
    )


def send_web_push(
    *,
    subscription,
    title: str,
    body: str,
    url: str = "",
) -> bool:
    if not is_configured():
        return False
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush не установлен")
        return False

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "url": url or "/",
        },
        ensure_ascii=False,
    )
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": getattr(
                    settings, "VAPID_ADMIN_EMAIL", "mailto:admin@example.com"
                )
            },
        )
        subscription.last_success_at = timezone.now()
        subscription.save(update_fields=["last_success_at"])
        return True
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.warning(
            "WebPush failed user=%s status=%s: %s",
            subscription.user_id,
            status,
            exc,
        )
        if status in (404, 410):
            subscription.delete()
        return False
    except Exception:
        logger.exception("WebPush error user=%s", subscription.user_id)
        return False
