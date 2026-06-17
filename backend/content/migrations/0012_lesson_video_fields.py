from django.db import migrations, models

import content.models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_module_lesson_shared_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="lessontheory",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=content.models._lesson_video_upload_to,
                verbose_name="Видеофайл",
            ),
        ),
        migrations.AddField(
            model_name="lessontheory",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="Ссылка на YouTube, Rutube или VK Видео (необязательно)",
                max_length=500,
                verbose_name="Ссылка на видео",
            ),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=content.models._lesson_video_upload_to,
                verbose_name="Видеофайл",
            ),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="Ссылка на YouTube, Rutube или VK Видео (необязательно)",
                max_length=500,
                verbose_name="Ссылка на видео",
            ),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=content.models._lesson_video_upload_to,
                verbose_name="Видеофайл",
            ),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="Ссылка на YouTube, Rutube или VK Видео (необязательно)",
                max_length=500,
                verbose_name="Ссылка на видео",
            ),
        ),
        migrations.AddField(
            model_name="codingchallenge",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=content.models._lesson_video_upload_to,
                verbose_name="Видеофайл",
            ),
        ),
        migrations.AddField(
            model_name="codingchallenge",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="Ссылка на YouTube, Rutube или VK Видео (необязательно)",
                max_length=500,
                verbose_name="Ссылка на видео",
            ),
        ),
    ]
