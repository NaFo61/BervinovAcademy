"""Обработка Callback API VK: чат-мост + команды."""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import InMemoryUploadedFile
from notify.dispatch import site_url
from notify.vk_api import (
    community_write_url,
    download_photo_url,
    send_message,
)

logger = logging.getLogger(__name__)
User = get_user_model()

PENDING_THREAD_TTL = 600
PENDING_THREAD_PREFIX = "vk_pending_thread:"


def handle_callback_event(event: dict[str, Any]) -> str | None:
    """
    Обработать событие Callback API.
    Для type=confirmation вернуть строку подтверждения (caller отвечает ею).
    Иначе None (caller отвечает ok).
    """
    etype = event.get("type") or ""
    if etype == "confirmation":
        from django.conf import settings

        return (
            getattr(settings, "VK_CALLBACK_CONFIRMATION", "") or ""
        ).strip()

    if etype == "message_allow":
        _on_message_allow(event.get("object") or {})
        return None
    if etype == "message_deny":
        _on_message_deny(event.get("object") or {})
        return None
    if etype == "message_new":
        _on_message_new(event.get("object") or {})
        return None
    return None


def _user_by_vk(vk_id: int | None):
    if not vk_id:
        return None
    return User.objects.filter(vk_id=int(vk_id)).first()


def _on_message_allow(obj: dict) -> None:
    user_id = obj.get("user_id")
    user = _user_by_vk(user_id)
    if user and not user.vk_messages_allowed:
        user.vk_messages_allowed = True
        user.save(update_fields=["vk_messages_allowed"])


def _on_message_deny(obj: dict) -> None:
    user_id = obj.get("user_id")
    user = _user_by_vk(user_id)
    if user and user.vk_messages_allowed:
        user.vk_messages_allowed = False
        user.save(update_fields=["vk_messages_allowed"])


def _extract_message(obj: dict) -> dict:
    # API 5.80+: object.message; older: object itself
    if isinstance(obj.get("message"), dict):
        return obj["message"]
    return obj


def _on_message_new(obj: dict) -> None:
    msg = _extract_message(obj)
    peer_id = msg.get("peer_id") or msg.get("from_id")
    from_id = msg.get("from_id")
    if not from_id or int(from_id) < 0:
        # исходящие от сообщества / групп — игнор
        return
    text = (msg.get("text") or "").strip()
    peer = int(peer_id or from_id)

    user = _user_by_vk(from_id)
    if not user:
        community_write_url() or site_url("/")
        send_message(
            peer,
            "Привет! Сначала войди на сайт через VK или привяжи VK "
            f"в профиле, затем напиши сообществу снова.\n{site_url('/auth')}",
        )
        return

    if not user.vk_messages_allowed:
        user.vk_messages_allowed = True
        user.save(update_fields=["vk_messages_allowed"])

    # payload кнопок выбора ментора
    payload = ""
    if isinstance(msg.get("payload"), str):
        payload = msg["payload"].strip().strip('"')
    elif msg.get("payload"):
        payload = str(msg["payload"])

    if payload.startswith("thread:"):
        _select_thread_and_prompt(peer, user, payload.split(":", 1)[1])
        return

    cmd = text.split()[0].split("@")[0].lower() if text else ""
    if cmd in ("/start", "начать"):
        send_message(
            peer,
            f"Привет, {user.first_name}! Пиши сюда — сообщения уйдут "
            "ментору в чат на сайте.\n\n"
            "Команды:\n"
            "/unread — непрочитанные\n"
            "/calls — созвоны\n"
            "/progress — прогресс\n"
            "/help — справка",
        )
        return
    if cmd in ("/help", "/commands"):
        send_message(
            peer,
            "Команды:\n"
            "/unread — непрочитанные от ментора\n"
            "/calls — ожидающие созвоны\n"
            "/progress — курсы и streak\n\n"
            "Обычный текст и одно фото — в активный чат с ментором.\n"
            f"Сайт: {site_url('/')}",
        )
        return
    if cmd == "/unread":
        _cmd_unread(peer, user)
        return
    if cmd == "/calls":
        _cmd_calls(peer, user)
        return
    if cmd == "/progress":
        _cmd_progress(peer, user)
        return

    photo = _first_photo_url(msg)
    if not text and not photo:
        send_message(
            peer,
            "Пока принимаю текст и одно фото. Остальное — на сайте.",
        )
        return

    _relay_to_thread(peer, user, text=text, photo_url=photo)


def _first_photo_url(msg: dict) -> str | None:
    for att in msg.get("attachments") or []:
        if att.get("type") != "photo":
            continue
        photo = att.get("photo") or {}
        sizes = photo.get("sizes") or []
        if not sizes:
            continue
        best = max(sizes, key=lambda s: int(s.get("width") or 0))
        return best.get("url") or None
    return None


def _pending_key(vk_id: int) -> str:
    return f"{PENDING_THREAD_PREFIX}{vk_id}"


