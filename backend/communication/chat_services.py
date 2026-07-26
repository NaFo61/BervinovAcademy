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

from .models import (
    ChatMessage,
    ChatMessageAttachment,
    Conference,
    DirectThread,
)

User = get_user_model()

MAX_MESSAGE_LENGTH = 4000
MAX_CODE_LENGTH = 16000
CHAT_MAX_IMAGE_BYTES = 10 * 1024 * 1024
CHAT_MAX_VIDEO_BYTES = 50 * 1024 * 1024
CHAT_MAX_ALBUM_ITEMS = 10
CODE_LANGUAGE_PYTHON = "python"
EDITABLE_KINDS = frozenset({ChatMessage.Kind.TEXT, ChatMessage.Kind.CODE})
DELETABLE_KINDS = frozenset(
    {
        ChatMessage.Kind.TEXT,
        ChatMessage.Kind.CODE,
        ChatMessage.Kind.IMAGE,
        ChatMessage.Kind.VIDEO,
        ChatMessage.Kind.ALBUM,
    }
)
MEDIA_KINDS = frozenset(
    {
        ChatMessage.Kind.IMAGE,
        ChatMessage.Kind.VIDEO,
        ChatMessage.Kind.ALBUM,
    }
)


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
    from subscriptions.services import FEATURE_MENTOR_CHAT, user_has_feature

    if not user_has_feature(student, FEATURE_MENTOR_CHAT):
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
    if is_student_user(actor) and is_mentor_user(other):
        from subscriptions.services import (
            FEATURE_MENTOR_CHAT,
            user_has_feature,
        )

        if not user_has_feature(actor, FEATURE_MENTOR_CHAT):
            raise PermissionDenied("Чат с ментором доступен по тарифу Про.")
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
        from subscriptions.services import (
            FEATURE_MENTOR_CHAT,
            user_has_feature,
        )

        if not user_has_feature(actor, FEATURE_MENTOR_CHAT):
            raise PermissionDenied("Чат с ментором доступен по тарифу Про.")
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
    *,
    thread: DirectThread,
    sender,
    body: str,
    reply_to: ChatMessage | None = None,
) -> ChatMessage:
    return create_message(
        thread=thread,
        sender=sender,
        kind=ChatMessage.Kind.TEXT,
        body=body,
        reply_to=reply_to,
    )


def _resolve_reply_to(
    *, thread: DirectThread, reply_to_public_id: str | None
) -> ChatMessage | None:
    if not reply_to_public_id:
        return None
    try:
        reply = ChatMessage.objects.get(public_id=reply_to_public_id)
    except ChatMessage.DoesNotExist as exc:
        raise ValidationError({"reply_to": "Сообщение не найдено."}) from exc
    if reply.thread_id != thread.pk:
        raise ValidationError(
            {
                "reply_to": "Можно ответить только на сообщение из этого диалога."
            }
        )
    if reply.is_deleted:
        raise ValidationError({"reply_to": "Нельзя ответить на удалённое."})
    return reply


def _read_upload_header(upload, size: int = 64) -> bytes:
    pos = upload.tell() if hasattr(upload, "tell") else None
    header = upload.read(size) or b""
    if hasattr(upload, "seek"):
        try:
            upload.seek(pos or 0)
        except Exception:
            upload.seek(0)
    return header


