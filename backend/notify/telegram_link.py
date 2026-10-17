"""Привязка аккаунта к боту Telegram по одноразовому коду."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from notify.models import TelegramLinkToken

LINK_TTL = timedelta(minutes=30)


def issue_link_token(user) -> TelegramLinkToken:
    now = timezone.now()
    TelegramLinkToken.objects.filter(user=user, used_at__isnull=True).delete()
    return TelegramLinkToken.objects.create(
        user=user,
        expires_at=now + LINK_TTL,
    )


def unlink_telegram(user) -> None:
    user.telegram_id = None
    user.telegram_chat_id = None
    user.telegram_username = ""
    user.telegram_linked_at = None
    user.save(
        update_fields=[
            "telegram_id",
            "telegram_chat_id",
            "telegram_username",
            "telegram_linked_at",
        ]
    )


def apply_telegram_link(
    *,
    token_value: str,
    telegram_user_id: int,
    chat_id: int,
    username: str = "",
) -> bool:
    code = (token_value or "").strip()
    if not code or not telegram_user_id:
        return False
    now = timezone.now()
    User = get_user_model()
    with transaction.atomic():
        link = (
            TelegramLinkToken.objects.select_for_update()
            .filter(token=code, used_at__isnull=True, expires_at__gt=now)
            .select_related("user")
            .first()
        )
        if link is None:
            return False
        taken = (
            User.objects.filter(telegram_id=telegram_user_id)
            .exclude(pk=link.user_id)
            .exists()
        )
        if taken:
            return False
        user = link.user
        user.telegram_id = telegram_user_id
        user.telegram_chat_id = chat_id
        user.telegram_username = (username or "").lstrip("@")[:64]
        user.telegram_linked_at = now
        user.save(
            update_fields=[
                "telegram_id",
                "telegram_chat_id",
                "telegram_username",
                "telegram_linked_at",
            ]
        )
        link.used_at = now
        link.save(update_fields=["used_at"])
    return True


def handle_update(update: dict) -> None:
    """Связать аккаунт, если в личке пришёл /start <код>."""
    message = update.get("message") or update.get("edited_message") or {}
    text = (message.get("text") or "").strip()
    if not text.startswith("/start"):
        return
    parts = text.split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    sender = message.get("from") or {}
    chat = message.get("chat") or {}
    try:
        telegram_user_id = int(sender.get("id"))
        chat_id = int(chat.get("id"))
    except (TypeError, ValueError):
        return
    from notify.telegram_api import send_message

    if not payload:
        send_message(
            chat_id,
            "Чтобы привязать кабинет, откройте профиль на сайте "
            "и нажмите «Привязать Telegram».",
        )
        return
    linked = apply_telegram_link(
        token_value=payload,
        telegram_user_id=telegram_user_id,
        chat_id=chat_id,
        username=(sender.get("username") or ""),
    )

    if linked:
        send_message(chat_id, "Готово. Telegram привязан к кабинету.")
        return
    if payload:
        send_message(
            chat_id,
            "Ссылка устарела или этот Telegram уже занят. "
            "Откройте профиль на сайте и получите новую.",
        )
