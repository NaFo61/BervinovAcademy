"""Web Push через pywebpush."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def vapid_public_key() -> str:
    return (getattr(settings, "VAPID_PUBLIC_KEY", "") or "").strip()


def _private_key_material() -> str:
    raw = (getattr(settings, "VAPID_PRIVATE_KEY", "") or "").strip()
    if not raw:
        return ""
    # path to PEM on disk
    if raw.startswith("/") or raw.endswith(".pem"):
        try:
            with open(raw, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            logger.exception(
                "Не удалось прочитать VAPID_PRIVATE_KEY path=%s", raw
            )
            return ""
    return raw.replace("\\n", "\n")


def is_configured() -> bool:
    return bool(vapid_public_key() and _private_key_material())


def send_web_push(
    *,
    subscription,
    title: str,
    body: str,
    url: str = "",
) -> bool:
    private_key = _private_key_material()
    if not vapid_public_key() or not private_key:
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
            vapid_private_key=private_key,
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