def _sniff_chat_upload(upload) -> tuple[str, str]:
    """Определяет тип по magic bytes. Возвращает (kind, safe_ext)."""
    if upload is None:
        raise ValidationError({"files": "Нужен файл."})
    size = getattr(upload, "size", 0) or 0
    header = _read_upload_header(upload)

    kind = None
    ext = None
    if header.startswith(b"\xff\xd8\xff"):
        kind, ext = ChatMessageAttachment.Kind.IMAGE, ".jpg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        kind, ext = ChatMessageAttachment.Kind.IMAGE, ".png"
    elif header.startswith((b"GIF87a", b"GIF89a")):
        kind, ext = ChatMessageAttachment.Kind.IMAGE, ".gif"
    elif (
        len(header) >= 12
        and header.startswith(b"RIFF")
        and header[8:12] == b"WEBP"
    ):
        kind, ext = ChatMessageAttachment.Kind.IMAGE, ".webp"
    elif len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in (
            b"qt  ",
            b"isom",
            b"iso2",
            b"mp41",
            b"mp42",
            b"M4V ",
            b"avc1",
        ) or brand.startswith(b"mp4"):
            kind, ext = ChatMessageAttachment.Kind.VIDEO, ".mp4"
        else:
            # QuickTime / generic ISO BMFF — treat as video
            kind, ext = ChatMessageAttachment.Kind.VIDEO, ".mp4"
    elif header.startswith(b"\x1aE\xdf\xa3"):
        kind, ext = ChatMessageAttachment.Kind.VIDEO, ".webm"

    if kind is None:
        raise ValidationError(
            {
                "files": "Допустимы изображения (JPEG/PNG/WebP/GIF) или видео (MP4/WebM/MOV)."
            }
        )

    if (
        kind == ChatMessageAttachment.Kind.IMAGE
        and size > CHAT_MAX_IMAGE_BYTES
    ):
        raise ValidationError({"files": "Изображение не больше 10 МБ."})
    if (
        kind == ChatMessageAttachment.Kind.VIDEO
        and size > CHAT_MAX_VIDEO_BYTES
    ):
        raise ValidationError({"files": "Видео не больше 50 МБ."})
    return kind, ext


def _normalize_uploads(*, upload=None, uploads=None) -> list:
    files = [f for f in (uploads or []) if f is not None]
    if not files and upload is not None:
        files = [upload]
    return files


def _message_kind_for_items(item_kinds: list[str]) -> str:
    if not item_kinds:
        raise ValidationError({"files": "Нужен хотя бы один файл."})
    if len(item_kinds) == 1:
        return item_kinds[0]
    return ChatMessage.Kind.ALBUM


def message_preview_text(msg: ChatMessage) -> str:
    if msg.is_deleted:
        return "Сообщение удалено"
    if msg.kind == ChatMessage.Kind.SYSTEM:
        return (msg.body or "")[:120]
    if msg.kind == ChatMessage.Kind.IMAGE:
        caption = (msg.body or "").strip()
        return f"Фото{': ' + caption[:100] if caption else ''}"
    if msg.kind == ChatMessage.Kind.VIDEO:
        caption = (msg.body or "").strip()
        return f"Видео{': ' + caption[:100] if caption else ''}"
    if msg.kind == ChatMessage.Kind.ALBUM:
        caption = (msg.body or "").strip()
        count = msg.attachments.count() if msg.pk else 0
        label = f"Альбом ({count})" if count else "Альбом"
        return f"{label}{': ' + caption[:100] if caption else ''}"
    if msg.kind == ChatMessage.Kind.CODE:
        return "Код (python)"
    return (msg.body or "")[:120]


def _save_message_attachments(
    *,
    message: ChatMessage,
    files: list,
    item_kinds: list[str],
    safe_exts: list[str],
) -> None:
    from django.core.files.base import ContentFile

    first_path = None
    for index, (upload, item_kind, ext) in enumerate(
        zip(files, item_kinds, safe_exts)
    ):
        raw = upload.read()
        if hasattr(upload, "seek"):
            upload.seek(0)
        attachment = ChatMessageAttachment(
            message=message,
            kind=item_kind,
            sort_order=index,
        )
        attachment.file.save(
            f"upload{ext}",
            ContentFile(raw),
            save=True,
        )
        if first_path is None:
            first_path = attachment.file.name
    if first_path:
        message.attachment = first_path
        message.save(update_fields=["attachment"])


