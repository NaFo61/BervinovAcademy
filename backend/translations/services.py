import logging

logger = logging.getLogger(__name__)


class TranslationService:
    @staticmethod
    def get_translation(text, source_lang, target_lang, context=None):
        """Синхронное получение перевода"""
        from translations.models import TranslationMemory
        from translations.tasks import translate_text

        text = text.strip()

        # Проверяем кэш
        existing = TranslationMemory.objects.filter(
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        ).first()

        if existing:
            return existing.target_text

        # Отправляем задачу в Celery и ждем результат
        result = translate_text.delay(text, source_lang, target_lang, context)

        try:
            # Ждем результат до 10 секунд
            translated = result.get(timeout=10)
            return translated
        except Exception as e:
            logger.error(f"Ошибка получения перевода: {e}")
            return "в процессе"  # или вернуть оригинал
