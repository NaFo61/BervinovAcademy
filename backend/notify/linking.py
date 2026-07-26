"""Привязка Telegram-аккаунта."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from notify.models import TelegramLinkToken
from notify.telegram_api import deep_link, is_configured

User = get_user_model()

LINK_TTL_MINUTES = 30


@transaction.atomic
def issue_link_token(*, user) -> dict:
    """Выдать одноразовый deep-link для привязки."""
    TelegramLinkToken.objects.filter(user=user, used_at__isnull=True).delete()
    token = TelegramLinkToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=LINK_TTL_MINUTES),
    )
    link = deep_link(token.token)
    return {
        "token": token.token,
        "expires_at": token.expires_at.isoformat(),
        "deep_link": link,
        "bot_configured": is_configured(),
        "bot_username": (
            __import__(
                "notify.telegram_api", fromlist=["bot_username"]
            ).bot_username()
        ),
    }


@transaction.atomic
def unlink_telegram(*, user) -> None:
    user.telegram_id = None
    user.telegram_username = ""
    user.telegram_linked_at = None
    user.save(
        update_fields=[
            "telegram_id",
            "telegram_username",
            "telegram_linked_at",
        ]
    )


@transaction.atomic
def consume_link_token(
    *,
    token: str,
    telegram_id: int,
    telegram_username: str = "",
) -> User | None:
    row = (
        TelegramLinkToken.objects.select_related("user")
        .filter(token=token)
        .first()
    )
    if not row or not row.is_valid:
        return None

    # Один telegram_id — один аккаунт
    User.objects.filter(telegram_id=telegram_id).exclude(
        pk=row.user_id
    ).update(
        telegram_id=None,
        telegram_username="",
        telegram_linked_at=None,
    )

    user = row.user
    user.telegram_id = telegram_id
    user.telegram_username = (telegram_username or "")[:64]
    user.telegram_linked_at = timezone.now()
    user.save(
        update_fields=[
            "telegram_id",
            "telegram_username",
            "telegram_linked_at",
        ]
    )
    row.used_at = timezone.now()
    row.save(update_fields=["used_at"])
    return user
