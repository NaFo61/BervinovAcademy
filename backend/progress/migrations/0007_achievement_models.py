import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0006_userlessontheoryread"),
    ]

    operations = [
        migrations.CreateModel(
            name="Achievement",
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
                    "code",
                    models.SlugField(max_length=64, unique=True, verbose_name="Код"),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("tasks_solved", "Решено задач"),
                            ("theories_read", "Прочитано теорий"),
                            ("courses_completed", "Завершено курсов"),
                            ("quizzes_solved", "Решено тестов"),
                            ("streak_days", "Дней подряд"),
                        ],
                        db_index=True,
                        max_length=32,
                        verbose_name="Тип",
                    ),
                ),
                (
                    "threshold",
                    models.PositiveIntegerField(
                        help_text="Минимальное значение метрики для разблокировки",
                        verbose_name="Порог",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=120, verbose_name="Название"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Описание"),
                ),
                (
                    "emoji",
                    models.CharField(
                        default="🏆", max_length=16, verbose_name="Эмодзи"
                    ),
                ),
                (
                    "order_index",
                    models.PositiveIntegerField(default=0, verbose_name="Порядок"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активно"),
                ),
            ],
            options={
                "verbose_name": "Достижение",
                "verbose_name_plural": "Достижения",
                "ordering": ("order_index", "threshold", "code"),
            },
        ),
        migrations.CreateModel(
            name="UserAchievement",
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
                    "unlocked_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name="Разблокировано",
                    ),
                ),
                (
                    "achievement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_unlocks",
                        to="progress.achievement",
                        verbose_name="Достижение",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="achievements",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Достижение пользователя",
                "verbose_name_plural": "Достижения пользователей",
                "ordering": ("-unlocked_at",),
                "unique_together": {("user", "achievement")},
            },
        ),
        migrations.AddIndex(
            model_name="achievement",
            index=models.Index(
                fields=["kind", "threshold"],
                name="progress_ach_kind_0a8f2d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userachievement",
            index=models.Index(
                fields=["user", "-unlocked_at"],
                name="progress_use_user_id_91b4e2_idx",
            ),
        ),
    ]
