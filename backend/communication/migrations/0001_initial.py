import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conference",
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
                    "room_name",
                    models.CharField(
                        max_length=128,
                        unique=True,
                        verbose_name="Комната LiveKit",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("waiting", "Ожидание"),
                            ("active", "Идёт"),
                            ("completed", "Завершена"),
                            ("declined", "Отклонена"),
                            ("cancelled", "Отменена"),
                            ("expired", "Истекла"),
                        ],
                        db_index=True,
                        default="waiting",
                        max_length=16,
                        verbose_name="Статус",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                (
                    "ended_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ended_conferences",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Завершил",
                    ),
                ),
                (
                    "guest",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="guest_conferences",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Участник",
                    ),
                ),
                (
                    "mentor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mentor_conferences",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Ментор",
                    ),
                ),
            ],
            options={
                "verbose_name": "Конференция",
                "verbose_name_plural": "Конференции",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="UserNotification",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("conference_invite", "Приглашение на созвон"),
                        ],
                        max_length=32,
                        verbose_name="Тип",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=255, verbose_name="Заголовок"),
                ),
                ("body", models.TextField(blank=True, verbose_name="Текст")),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("dismissed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "conference",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="communication.conference",
                        verbose_name="Конференция",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Уведомление",
                "verbose_name_plural": "Уведомления",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="conference",
            index=models.Index(
                fields=["mentor", "-created_at"],
                name="communicati_mentor__a8e4c2_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="conference",
            index=models.Index(
                fields=["guest", "-created_at"],
                name="communicati_guest_i_91f0ab_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="conference",
            index=models.Index(
                fields=["status", "-created_at"],
                name="communicati_status_4b2f11_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(
                fields=["user", "-created_at"],
                name="communicati_user_id_6d8e21_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(
                fields=["user", "dismissed_at", "-created_at"],
                name="communicati_user_id_2c7a55_idx",
            ),
        ),
    ]
