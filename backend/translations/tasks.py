import logging

from celery import shared_task
from deep_translator import GoogleTranslator

from translations.models import TranslationMemory

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def translate_text(self, source_text, source_lang, target_lang, context=None):
    """Синхронная задача перевода"""
    try:
        source_text = source_text.strip()

        # Убираем await и sync_to_async
        existing = TranslationMemory.objects.filter(
            source_text=source_text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        ).first()

        logger.info(
            f"translate_text вызвался {source_text[:30]} ({source_lang}) "
            f"-> {target_lang}"
        )

        if existing:
            logger.info(
                f"translate_text найден в кэше: {existing.target_text[:30]}"
            )
            return existing.target_text

        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(source_text)

        # Сохраняем в БД
        TranslationMemory.objects.create(
            source_text=source_text,
            source_lang=source_lang,
            target_lang=target_lang,
            target_text=translated.strip(),
            context=context,
        )

        return translated

    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        self.retry(exc=e, countdown=5)
