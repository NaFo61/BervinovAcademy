"""Настройки ИИ-помощника (базовый шаблон промпта)."""

from django.db import models
from django.utils.translation import gettext_lazy as _

DEFAULT_ASSISTANT_BASE_PROMPT = (
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


class AssistantSettings(models.Model):
    """Singleton: один базовый промпт на всю школу."""

    base_prompt = models.TextField(
        verbose_name=_("Базовый промпт ИИ"),
        help_text=_(
            "Общие правила школы. Дальше добавляются промпты курса, "
            "модуля и урока. Плейсхолдеры: {{condition}}, "
            "{{instructions}}, {{tests}}, {{title}}, {{course}}, "
            "{{module}}, {{kind}}, {{code}}."
        ),
        default=DEFAULT_ASSISTANT_BASE_PROMPT,
    )

    class Meta:
        verbose_name = _("Настройки ИИ-помощника")
        verbose_name_plural = _("Настройки ИИ-помощника")

    def __str__(self):
        return "Базовый промпт ИИ"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"base_prompt": DEFAULT_ASSISTANT_BASE_PROMPT},
        )
        return obj
