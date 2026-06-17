import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_module_lesson_shared_order"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Enrollment",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "В процессе"),
                            ("completed", "Завершён"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name="Начало",
                    ),
                ),
                (
                    "last_activity_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Последняя активность",
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Завершён",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="content.course",
                        verbose_name="Курс",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Запись на курс",
                "verbose_name_plural": "Записи на курсы",
                "ordering": ("-last_activity_at",),
                "unique_together": {("user", "course")},
            },
        ),
        migrations.AddIndex(
            model_name="enrollment",
            index=models.Index(
                fields=["user", "-last_activity_at"],
                name="education_en_user_id_8a1f2d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="enrollment",
            index=models.Index(
                fields=["course", "status"],
                name="education_en_course__91c4e0_idx",
            ),
        ),
    ]
