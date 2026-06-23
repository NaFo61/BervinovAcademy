# Generated manually

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("progress", "0010_useranswercheckbox_failed_attempts"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonUserComment",
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
                    "lesson_kind",
                    models.CharField(
                        choices=[
                            ("theory", "Теория"),
                            ("radio", "Radio"),
                            ("checkbox", "Checkbox"),
                            ("coding", "Код"),
                        ],
                        db_index=True,
                        max_length=16,
                        verbose_name="Тип урока",
                    ),
                ),
                (
                    "lesson_public_id",
                    models.UUIDField(
                        db_index=True,
                        verbose_name="Урок (public_id)",
                    ),
                ),
                ("body", models.TextField(verbose_name="Текст комментария")),
                (
                    "is_hidden",
                    models.BooleanField(
                        default=False,
                        verbose_name="Скрыт модератором",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name="Создан",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлён"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_comments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Автор",
                    ),
                ),
            ],
            options={
                "verbose_name": "Комментарий к уроку",
                "verbose_name_plural": "Комментарии к урокам",
                "ordering": ("created_at",),
                "indexes": [
                    models.Index(
                        fields=["lesson_kind", "lesson_public_id", "created_at"],
                        name="progress_le_lesson__a1b2c3_idx",
                    ),
                    models.Index(
                        fields=["user", "-created_at"],
                        name="progress_le_user_id_d4e5f6_idx",
                    ),
                ],
            },
        ),
    ]
