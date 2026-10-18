from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tutoringlesson",
            name="homework_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Не отмечено"),
                    ("done", "Сдал"),
                    ("not_done", "Не сдал"),
                ],
                db_index=True,
                default="",
                max_length=16,
                verbose_name="Домашка",
            ),
        ),
        migrations.AddField(
            model_name="tutoringlesson",
            name="learned_note",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="Чему научился",
            ),
        ),
    ]
