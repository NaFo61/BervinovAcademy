"""Клиент Telegram Bot API (без aiogram — HTTP достаточно для MVP)."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
import requests

logger = logging.getLogger(__name__)


def bot_token() -> str:
    return (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()


def bot_username() -> str:
    return (
        (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "")
        .strip()
        .lstrip("@")
    )


def is_configured() -> bool:
    return bool(bot_token())


def send_message(
    chat_id: int | str,
    text: str,
    *,
    reply_markup: dict | None = None,
) -> bool:
    token = bot_token()
    if not token or not chat_id:
        return False
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.warning(
                "Telegram sendMessage %s: %s",
                resp.status_code,
                resp.text[:300],
            )
            return False
        return True
    except requests.RequestException:
        logger.exception("Telegram sendMessage failed chat_id=%s", chat_id)
        return False


def deep_link(token: str) -> str:
    name = bot_username()
    if not name:
        return ""
    return f"https://t.me/{name}?start={token}"
