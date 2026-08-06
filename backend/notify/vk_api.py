"""Тонкий клиент VK API (messages.send + скачивание вложений)."""

from __future__ import annotations

import logging
import random
from typing import Any

from django.conf import settings
import requests

logger = logging.getLogger(__name__)

VK_API_VERSION = "5.199"


def is_configured() -> bool:
    return bool(
        (getattr(settings, "VK_GROUP_TOKEN", "") or "").strip()
        and (getattr(settings, "VK_GROUP_ID", "") or "").strip()
    )


def group_id() -> str:
    return (getattr(settings, "VK_GROUP_ID", "") or "").strip()


def community_write_url() -> str:
    gid = group_id()
    if not gid:
        return ""
    # vk.me/club{id} — открыть диалог с сообществом
    return f"https://vk.me/club{gid}"


def _token() -> str:
    return (getattr(settings, "VK_GROUP_TOKEN", "") or "").strip()


def _api(method: str, params: dict[str, Any]) -> dict[str, Any] | None:
    token = _token()
    if not token:
        return None
    data = {
        **params,
        "access_token": token,
        "v": VK_API_VERSION,
    }
    try:
        resp = requests.post(
            f"https://api.vk.com/method/{method}",
            data=data,
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("VK API %s failed", method)
        return None
    if "error" in payload:
        logger.warning("VK API %s error: %s", method, payload["error"])
        return None
    return payload.get("response")


def send_message(
    peer_id: int,
    text: str,
    *,
    keyboard: dict | None = None,
) -> bool:
    if not is_configured() or not peer_id:
        return False
    params: dict[str, Any] = {
        "peer_id": int(peer_id),
        "message": (text or "")[:4096],
        "random_id": random.randint(1, 2**31 - 1),
    }
    if keyboard:
        import json

        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    return _api("messages.send", params) is not None


def download_photo_url(url: str) -> tuple[bytes, str] | None:
    """Скачать фото по URL; вернуть (content, content_type)."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        ctype = (
            (resp.headers.get("Content-Type") or "image/jpeg")
            .split(";")[0]
            .strip()
        )
        return resp.content, ctype
    except Exception:
        logger.exception("VK photo download failed")
        return None
