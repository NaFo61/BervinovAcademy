# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0014_course_mentor"),
    ]

    operations = [
        migrations.AddField(
            model_name="lessontheory",
            name="comment",
            field=models.TextField(
                blank=True,
                help_text="Пояснение или заметка к уроку, показывается на вкладке материала",
                verbose_name="Комментарий",
            ),
        ),
        migrations.AddField(
            model_name="lessontheory",
            name="solution_text",
            field=models.TextField(
                blank=True,
                help_text="Текст на вкладке «Эталонное решение» (вместе с видео)",
                verbose_name="Текст эталонного решения",
            ),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="comment",
            field=models.TextField(
                blank=True,
                help_text="Пояснение к заданию на вкладке «Задание»",
                verbose_name="Комментарий",
            ),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="solution_text",
            field=models.TextField(
                blank=True,
                help_text="Текст на вкладке «Эталонное решение»",
                verbose_name="Текст эталонного решения",
            ),
        ),
        migrations.AlterField(
            model_name="lessonradioquestion",
            name="explanation",
            field=models.TextField(
                blank=True,
                help_text="Краткий комментарий после ответа (правильного или неверного)",
                verbose_name="Пояснение",
            ),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="comment",
            field=models.TextField(
                blank=True,
                help_text="Пояснение к заданию на вкладке «Задание»",
                verbose_name="Комментарий",
            ),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="solution_text",
            field=models.TextField(
                blank=True,
                help_text="Текст на вкладке «Эталонное решение»",
                verbose_name="Текст эталонного решения",
            ),
        ),
        migrations.AlterField(
            model_name="lessoncheckboxquestion",
            name="explanation",
            field=models.TextField(
                blank=True,
                help_text="Краткий комментарий после ответа (правильного или неверного)",
                verbose_name="Пояснение",
            ),
        ),
        migrations.AddField(
            model_name="codingchallenge",
            name="comment",
            field=models.TextField(
                blank=True,
                help_text="Пояснение к задаче на вкладке «Задание»",
                verbose_name="Комментарий",
            ),
        ),
        migrations.AddField(
            model_name="codingchallenge",
            name="solution_text",
            field=models.TextField(
                blank=True,
                help_text="Текст на вкладке «Эталонное решение»",
                verbose_name="Текст эталонного решения",
            ),
        ),
    ]
