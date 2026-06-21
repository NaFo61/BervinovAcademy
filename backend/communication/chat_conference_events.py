"""Системные события созвонов в ленте чата."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from . import chat_services
from .models import ChatMessage, Conference, DirectThread

_UNIQUE_EVENTS = {
    ChatMessage.SystemEvent.CONFERENCE_INVITED,
    ChatMessage.SystemEvent.CONFERENCE_STARTED,
    ChatMessage.SystemEvent.CONFERENCE_ENDED,
    ChatMessage.SystemEvent.CONFERENCE_DECLINED,
    ChatMessage.SystemEvent.CONFERENCE_CANCELLED,
}


def _display_name(user) -> str:
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email or str(user.public_id)


def _conference_duration_seconds(conference: Conference) -> int | None:
    if conference.started_at and conference.ended_at:
        return int(
            (conference.ended_at - conference.started_at).total_seconds()
        )
    return None


def _format_duration(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return ""
    minutes, secs = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours} ч {minutes} мин"
    if minutes:
        return f"{minutes} мин {secs} с"
    return f"{secs} с"


def _thread_for_conference(conference: Conference) -> DirectThread:
    thread, _created = DirectThread.objects.get_or_create(
        mentor=conference.mentor,
        student=conference.guest,
    )
    return thread


def _build_payload(
    *,
    conference: Conference,
    event: str,
    actor=None,
) -> dict:
    payload = {
        "event": event,
        "conference_public_id": str(conference.public_id),
        "conference_status": conference.status,
    }
    if actor is not None:
        payload["actor_public_id"] = str(actor.public_id)
        payload["actor_name"] = _display_name(actor)
    duration = _conference_duration_seconds(conference)
    if duration is not None:
        payload["duration_seconds"] = duration
        payload["duration_label"] = _format_duration(duration)
    board = None
    try:
        board = conference.whiteboard
    except Exception:
        board = None
    if board and board.image:
        payload["has_whiteboard"] = True
    return payload


def _format_body(
    *,
    conference: Conference,
    event: str,
    actor=None,
) -> str:
    actor_name = _display_name(actor) if actor else "Участник"
    if event == ChatMessage.SystemEvent.CONFERENCE_INVITED:
        return f"{actor_name} пригласил на созвон"
    if event == ChatMessage.SystemEvent.CONFERENCE_STARTED:
        return "Созвон начался"
    if event == ChatMessage.SystemEvent.CONFERENCE_REJOINED:
        return f"{actor_name} вернулся в созвон"
    if event == ChatMessage.SystemEvent.CONFERENCE_ENDED:
        label = _format_duration(_conference_duration_seconds(conference))
        return f"Созвон завершён{(' · ' + label) if label else ''}"
    if event == ChatMessage.SystemEvent.CONFERENCE_DECLINED:
        return f"{actor_name} отклонил созвон"
    if event == ChatMessage.SystemEvent.CONFERENCE_CANCELLED:
        return f"{actor_name} отменил созвон"
    return "Событие созвона"


@transaction.atomic
def append_conference_chat_event(
    *,
    conference: Conference,
    event: str,
    actor=None,
) -> ChatMessage | None:
    if (
        event in _UNIQUE_EVENTS
        and ChatMessage.objects.filter(
            conference=conference,
            system_event=event,
        ).exists()
    ):
        return None

    thread = _thread_for_conference(conference)
    now = timezone.now()
    message = ChatMessage.objects.create(
        thread=thread,
        kind=ChatMessage.Kind.SYSTEM,
        sender=actor,
        body=_format_body(conference=conference, event=event, actor=actor),
        conference=conference,
        system_event=event,
        system_payload=_build_payload(
            conference=conference,
            event=event,
            actor=actor,
        ),
    )
    thread.last_message_at = now
    thread.save(update_fields=["last_message_at"])

    chat_services.broadcast_chat_event(
        thread=thread,
        event="message.new",
        payload=chat_services._serialize_message_for_ws(message),
    )
    return message


def maybe_emit_conference_join_event(
    *,
    conference: Conference,
    user,
    became_active: bool,
    rejoined: bool,
) -> None:
    if became_active:
        append_conference_chat_event(
            conference=conference,
            event=ChatMessage.SystemEvent.CONFERENCE_STARTED,
            actor=user,
        )
    elif rejoined:
        append_conference_chat_event(
            conference=conference,
            event=ChatMessage.SystemEvent.CONFERENCE_REJOINED,
            actor=user,
        )


def maybe_emit_conference_ended_event(
    *,
    conference: Conference,
    user=None,
) -> None:
    conference.refresh_from_db()
    append_conference_chat_event(
        conference=conference,
        event=ChatMessage.SystemEvent.CONFERENCE_ENDED,
        actor=user,
    )
