# Generated manually for ConferenceWhiteboard

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0002_conference_presence_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConferenceWhiteboard",
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
                    "image",
                    models.ImageField(
                        upload_to="whiteboards/%Y/%m/",
                        verbose_name="Изображение",
                    ),
                ),
                (
                    "snapshot_json",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Snapshot JSON",
                    ),
                ),
                ("exported_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conference",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whiteboard",
                        to="communication.conference",
                        verbose_name="Конференция",
                    ),
                ),
                (
                    "exported_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="exported_whiteboards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Экспортировал",
                    ),
                ),
            ],
            options={
                "verbose_name": "Доска конференции",
                "verbose_name_plural": "Доски конференций",
            },
        ),
    ]
