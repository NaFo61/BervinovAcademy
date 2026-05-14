import logging

logger = logging.getLogger(__name__)


class TranslationService:
    @staticmethod
    def get_translation(text, source_lang, target_lang, context=None):
        """Синхронное получение перевода (выполняется в этом процессе)."""
        # Ленивый импорт: иначе users.models → mixins → services → tasks
        # → translations.models → get_user_model() до установки User.
        from translations.models import TranslationMemory
        from translations.tasks import perform_translation

        text = text.strip()

        existing = TranslationMemory.objects.filter(
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        ).first()

        if existing:
            return existing.target_text

        try:
            return perform_translation(text, source_lang, target_lang, context)
        except Exception as e:
            logger.exception("Ошибка получения перевода: %s", e)
            return "в процессе"
