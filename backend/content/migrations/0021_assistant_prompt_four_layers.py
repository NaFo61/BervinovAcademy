# Generated manually for four-layer assistant prompts

from django.db import migrations, models

_LESSON_HELP = (
    "Дополнение к общему / курсу / модулю для этого урока. "
    "Плейсхолдеры: {{condition}}, {{instructions}}, {{tests}}, "
    "{{title}}, {{course}}, {{module}}, {{kind}}, {{code}}."
)


def _lesson_field():
    return models.TextField(
        blank=True,
        help_text=_LESSON_HELP,
        verbose_name="Промпт ИИ (урок)",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0020_assistant_prompt_layers"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="assistant_prompt",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Дополнение к общему промпту для всех уроков курса. "
                    "Плейсхолдеры: {{condition}}, {{instructions}}, {{tests}}, "
                    "{{title}}, {{course}}, {{module}}, {{kind}}, {{code}}."
                ),
                verbose_name="Промпт ИИ курса",
            ),
        ),
        migrations.AddField(
            model_name="lessontheory",
            name="assistant_prompt",
            field=_lesson_field(),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="assistant_prompt",
            field=_lesson_field(),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="assistant_prompt",
            field=_lesson_field(),
        ),
        migrations.AddField(
            model_name="lessonshortanswer",
            name="assistant_prompt",
            field=_lesson_field(),
        ),
        migrations.AlterField(
            model_name="module",
            name="assistant_prompt",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Дополнение к общему и курсовому промпту для уроков модуля. "
                    "Можно вставить {{condition}} / {{instructions}}, чтобы "
                    "модель видела текст задания. Плейсхолдеры: {{condition}}, "
                    "{{instructions}}, {{tests}}, {{title}}, {{course}}, "
                    "{{module}}, {{kind}}, {{code}}."
                ),
                verbose_name="Промпт ИИ модуля",
            ),
        ),
        migrations.AlterField(
            model_name="codingchallenge",
            name="assistant_prompt",
            field=_lesson_field(),
        ),
    ]