@transaction.atomic
def create_message(
    *,
    thread: DirectThread,
    sender,
    kind: str = ChatMessage.Kind.TEXT,
    body: str = "",
    reply_to: ChatMessage | None = None,
    reply_to_public_id: str | None = None,
    upload=None,
    uploads=None,
) -> ChatMessage:
    if not user_in_thread(sender, thread):
        raise PermissionDenied("Нет доступа к этому диалогу.")

    if reply_to is None:
        reply_to = _resolve_reply_to(
            thread=thread, reply_to_public_id=reply_to_public_id
        )

    text = (body or "").strip()
    files = _normalize_uploads(upload=upload, uploads=uploads)
    item_kinds: list[str] = []
    safe_exts: list[str] = []

    if files:
        if len(files) > CHAT_MAX_ALBUM_ITEMS:
            raise ValidationError(
                {
                    "files": f"Не больше {CHAT_MAX_ALBUM_ITEMS} файлов в альбоме."
                }
            )
        for upload_file in files:
            item_kind, ext = _sniff_chat_upload(upload_file)
            item_kinds.append(item_kind)
            safe_exts.append(ext)
        kind = _message_kind_for_items(item_kinds)
        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValidationError(
                {"body": f"Подпись не более {MAX_MESSAGE_LENGTH} символов."}
            )
    elif kind in MEDIA_KINDS:
        raise ValidationError({"files": "Нужен файл."})
    elif kind == ChatMessage.Kind.TEXT:
        if not text:
            raise ValidationError({"body": "Сообщение не может быть пустым."})
        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValidationError(
                {"body": f"Не более {MAX_MESSAGE_LENGTH} символов."}
            )
    elif kind == ChatMessage.Kind.CODE:
        if not text:
            raise ValidationError({"body": "Вставьте код."})
        if len(text) > MAX_CODE_LENGTH:
            raise ValidationError(
                {"body": f"Не более {MAX_CODE_LENGTH} символов."}
            )
    else:
        raise ValidationError({"kind": "Неподдерживаемый тип сообщения."})

    now = timezone.now()
    message = ChatMessage(
        thread=thread,
        kind=kind,
        sender=sender,
        body=text,
        code_language=(
            CODE_LANGUAGE_PYTHON if kind == ChatMessage.Kind.CODE else ""
        ),
        reply_to=reply_to,
    )
    message.save()
    if files:
        _save_message_attachments(
            message=message,
            files=files,
            item_kinds=item_kinds,
            safe_exts=safe_exts,
        )

    thread.last_message_at = now
    thread.save(update_fields=["last_message_at"])

    message = (
        ChatMessage.objects.select_related(
            "sender",
            "reply_to",
            "reply_to__sender",
            "forwarded_from",
            "forwarded_from__sender",
            "conference",
            "conference__whiteboard",
        )
        .prefetch_related("attachments")
        .get(pk=message.pk)
    )

    broadcast_chat_event(
        thread=thread,
        event="message.new",
        payload=_serialize_message_for_ws(message),
    )

    # Уведомление собеседнику (ментор → студент и наоборот)
    if kind != ChatMessage.Kind.SYSTEM and sender is not None:
        recipient = (
            thread.student if sender.pk == thread.mentor_id else thread.mentor
        )
        if recipient and recipient.pk != sender.pk:
            preview = (text or "").strip()
            if not preview and kind in MEDIA_KINDS:
                preview = "Медиа"
            if kind == ChatMessage.Kind.CODE:
                preview = "Код (Python)"
            preview = preview[:180] or "Новое сообщение"
            sender_name = (
                f"{sender.first_name} {sender.last_name}".strip()
                or "Собеседник"
            )
            from notify.dispatch import create_and_deliver, site_url

            from communication.models import UserNotification

            # In-app только для студента (ментор и так в кабинете);
            # Telegram/Push — обоим.
            persist = recipient.pk == thread.student_id
            other_id = (
                thread.mentor.public_id
                if recipient.pk == thread.student_id
                else thread.student.public_id
            )
            create_and_deliver(
                user=recipient,
                kind=UserNotification.Kind.MENTOR_MESSAGE,
                title=f"Сообщение от {sender_name}",
                body=preview,
                url=site_url(f"/messages?user={other_id}"),
                persist=persist,
            )

    return message


