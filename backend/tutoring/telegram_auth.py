"""Вход в занятия из Telegram Mini App по подписи initData."""

from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received = parsed.pop("hash", None)
    if not received or not bot_token:
        return None
    check = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    secret = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    digest = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, received):
        return None
    return parsed


class TelegramInitDataAuthentication(BaseAuthentication):
    """Authorization: tma <initData>. Пользователь уже привязан к профилю."""

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("tma "):
            return None
        token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
        parsed = validate_init_data(header[4:].strip(), token)
        if not parsed:
            raise AuthenticationFailed("Подпись Telegram не сошлась.")
        try:
            tg_user = json.loads(parsed.get("user") or "{}")
            telegram_id = int(tg_user["id"])
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise AuthenticationFailed("В initData нет пользователя.") from exc
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user is None or not user.is_active:
            raise AuthenticationFailed(
                "Этот Telegram ещё не привязан к кабинету."
            )
        return (user, None)
