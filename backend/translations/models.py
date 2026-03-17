from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TranslationMemory(models.Model):
    source_text = models.TextField(
        verbose_name=_("Исходный текст"),
        help_text=_("Оригинальный текст для перевода."),
    )
    source_lang = models.CharField(
        max_length=10,
        verbose_name=_("Исходный язык"),
        help_text=_("Язык исходного текста (например, 'en', 'ru')."),
    )

    target_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Переведенный текст"),
        help_text=_("Переведенная версия текста."),
    )
    target_lang = models.CharField(
        max_length=10,
        verbose_name=_("Целевой язык"),
        help_text=_(
            "Язык, на который был переведен текст (например, 'en', 'ru')."
        ),
    )

    context = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Контекст"),
        help_text=_(
            "Где используется этот перевод, например: "
            "'Specialization.title' или 'Lesson.description'."
        ),
    )

    last_edited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Последний редактор"),
        help_text=_(
            "Пользователь, который вручную отредактировал этот перевод."
        ),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Одобрено"),
        help_text=_(
            "Отметьте как одобрено, если перевод "
            "был проверен администратором."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления"),
    )

    class Meta:
        unique_together = (
            "source_text",
            "source_lang",
            "target_lang",
            "context",
        )
        verbose_name = _("Перевод")
        verbose_name_plural = _("Переводы")
        ordering = ("-updated_at",)

    def __str__(self):
        text_preview = self.source_text[:40].strip().replace("\n", " ")
        return (
            f"[{self.source_lang} → {self.target_lang}] {text_preview or '—'}"
        )
