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


def api_base() -> str:
    base = (getattr(settings, "TELEGRAM_API_BASE", "") or "").strip()
    return (base or "https://api.telegram.org").rstrip("/")


def proxy_dict() -> dict[str, str] | None:
    """Опциональный прокси: TELEGRAM_PROXY=socks5://user:pass@host:port."""
    raw = (getattr(settings, "TELEGRAM_PROXY", "") or "").strip()
    if not raw:
        return None
    return {"http": raw, "https": raw}


def is_configured() -> bool:
    return bool(bot_token())


def _request(method: str, api_method: str, **kwargs) -> requests.Response:
    url = f"{api_base()}/bot{bot_token()}/{api_method}"
    timeout = kwargs.pop("timeout", 20)
    proxies = proxy_dict()
    if proxies:
        kwargs.setdefault("proxies", proxies)
    return requests.request(method, url, timeout=timeout, **kwargs)


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
        resp = _request("POST", "sendMessage", json=payload, timeout=20)
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
