"""Бизнес-логика чата ментор ↔ студент."""

from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from content.models import Course
from education.models import Enrollment

from .models import ChatMessage, Conference, DirectThread

User = get_user_model()

MAX_MESSAGE_LENGTH = 4000


def is_mentor_user(user) -> bool:
    return getattr(user, "role", None) in ("mentor", "admin")


def is_student_user(user) -> bool:
    return getattr(user, "role", None) == "student"


def user_in_thread(user, thread: DirectThread) -> bool:
    return user.pk in (thread.mentor_id, thread.student_id)


def _last_read_field_for_user(user, thread: DirectThread) -> str:
    if user.pk == thread.mentor_id:
        return "mentor_last_read_at"
    if user.pk == thread.student_id:
        return "student_last_read_at"
    raise PermissionDenied("Нет доступа к этому диалогу.")


def user_last_read_at(thread: DirectThread, user):
    field = _last_read_field_for_user(user, thread)
    return getattr(thread, field)


def thread_unread_count(*, thread: DirectThread, user) -> int:
    if not user_in_thread(user, thread):
        return 0
    last_read = user_last_read_at(thread, user)
    qs = thread.messages.filter(is_deleted=False).exclude(sender_id=user.pk)
    if last_read:
        qs = qs.filter(created_at__gt=last_read)
    return qs.count()


def total_unread_count(*, user) -> int:
    total = 0
    for thread in threads_for_user(user):
        total += thread_unread_count(thread=thread, user=user)
    return total


@transaction.atomic
def mark_thread_read(*, thread: DirectThread, user, at=None) -> DirectThread:
    if not user_in_thread(user, thread):
        raise PermissionDenied("Нет доступа к этому диалогу.")
    field = _last_read_field_for_user(user, thread)
    now = at or timezone.now()
    current = getattr(thread, field)
    if current is None or now > current:
        setattr(thread, field, now)
        thread.save(update_fields=[field])
    return thread


def student_may_message_mentor(*, student, mentor) -> bool:
    if not is_mentor_user(mentor) or not is_student_user(student):
        return False
    return Enrollment.objects.filter(
        user=student,
        course__mentor=mentor,
    ).exists()


def mentor_may_message_student(*, mentor, student) -> bool:
    if not is_mentor_user(mentor) or not is_student_user(student):
        return False
    return True


def can_open_thread(*, actor, other) -> bool:
    if actor.pk == other.pk:
        return False
    if is_mentor_user(actor) and is_student_user(other):
        return mentor_may_message_student(mentor=actor, student=other)
    if is_student_user(actor) and is_mentor_user(other):
        return student_may_message_mentor(student=actor, mentor=other)
    return False


def normalize_thread_participants(*, actor, other) -> tuple[User, User]:
    if not can_open_thread(actor=actor, other=other):
        raise PermissionDenied("Нет доступа к диалогу с этим пользователем.")
    if is_mentor_user(actor):
        return actor, other
    return other, actor


def resolve_open_target(*, actor, user_public_id=None, course_public_id=None):
    if user_public_id and course_public_id:
        raise ValidationError(
            {"detail": "Укажите user или course, но не оба параметра."}
        )

    if course_public_id:
        if not is_student_user(actor):
            raise PermissionDenied(
                "Открыть чат по курсу может только студент."
            )
        try:
            course = Course.objects.select_related("mentor").get(
                public_id=course_public_id,
                is_active=True,
            )
        except Course.DoesNotExist as exc:
            raise ValidationError({"course": "Курс не найден."}) from exc
        if not course.mentor_id:
            raise ValidationError({"course": "У курса не назначен ментор."})
        if not Enrollment.objects.filter(user=actor, course=course).exists():
            raise PermissionDenied("Вы не записаны на этот курс.")
        return course.mentor

    if not user_public_id:
        raise ValidationError({"detail": "Нужен параметр user или course."})

    try:
        other = User.objects.get(public_id=user_public_id)
    except User.DoesNotExist as exc:
        raise ValidationError({"user": "Пользователь не найден."}) from exc

    return other


def open_thread(
    *,
    actor,
    user_public_id=None,
    course_public_id=None,
    conference_public_id=None,
) -> DirectThread:
    params = [user_public_id, course_public_id, conference_public_id]
    if sum(bool(x) for x in params) != 1:
        raise ValidationError(
            {
                "detail": "Нужен ровно один параметр: user, course или conference."
            }
        )

    if conference_public_id:
        try:
            conference = Conference.objects.select_related(
                "mentor", "guest"
            ).get(public_id=conference_public_id)
        except Conference.DoesNotExist as exc:
            raise ValidationError({"conference": "Созвон не найден."}) from exc
        if actor.pk not in (conference.mentor_id, conference.guest_id):
            raise PermissionDenied("Нет доступа к этому созвону.")
        thread, _created = DirectThread.objects.get_or_create(
            mentor=conference.mentor,
            student=conference.guest,
        )
        return thread

    other = resolve_open_target(
        actor=actor,
        user_public_id=user_public_id,
        course_public_id=course_public_id,
    )
    return get_or_create_thread(actor=actor, other=other)