@transaction.atomic
def forward_message(
    *,
    source: ChatMessage,
    actor,
    target_thread: DirectThread,
) -> ChatMessage:
    if source.is_deleted:
        raise ValidationError({"detail": "Нельзя переслать удалённое."})
    if source.kind == ChatMessage.Kind.SYSTEM:
        raise ValidationError(
            {"detail": "Системные сообщения нельзя пересылать."}
        )
    if not user_in_thread(actor, source.thread):
        raise PermissionDenied("Нет доступа к исходному сообщению.")
    if not user_in_thread(actor, target_thread):
        raise PermissionDenied("Нет доступа к целевому диалогу.")

    now = timezone.now()
    message = ChatMessage(
        thread=target_thread,
        kind=source.kind,
        sender=actor,
        body=source.body,
        code_language=source.code_language,
        forwarded_from=source,
    )
    message.save()

    source_attachments = list(source.attachments.order_by("sort_order", "id"))
    if source_attachments:
        from pathlib import Path

        from django.core.files.base import ContentFile

        copied = []
        item_kinds = []
        safe_exts = []
        for item in source_attachments:
            item.file.open("rb")
            try:
                content = item.file.read()
            finally:
                item.file.close()
            name = Path(item.file.name).name
            blob = ContentFile(content, name=name)
            kind, ext = _sniff_chat_upload(blob)
            copied.append(blob)
            item_kinds.append(kind)
            safe_exts.append(ext)
        _save_message_attachments(
            message=message,
            files=copied,
            item_kinds=item_kinds,
            safe_exts=safe_exts,
        )
    elif source.attachment:
        from pathlib import Path

        from django.core.files.base import ContentFile

        source.attachment.open("rb")
        try:
            content = source.attachment.read()
        finally:
            source.attachment.close()
        name = Path(source.attachment.name).name
        blob = ContentFile(content, name=name)
        kind, ext = _sniff_chat_upload(blob)
        _save_message_attachments(
            message=message,
            files=[blob],
            item_kinds=[kind],
            safe_exts=[ext],
        )

    target_thread.last_message_at = now
    target_thread.save(update_fields=["last_message_at"])

    message = (
        ChatMessage.objects.select_related(
            "sender",
            "forwarded_from",
            "forwarded_from__sender",
        )
        .prefetch_related("attachments")
        .get(pk=message.pk)
    )

    broadcast_chat_event(
        thread=target_thread,
        event="message.new",
        payload=_serialize_message_for_ws(message),
    )
    return message


def list_thread_messages(
    *, thread: DirectThread, before=None, limit: int = 50
):
    qs = (
        thread.messages.select_related(
            "sender",
            "conference",
            "conference__whiteboard",
            "reply_to",
            "reply_to__sender",
            "forwarded_from",
            "forwarded_from__sender",
        )
        .prefetch_related("attachments")
        .order_by("-created_at")
    )
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
        message = (
            ChatMessage.objects.select_related(
                "sender",
                "thread",
                "reply_to",
                "reply_to__sender",
                "forwarded_from",
                "forwarded_from__sender",
            )
            .prefetch_related("attachments")
            .get(public_id=message_public_id)
        )
    except ChatMessage.DoesNotExist as exc:
        raise NotFound("Сообщение не найдено.") from exc
    if not user_in_thread(user, message.thread):
        raise PermissionDenied("Нет доступа к этому сообщению.")
    return message


def _validate_own_editable_message(*, message: ChatMessage, actor) -> None:
    if message.kind not in EDITABLE_KINDS:
        raise ValidationError(
            {"detail": "Этот тип сообщения нельзя изменить."}
        )
    if message.is_deleted:
        raise ValidationError({"detail": "Сообщение уже удалено."})
    if message.sender_id != actor.pk:
        raise PermissionDenied("Можно изменять только свои сообщения.")


def _validate_own_deletable_message(*, message: ChatMessage, actor) -> None:
    if message.kind not in DELETABLE_KINDS:
        raise ValidationError(
            {"detail": "Системные сообщения нельзя удалять."}
        )
    if message.is_deleted:
        raise ValidationError({"detail": "Сообщение уже удалено."})
    if message.sender_id != actor.pk:
        raise PermissionDenied("Можно удалять только свои сообщения.")


@transaction.atomic
def update_text_message(
    *, message: ChatMessage, editor, body: str
) -> ChatMessage:
    _validate_own_editable_message(message=message, actor=editor)
    text = (body or "").strip()
    if not text:
        raise ValidationError({"body": "Сообщение не может быть пустым."})
    max_len = (
        MAX_CODE_LENGTH
        if message.kind == ChatMessage.Kind.CODE
        else MAX_MESSAGE_LENGTH
    )
    if len(text) > max_len:
        raise ValidationError({"body": f"Не более {max_len} символов."})

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
    _validate_own_deletable_message(message=message, actor=deleter)
    deleted_paths: set[str] = set()
    for item in list(message.attachments.all()):
        if item.file:
            deleted_paths.add(item.file.name)
            item.file.delete(save=False)
        item.delete()
    if message.attachment and message.attachment.name not in deleted_paths:
        message.attachment.delete(save=False)
    message.attachment = None
    message.body = ""
    message.is_deleted = True
    message.save(update_fields=["is_deleted", "body", "attachment"])

    broadcast_chat_event(
        thread=message.thread,
        event="message.deleted",
        payload=_serialize_message_for_ws(message),
    )
    return message
