"""Обработка входящих update от Telegram."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model
from notify.dispatch import site_url
from notify.linking import consume_link_token
from notify.telegram_api import send_message

logger = logging.getLogger(__name__)
User = get_user_model()


def _chat_id(update: dict) -> int | None:
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    cid = chat.get("id")
    return int(cid) if cid is not None else None


def _from_user(update: dict) -> dict:
    msg = update.get("message") or {}
    return msg.get("from") or {}


def handle_update(update: dict[str, Any]) -> None:
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    chat_id = _chat_id(update)
    if not chat_id or not text:
        return

    from_user = _from_user(update)
    tg_id = from_user.get("id")
    username = from_user.get("username") or ""

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        if payload:
            user = consume_link_token(
                token=payload,
                telegram_id=int(tg_id),
                telegram_username=username,
            )
            if user:
                send_message(
                    chat_id,
                    (
                        f"Готово, {user.first_name}! Аккаунт Bervinov Academy "
                        "привязан.\n\n"
                        "Команды:\n"
                        "/unread — непрочитанные сообщения\n"
                        "/calls — ожидают созвоны\n"
                        "/progress — прогресс и streak\n"
                        "/help — справка"
                    ),
                )
            else:
                send_message(
                    chat_id,
                    "Ссылка устарела или уже использована. "
                    "Открой настройки профиля и получи новую.",
                )
            return
        user = User.objects.filter(telegram_id=tg_id).first()
        if user:
            send_message(
                chat_id,
                f"Снова привет, {user.first_name}! /help — список команд.",
            )
        else:
            send_message(
                chat_id,
                "Привет! Чтобы привязать аккаунт, зайди на сайт → "
                "Профиль → Настройки → «Подключить Telegram».",
            )
        return

    user = User.objects.filter(telegram_id=tg_id).first()
    if not user:
        send_message(
            chat_id,
            "Сначала привяжи аккаунт через настройки профиля на сайте.",
        )
        return

    cmd = text.split()[0].split("@")[0].lower()
    if cmd in ("/help", "/commands"):
        send_message(
            chat_id,
            "Команды:\n"
            "/unread — непрочитанные от ментора\n"
            "/calls — ожидающие созвоны\n"
            "/progress — курсы и streak\n\n"
            f"Сайт: {site_url('/')}",
        )
        return
    if cmd == "/unread":
        _cmd_unread(chat_id, user)
        return
    if cmd == "/calls":
        _cmd_calls(chat_id, user)
        return
    if cmd == "/progress":
        _cmd_progress(chat_id, user)
        return

    send_message(chat_id, "Не понял. Напиши /help.")


def _cmd_unread(chat_id: int, user) -> None:
    from communication.chat_services import (
        thread_unread_count,
        threads_for_user,
    )

    threads = threads_for_user(user)
    lines = []
    total = 0
    for th in threads[:10]:
        n = thread_unread_count(thread=th, user=user)
        if n <= 0:
            continue
        total += n
        other = th.mentor if th.student_id == user.pk else th.student
        name = f"{other.first_name} {other.last_name}".strip() or "Диалог"
        lines.append(f"• {name}: {n}")
    if not lines:
        send_message(chat_id, "Непрочитанных нет. Красавчик.")
        return
    send_message(
        chat_id,
        f"Непрочитанных: {total}\n"
        + "\n".join(lines)
        + f"\n\nОткрыть: {site_url('/messages')}",
    )


def _cmd_calls(chat_id: int, user) -> None:
    from communication.models import Conference

    qs = Conference.objects.filter(
        guest=user,
        status=Conference.Status.WAITING,
    ).select_related("mentor")[:5]
    if not qs:
        send_message(chat_id, "Нет ожидающих созвонов.")
        return
    lines = []
    for c in qs:
        mentor = f"{c.mentor.first_name} {c.mentor.last_name}".strip()
        lines.append(f"• {mentor}\n  {site_url(f'/call?conf={c.public_id}')}")
    send_message(chat_id, "Ожидают созвоны:\n" + "\n".join(lines))


def _cmd_progress(chat_id: int, user) -> None:
    from education.models import Enrollment
    from progress.stats import compute_streak_days

    streak = compute_streak_days(user)
    ens = (
        Enrollment.objects.filter(user=user, status=Enrollment.Status.ACTIVE)
        .select_related("course")
        .order_by("-last_activity_at")[:5]
    )
    lines = [f"🔥 Streak: {streak} дн."]
    if not ens:
        lines.append("Активных курсов нет.")
    else:
        lines.append("Курсы:")
        for e in ens:
            title = getattr(e.course, "title", "Курс")
            lines.append(f"• {title}")
    lines.append(f"\nУчиться: {site_url('/catalog')}")
    send_message(chat_id, "\n".join(lines))
