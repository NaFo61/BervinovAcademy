# Generated manually for four-layer assistant prompts

from django.db import migrations, models

DEFAULT = (
    "Ты помощник ученика онлайн-школы. Отвечай по-русски коротко и чётко.\n"
    "Не выдавай полное решение сразу — сначала наводящие подсказки.\n\n"
    "Курс: {{course}}\n"
    "Модуль: {{module}}\n"
    "Тип урока: {{kind}}\n"
    "Задача: {{title}}\n\n"
    "Условие / материал:\n{{condition}}\n\n"
    "Инструкции:\n{{instructions}}\n\n"
    "Тесты:\n{{tests}}\n\n"
    "Код ученика (если есть):\n{{code}}\n\n"
    "Вопрос ученика придёт отдельным сообщением."
)


class Migration(migrations.Migration):

    dependencies = [
        ("mentoring", "0002_assistant_prompt_layers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assistantsettings",
            name="base_prompt",
            field=models.TextField(
                default=DEFAULT,
                help_text=(
                    "Общие правила школы. Дальше добавляются промпты курса, "
                    "модуля и урока. Плейсхолдеры: {{condition}}, "
                    "{{instructions}}, {{tests}}, {{title}}, {{course}}, "
                    "{{module}}, {{kind}}, {{code}}."
                ),
                verbose_name="Базовый промпт ИИ",
            ),
        ),
    ]
