import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_module_lesson_shared_order"),
        ("progress", "0005_alter_useranswerradio_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserLessonTheoryRead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
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
                ("read_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="Прочитано в")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_reads", to="content.lessontheory", verbose_name="Теоретический урок")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="theory_reads", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Прочтение теории",
                "verbose_name_plural": "Прочтения теории",
                "ordering": ("-read_at",),
                "unique_together": {("user", "lesson")},
            },
        ),
        migrations.AddIndex(
            model_name="userlessontheoryread",
            index=models.Index(fields=["user", "lesson"], name="progress_use_user_id_3d5c9c_idx"),
        ),
        migrations.AddIndex(
            model_name="userlessontheoryread",
            index=models.Index(fields=["lesson", "-read_at"], name="progress_use_lesson_i_44c6d9_idx"),
        ),
    ]
