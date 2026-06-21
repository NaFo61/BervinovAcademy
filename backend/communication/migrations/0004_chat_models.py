# Generated manually for chat models

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0003_conference_whiteboard"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectThread",
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
                    ),
                ),
                (
                    "last_message_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="Последнее сообщение",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "mentor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mentor_chat_threads",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Ментор",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_chat_threads",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Студент",
                    ),
                ),
            ],
            options={
                "verbose_name": "Диалог",
                "verbose_name_plural": "Диалоги",
                "ordering": ("-last_message_at", "-created_at"),
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
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
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("text", "Текст"), ("system", "Системное")],
                        db_index=True,
                        default="text",
                        max_length=16,
                        verbose_name="Тип",
                    ),
                ),
                ("body", models.TextField(verbose_name="Текст")),
                (
                    "is_deleted",
                    models.BooleanField(default=False, verbose_name="Удалено"),
                ),
                (
                    "edited_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Изменено"
                    ),
                ),
                (
                    "show_edited",
                    models.BooleanField(
                        default=False,
                        verbose_name="Показывать метку «изменено»",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "sender",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="chat_messages_sent",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Отправитель",
                    ),
                ),
                (
                    "thread",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="communication.directthread",
                        verbose_name="Диалог",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сообщение чата",
                "verbose_name_plural": "Сообщения чата",
                "ordering": ("created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="directthread",
            constraint=models.UniqueConstraint(
                fields=("mentor", "student"),
                name="communicati_mentor__chat_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="directthread",
            index=models.Index(
                fields=["mentor", "-last_message_at"],
                name="communicati_mentor__chat_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="directthread",
            index=models.Index(
                fields=["student", "-last_message_at"],
                name="communicati_student_chat_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(
                fields=["thread", "-created_at"],
                name="communicati_thread__chat_idx",
            ),
        ),
    ]
