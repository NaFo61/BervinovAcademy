from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("communication", "0014_lesson_summary_and_board_assets"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserBoard",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "snapshot_json",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Сохранённый рисунок",
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_board",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Владелец",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_user_boards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Последний правил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Личная доска",
                "verbose_name_plural": "Личные доски",
            },
        ),
    ]
