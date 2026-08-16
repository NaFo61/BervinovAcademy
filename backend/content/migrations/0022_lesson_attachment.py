import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import content.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("content", "0021_assistant_prompt_four_layers"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonAttachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Публичный идентификатор",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=content.models.lesson_attachment_upload_to,
                        verbose_name="Файл",
                    ),
                ),
                (
                    "original_name",
                    models.CharField(
                        max_length=255, verbose_name="Имя файла"
                    ),
                ),
                (
                    "content_type",
                    models.CharField(
                        blank=True, max_length=128, verbose_name="MIME-тип"
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Размер, байт"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "checkbox",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="content.lessoncheckboxquestion",
                        verbose_name="Checkbox",
                    ),
                ),
                (
                    "coding",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="content.codingchallenge",
                        verbose_name="Задача с кодом",
                    ),
                ),
                (
                    "radio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="content.lessonradioquestion",
                        verbose_name="Radio",
                    ),
                ),
                (
                    "short_answer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="content.lessonshortanswer",
                        verbose_name="Краткий ответ",
                    ),
                ),
                (
                    "theory",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="content.lessontheory",
                        verbose_name="Теория",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lesson_attachments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Загрузил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Файл задания",
                "verbose_name_plural": "Файлы заданий",
                "ordering": ("created_at", "id"),
            },
        ),
    ]
