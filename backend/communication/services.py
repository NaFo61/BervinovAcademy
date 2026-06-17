"""Бизнес-логика конференций и уведомлений."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .livekit_tokens import livekit_configured
from .models import Conference, UserNotification

User = get_user_model()

TERMINAL_STATUSES = {
    Conference.Status.COMPLETED,
    Conference.Status.DECLINED,
    Conference.Status.CANCELLED,
    Conference.Status.EXPIRED,
}


def _display_name(user) -> str:
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email or str(user.public_id)


def _cancel_stale_waiting(mentor, guest) -> None:
    Conference.objects.filter(
        mentor=mentor,
        guest=guest,
        status=Conference.Status.WAITING,
    ).update(
        status=Conference.Status.CANCELLED,
        ended_at=timezone.now(),
        ended_by=mentor,
    )


def _set_ended_fields(conference: Conference, *, status, user=None) -> None:
    conference.status = status
    conference.ended_at = timezone.now()
    conference.ended_by = user
    conference.mentor_in_room = False
    conference.guest_in_room = False
    if not conference.started_at:
        conference.started_at = conference.ended_at


async def _delete_livekit_room_async(room_name: str) -> None:
    if not livekit_configured():
        return

    from livekit.api import DeleteRoomRequest, LiveKitAPI

    api = LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    try:
        await api.room.delete_room(DeleteRoomRequest(room=room_name))
    finally:
        await api.aclose()


def delete_livekit_room(room_name: str) -> None:
    """Удалить комнату в LiveKit Cloud, если она ещё существует."""

    if not room_name:
        return

    import asyncio

    try:
        asyncio.run(_delete_livekit_room_async(room_name))
    except Exception:
        # LiveKit мог уже удалить пустую комнату сам; статус в БД важнее.
        return


async def _list_livekit_participants_async(room_name: str) -> set[str]:
    if not livekit_configured():
        return set()

    from livekit.api import ListParticipantsRequest, LiveKitAPI

    api = LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    try:
        resp = await api.room.list_participants(
            ListParticipantsRequest(room=room_name)
        )
        return {p.identity for p in resp.participants}
    finally:
        await api.aclose()


def list_livekit_participants(room_name: str) -> set[str]:
    import asyncio

    try:
        return asyncio.run(_list_livekit_participants_async(room_name))
    except Exception:
        return set()


@transaction.atomic
def create_conference(*, mentor, guest) -> Conference:
    if mentor.pk == guest.pk:
        raise ValueError("Нельзя создать созвон с самим собой.")

    _cancel_stale_waiting(mentor, guest)

    conference = Conference.objects.create(
        mentor=mentor,
        guest=guest,
        room_name=f"conf-{uuid.uuid4()}",
    )

    mentor_name = _display_name(mentor)
    UserNotification.objects.create(
        user=guest,
        kind=UserNotification.Kind.CONFERENCE_INVITE,
        title=f"Приглашение на созвон от {mentor_name}",
        body=f"{mentor_name} приглашает вас на видеозвонок.",
        conference=conference,
    )
    return conference


def user_may_access_conference(user, conference: Conference) -> bool:
    return user.pk in (conference.mentor_id, conference.guest_id)


def mark_conference_joined(*, conference: Conference, user) -> Conference:
    if conference.status in TERMINAL_STATUSES:
        return conference

    now = timezone.now()
    if user.pk == conference.guest_id:
        conference.guest_in_room = True
        conference.guest_joined_at = conference.guest_joined_at or now
        conference.last_guest_left_at = None
        if conference.status == Conference.Status.WAITING:
            conference.status = Conference.Status.ACTIVE
            conference.started_at = now
        conference.save(
            update_fields=[
                "status",
                "started_at",
                "guest_in_room",
                "guest_joined_at",
                "last_guest_left_at",
            ]
        )
    elif user.pk == conference.mentor_id:
        conference.mentor_in_room = True
        conference.mentor_joined_at = conference.mentor_joined_at or now
        conference.last_mentor_left_at = None
        conference.save(
            update_fields=[
                "mentor_in_room",
                "mentor_joined_at",
                "last_mentor_left_at",
            ]
        )
    return conference


def end_conference(*, conference: Conference, user) -> Conference:
    if conference.status in TERMINAL_STATUSES:
        return conference

    _set_ended_fields(
        conference, status=Conference.Status.COMPLETED, user=user
    )
    conference.save(
        update_fields=[
            "status",
            "ended_at",
            "ended_by",
            "started_at",
            "mentor_in_room",
            "guest_in_room",
        ]
    )
    delete_livekit_room(conference.room_name)
    return conference


def decline_conference(*, conference: Conference, user) -> Conference:
    if conference.status in TERMINAL_STATUSES:
        return conference
    if user.pk != conference.guest_id:
        raise PermissionError("Отклонить может только приглашённый участник.")

    _set_ended_fields(conference, status=Conference.Status.DECLINED, user=user)
    conference.save(
        update_fields=[
            "status",
            "ended_at",
            "ended_by",
            "started_at",
            "mentor_in_room",
            "guest_in_room",
        ]
    )
    delete_livekit_room(conference.room_name)

    UserNotification.objects.filter(
        conference=conference,
        user=user,
        dismissed_at__isnull=True,
    ).update(dismissed_at=timezone.now())
    return conference


def cancel_conference(*, conference: Conference, user) -> Conference:
    if conference.status in TERMINAL_STATUSES:
        return conference
    if user.pk != conference.mentor_id:
        raise PermissionError("Отменить может только ментор.")

    _set_ended_fields(
        conference, status=Conference.Status.CANCELLED, user=user
    )
    conference.save(
        update_fields=[
            "status",
            "ended_at",
            "ended_by",
            "started_at",
            "mentor_in_room",
            "guest_in_room",
        ]
    )
    delete_livekit_room(conference.room_name)
    return conference


def expire_stale_conferences(*, ttl_hours: int) -> int:
    cutoff = timezone.now() - timezone.timedelta(hours=ttl_hours)
    qs = Conference.objects.filter(
        status=Conference.Status.WAITING,
        created_at__lt=cutoff,
    )
    count = qs.count()
    if count:
        room_names = list(qs.values_list("room_name", flat=True))
        qs.update(
            status=Conference.Status.EXPIRED,
            ended_at=timezone.now(),
            mentor_in_room=False,
            guest_in_room=False,
        )
        for room_name in room_names:
            delete_livekit_room(room_name)
    return count


def mark_conference_left(*, conference: Conference, user) -> Conference:
    if conference.status in TERMINAL_STATUSES:
        return conference

    now = timezone.now()
    if user.pk == conference.mentor_id:
        conference.mentor_in_room = False
        conference.last_mentor_left_at = now
        conference.save(
            update_fields=["mentor_in_room", "last_mentor_left_at"]
        )
    elif user.pk == conference.guest_id:
        conference.guest_in_room = False
        conference.last_guest_left_at = now
        conference.save(update_fields=["guest_in_room", "last_guest_left_at"])
    return conference


def sync_conference_presence(conference: Conference) -> Conference:
    identities = list_livekit_participants(conference.room_name)
    now = timezone.now()
    mentor_id = str(conference.mentor.public_id)
    guest_id = str(conference.guest.public_id)
    mentor_in_room = mentor_id in identities
    guest_in_room = guest_id in identities
    update_fields = []

    if conference.mentor_in_room != mentor_in_room:
        conference.mentor_in_room = mentor_in_room
        update_fields.append("mentor_in_room")
        if mentor_in_room:
            conference.mentor_joined_at = conference.mentor_joined_at or now
            conference.last_mentor_left_at = None
            update_fields.extend(["mentor_joined_at", "last_mentor_left_at"])
        else:
            conference.last_mentor_left_at = (
                conference.last_mentor_left_at or now
            )
            update_fields.append("last_mentor_left_at")

    if conference.guest_in_room != guest_in_room:
        conference.guest_in_room = guest_in_room
        update_fields.append("guest_in_room")
        if guest_in_room:
            conference.guest_joined_at = conference.guest_joined_at or now
            conference.last_guest_left_at = None
            update_fields.extend(["guest_joined_at", "last_guest_left_at"])
        else:
            conference.last_guest_left_at = (
                conference.last_guest_left_at or now
            )
            update_fields.append("last_guest_left_at")

    if guest_in_room and conference.status == Conference.Status.WAITING:
        conference.status = Conference.Status.ACTIVE
        conference.started_at = conference.started_at or now
        update_fields.extend(["status", "started_at"])

    if update_fields:
        conference.save(update_fields=sorted(set(update_fields)))
    return conference


def close_conferences_without_mentor(*, absence_minutes: int) -> int:
    now = timezone.now()
    cutoff = now - timezone.timedelta(minutes=absence_minutes)
    closed = 0
    qs = (
        Conference.objects.select_related("mentor", "guest")
        .filter(
            status__in=[Conference.Status.WAITING, Conference.Status.ACTIVE]
        )
        .order_by("created_at")
    )

    for conference in qs:
        sync_conference_presence(conference)
        if conference.mentor_in_room:
            continue
        if not conference.last_mentor_left_at:
            conference.last_mentor_left_at = now
            conference.save(update_fields=["last_mentor_left_at"])
            continue
        if conference.last_mentor_left_at <= cutoff:
            _set_ended_fields(
                conference,
                status=Conference.Status.COMPLETED,
                user=conference.mentor,
            )
            conference.save(
                update_fields=[
                    "status",
                    "ended_at",
                    "ended_by",
                    "started_at",
                    "mentor_in_room",
                    "guest_in_room",
                ]
            )
            delete_livekit_room(conference.room_name)
            closed += 1
    return closed


def apply_livekit_webhook_event(event) -> Conference | None:
    room_name = getattr(getattr(event, "room", None), "name", None)
    if not room_name:
        return None

    try:
        conference = Conference.objects.select_related("mentor", "guest").get(
            room_name=room_name
        )
    except Conference.DoesNotExist:
        return None

    event_name = getattr(event, "event", "")
    identity = getattr(getattr(event, "participant", None), "identity", None)
    user = None
    if identity:
        try:
            user = User.objects.get(public_id=identity)
        except (User.DoesNotExist, ValueError):
            user = None

    if event_name == "participant_joined" and user:
        return mark_conference_joined(conference=conference, user=user)
    if event_name == "participant_left" and user:
        return mark_conference_left(conference=conference, user=user)
    if (
        event_name == "room_finished"
        and conference.status not in TERMINAL_STATUSES
    ):
        _set_ended_fields(
            conference,
            status=Conference.Status.COMPLETED,
            user=conference.mentor,
        )
        conference.save(
            update_fields=[
                "status",
                "ended_at",
                "ended_by",
                "started_at",
                "mentor_in_room",
                "guest_in_room",
            ]
        )
        return conference

    return conference
