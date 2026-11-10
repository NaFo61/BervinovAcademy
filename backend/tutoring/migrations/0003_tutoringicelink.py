from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0002_lesson_homework_note"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TutoringIceLink",
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
                    "ice_tutor_id",
                    models.PositiveIntegerField(
                        db_index=True, verbose_name="ICE tutor id"
                    ),
                ),
                (
                    "telegram_id",
                    models.BigIntegerField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="Telegram id",
                    ),
                ),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Имя в боте",
                    ),
                ),
                (
                    "linked_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Привязан"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ice_link",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Связь с ICE",
                "verbose_name_plural": "Связи с ICE",
            },
        ),
    ]
