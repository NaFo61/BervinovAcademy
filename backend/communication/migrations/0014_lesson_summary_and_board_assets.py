import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import communication.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("communication", "0013_chat_source_telegram"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="conferencewhiteboard",
            options={
                "verbose_name": "Снимок доски конференции",
                "verbose_name_plural": "Снимки досок конференций",
            },
        ),
        migrations.CreateModel(
            name="BoardAsset",
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
                        upload_to=communication.models.board_asset_upload_to,
                        verbose_name="Файл",
                    ),
                ),
                (
                    "original_name",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Имя файла",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=128,
                        verbose_name="MIME",
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Размер"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="board_assets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Загрузил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ассет доски",
                "verbose_name_plural": "Ассеты доски",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="ConferenceLessonSummary",
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
                    "audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=communication.models.lesson_summary_audio_upload_to,
                        verbose_name="Аудио",
                    ),
                ),
                (
                    "transcript",
                    models.TextField(
                        blank=True, default="", verbose_name="Расшифровка"
                    ),
                ),
                (
                    "summary_md",
                    models.TextField(
                        blank=True, default="", verbose_name="Конспект"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Готовится"),
                            ("ready", "Готов"),
                            ("failed", "Ошибка"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "error_message",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=500,
                        verbose_name="Ошибка",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "conference",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_summary",
                        to="communication.conference",
                        verbose_name="Конференция",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_lesson_summaries",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Запросил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Конспект урока",
                "verbose_name_plural": "Конспекты уроков",
            },
        ),
    ]
