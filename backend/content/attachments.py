"""Файлы преподавателя к уроку/заданию. Тот же FileField/S3, что видео."""

from __future__ import annotations

from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

ALLOWED_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".zip",
        ".txt",
        ".md",
    }
)
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_FILES_PER_LESSON = 10

KIND_FK = {
    "theory": "theory",
    "radio": "radio",
    "checkbox": "checkbox",
    "short_answer": "short_answer",
    "coding": "coding",
}


def lesson_attachment_upload_to(instance, filename):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".bin"
    kind = resolved_kind(instance) or "lesson"
    stamp = timezone.now().strftime("%Y/%m")
    import uuid

    return f"lesson_attachments/{kind}/{stamp}/{uuid.uuid4().hex}{ext}"


def resolved_kind(instance) -> str:
    if getattr(instance, "theory_id", None):
        return "theory"
    if getattr(instance, "radio_id", None):
        return "radio"
    if getattr(instance, "checkbox_id", None):
        return "checkbox"
    if getattr(instance, "short_answer_id", None):
        return "short_answer"
    if getattr(instance, "coding_id", None):
        return "coding"
    return ""


def bind_parent(*, attachment, kind: str, lesson) -> None:
    fk = KIND_FK.get(kind)
    if not fk:
        raise ValidationError({"kind": "Неизвестный тип урока."})
    for name in KIND_FK.values():
        setattr(attachment, name, None)
    setattr(attachment, fk, lesson)


def validate_upload(upload) -> None:
    if upload is None:
        raise ValidationError({"file": "Прикрепите файл."})
    name = getattr(upload, "name", "") or "file"
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            {
                "file": (
                    "Этот тип файла нельзя прикрепить. "
                    "Можно: pdf, Word, Excel, PowerPoint, картинки "
                    "(включая svg), zip, txt, md."
                )
            }
        )
    size = int(getattr(upload, "size", 0) or 0)
    if size > MAX_FILE_BYTES:
        raise ValidationError(
            {"file": "Файл больше 20 МБ. Сожмите его или разбейте на части."}
        )
    if size <= 0:
        raise ValidationError({"file": "Пустой файл нельзя сохранить."})


def serialize_attachment(obj, request=None) -> dict:
    url = ""
    if obj.file and obj.file.name:
        try:
            url = obj.file.url
        except ValueError:
            url = ""
        if request and url.startswith("/"):
            url = request.build_absolute_uri(url)
    return {
        "public_id": str(obj.public_id),
        "name": obj.original_name or Path(obj.file.name).name,
        "size": obj.size,
        "content_type": obj.content_type or "",
        "url": url,
    }


def serialize_lesson_attachments(lesson, request=None) -> list[dict]:
    items = list(lesson.attachments.all())
    items.sort(key=lambda row: (row.created_at, row.pk))
    return [serialize_attachment(row, request) for row in items]


class LessonAttachmentsMixin(serializers.Serializer):
    attachments = serializers.SerializerMethodField()

    def get_attachments(self, obj):
        return serialize_lesson_attachments(obj, self.context.get("request"))