def _select_thread_and_prompt(peer: int, user, thread_public_id: str) -> None:
    from communication.models import DirectThread

    thread = DirectThread.objects.filter(public_id=thread_public_id).first()
    if not thread or user.pk not in (thread.mentor_id, thread.student_id):
        send_message(peer, "Диалог не найден. Напиши сообщение ещё раз.")
        return
    cache.set(
        _pending_key(user.vk_id), str(thread.public_id), PENDING_THREAD_TTL
    )
    other = thread.mentor if thread.student_id == user.pk else thread.student
    name = f"{other.first_name} {other.last_name}".strip()
    send_message(
        peer,
        f"Выбран чат с {name}. Напиши сообщение — оно уйдёт на сайт.",
    )


def _relay_to_thread(
    peer: int, user, *, text: str, photo_url: str | None
) -> None:
    from communication.chat_services import create_message, threads_for_user
    from communication.models import ChatMessage

    threads = list(threads_for_user(user)[:10])
    if not threads:
        send_message(
            peer,
            "Нет диалогов с ментором. Открой чат на сайте:\n"
            f"{site_url('/messages')}",
        )
        return

    pending_id = cache.get(_pending_key(user.vk_id))
    thread = None
    if pending_id:
        thread = next(
            (t for t in threads if str(t.public_id) == str(pending_id)),
            None,
        )

    if thread is None and len(threads) == 1:
        thread = threads[0]
    elif thread is None and len(threads) > 1:
        buttons = []
        for th in threads[:5]:
            other = th.mentor if th.student_id == user.pk else th.student
            label = (
                f"{other.first_name} {other.last_name}".strip() or "Диалог"
            )[:40]
            buttons.append(
                [
                    {
                        "action": {
                            "type": "text",
                            "label": label,
                            "payload": f"thread:{th.public_id}",
                        },
                        "color": "primary",
                    }
                ]
            )
        send_message(
            peer,
            "У тебя несколько диалогов. Выбери ментора кнопкой, "
            "затем напиши сообщение:",
            keyboard={"one_time": True, "buttons": buttons},
        )
        return

    if thread is None:
        send_message(peer, f"Открой чат на сайте: {site_url('/messages')}")
        return

    cache.set(
        _pending_key(user.vk_id), str(thread.public_id), PENDING_THREAD_TTL
    )

    upload = None
    if photo_url:
        downloaded = download_photo_url(photo_url)
        if downloaded:
            content, ctype = downloaded
            ext = "jpg"
            if "png" in ctype:
                ext = "png"
            elif "webp" in ctype:
                ext = "webp"
            upload = InMemoryUploadedFile(
                BytesIO(content),
                field_name="file",
                name=f"vk_photo.{ext}",
                content_type=ctype,
                size=len(content),
                charset=None,
            )

    try:
        create_message(
            thread=thread,
            sender=user,
            body=text or ("" if upload else ""),
            upload=upload,
            source=ChatMessage.Source.VK,
        )
    except Exception:
        logger.exception("VK→chat create_message failed")
        send_message(
            peer,
            "Не удалось отправить в чат. Попробуй на сайте:\n"
            f"{site_url('/messages')}",
        )
        return

    # Для текста без фото create_message требует body — если только фото, body=""
    # and upload set — OK for media. If only text — OK.
    # If both empty we already returned.


def _cmd_unread(peer: int, user) -> None:
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
        send_message(peer, "Непрочитанных нет.")
        return
    send_message(
        peer,
        f"Непрочитанных: {total}\n"
        + "\n".join(lines)
        + f"\n\nОткрыть: {site_url('/messages')}",
    )


def _cmd_calls(peer: int, user) -> None:
    from communication.models import Conference

    qs = Conference.objects.filter(
        guest=user,
        status=Conference.Status.WAITING,
    ).select_related("mentor")[:5]
    if not qs:
        send_message(peer, "Нет ожидающих созвонов.")
        return
    lines = []
    for c in qs:
        mentor = f"{c.mentor.first_name} {c.mentor.last_name}".strip()
        lines.append(f"• {mentor}\n  {site_url(f'/call?conf={c.public_id}')}")
    send_message(peer, "Ожидают созвоны:\n" + "\n".join(lines))


def _cmd_progress(peer: int, user) -> None:
    from education.models import Enrollment
    from progress.stats import compute_streak_days

    streak = compute_streak_days(user)
    ens = (
        Enrollment.objects.filter(user=user, status=Enrollment.Status.ACTIVE)
        .select_related("course")
        .order_by("-last_activity_at")[:5]
    )
    lines = [f"Streak: {streak} дн."]
    if not ens:
        lines.append("Активных курсов нет.")
    else:
        lines.append("Курсы:")
        for e in ens:
            title = getattr(e.course, "title", "Курс")
            lines.append(f"• {title}")
    lines.append(f"\nУчиться: {site_url('/catalog')}")
    send_message(peer, "\n".join(lines))