@transaction.atomic
def get_or_create_thread(*, actor, other) -> DirectThread:
    mentor, student = normalize_thread_participants(actor=actor, other=other)
    thread, _created = DirectThread.objects.get_or_create(
        mentor=mentor,
        student=student,
    )
    return thread


def threads_for_user(user):
    return (
        DirectThread.objects.select_related("mentor", "student")
        .filter(Q(mentor=user) | Q(student=user))
        .order_by("-last_message_at", "-created_at")
    )


def thread_for_user(*, user, thread_public_id) -> DirectThread:
    try:
        thread = DirectThread.objects.select_related("mentor", "student").get(
            public_id=thread_public_id
        )
    except DirectThread.DoesNotExist as exc:
        raise NotFound("Диалог не найден.") from exc
    if not user_in_thread(user, thread):
        raise PermissionDenied("Нет доступа к этому диалогу.")
    return thread


def _serialize_message_for_ws(message: ChatMessage) -> dict:
    from .serializers import ChatMessageSerializer

    return ChatMessageSerializer(message).data


def broadcast_chat_event(
    *, thread: DirectThread, event: str, payload: dict
) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_thread_{thread.public_id}",
        {
            "type": "chat.event",
            "event": event,
            "payload": payload,
        },
    )


@transaction.atomic
def create_text_message(
    *, thread: DirectThread, sender, body: str
) -> ChatMessage:
    text = (body or "").strip()
    if not text:
        raise ValidationError({"body": "Сообщение не может быть пустым."})
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            {"body": f"Не более {MAX_MESSAGE_LENGTH} символов."}
        )
    if not user_in_thread(sender, thread):
        raise PermissionDenied("Нет доступа к этому диалогу.")

    now = timezone.now()
    message = ChatMessage.objects.create(
        thread=thread,
        kind=ChatMessage.Kind.TEXT,
        sender=sender,
        body=text,
    )
    thread.last_message_at = now
    thread.save(update_fields=["last_message_at"])

    broadcast_chat_event(
        thread=thread,
        event="message.new",
        payload=_serialize_message_for_ws(message),
    )
    return message


def list_thread_messages(
    *, thread: DirectThread, before=None, limit: int = 50
):
    qs = thread.messages.select_related(
        "sender", "conference", "conference__whiteboard"
    ).order_by("-created_at")
    if before:
        qs = qs.filter(created_at__lt=before)
    limit = max(1, min(limit, 100))
    rows = list(qs[: limit + 1])
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    rows.reverse()
    return rows, has_more


def message_for_user(*, user, message_public_id) -> ChatMessage:
    try:
        message = ChatMessage.objects.select_related("sender", "thread").get(
            public_id=message_public_id
        )
    except ChatMessage.DoesNotExist as exc:
        raise NotFound("Сообщение не найдено.") from exc
    if not user_in_thread(user, message.thread):
        raise PermissionDenied("Нет доступа к этому сообщению.")
    return message


def _validate_own_text_message(*, message: ChatMessage, actor) -> None:
    if message.kind != ChatMessage.Kind.TEXT:
        raise ValidationError(
            {"detail": "Системные сообщения нельзя изменять."}
        )
    if message.is_deleted:
        raise ValidationError({"detail": "Сообщение уже удалено."})
    if message.sender_id != actor.pk:
        raise PermissionDenied("Можно изменять только свои сообщения.")


@transaction.atomic
def update_text_message(
    *, message: ChatMessage, editor, body: str
) -> ChatMessage:
    _validate_own_text_message(message=message, actor=editor)
    text = (body or "").strip()
    if not text:
        raise ValidationError({"body": "Сообщение не может быть пустым."})
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            {"body": f"Не более {MAX_MESSAGE_LENGTH} символов."}
        )

    message.body = text
    message.edited_at = timezone.now()
    message.show_edited = is_student_user(editor)
    message.save(update_fields=["body", "edited_at", "show_edited"])

    broadcast_chat_event(
        thread=message.thread,
        event="message.updated",
        payload=_serialize_message_for_ws(message),
    )
    return message


@transaction.atomic
def delete_text_message(*, message: ChatMessage, deleter) -> ChatMessage:
    _validate_own_text_message(message=message, actor=deleter)
    message.is_deleted = True
    message.save(update_fields=["is_deleted"])

    broadcast_chat_event(
        thread=message.thread,
        event="message.deleted",
        payload=_serialize_message_for_ws(message),
    )
    return message
