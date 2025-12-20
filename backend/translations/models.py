from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TranslationMemory(models.Model):
    source_text = models.TextField(
        verbose_name=_("Source text"),
        help_text=_("The original text to be translated."),
    )
    source_lang = models.CharField(
        max_length=10,
        verbose_name=_("Source language"),
        help_text=_("Language of the source text (e.g. 'en', 'ru')."),
    )

    target_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Translated text"),
        help_text=_("The translated version of the text."),
    )
    target_lang = models.CharField(
        max_length=10,
        verbose_name=_("Target language"),
        help_text=_(
            "Language to which the text was translated (e.g. 'en', 'ru')."
        ),
    )

    context = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Context"),
        help_text=_(
            "Where this translation is used, e.g. "
            "'Specialization.title' or 'Lesson.description'."
        ),
    )

    last_edited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Last edited by"),
        help_text=_("User who manually edited this translation."),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Approved"),
        help_text=_(
            "Mark as approved if the translation "
            "was verified by an administrator."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        unique_together = (
            "source_text",
            "source_lang",
            "target_lang",
            "context",
        )
        verbose_name = _("Translation")
        verbose_name_plural = _("Translations")
        ordering = ("-updated_at",)

    def __str__(self):
        text_preview = self.source_text[:40].strip().replace("\n", " ")
        return (
            f"[{self.source_lang} → {self.target_lang}] {text_preview or '—'}"
        )
