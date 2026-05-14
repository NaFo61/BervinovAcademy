import logging

from celery import shared_task
from deep_translator import GoogleTranslator

from translations.models import TranslationMemory

logger = logging.getLogger(__name__)


def perform_translation(source_text, source_lang, target_lang, context=None):
    """
    Перевод и запись в TranslationMemory в текущем процессе (без брокера).

    Вызывается из TranslationService: вызывающий уже ждёт результат, поэтому
    очередь Celery только добавляет гонку с воркером при сидинге и холодном
    старте контейнеров.
    """
    source_text = source_text.strip()

    existing = TranslationMemory.objects.filter(
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        context=context,
    ).first()

    logger.info(
        "perform_translation %r (%s) -> %s",
        source_text[:30],
        source_lang,
        target_lang,
    )

    if existing:
        logger.info(
            "perform_translation cache hit: %r",
            existing.target_text[:30],
        )
        return existing.target_text

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    translated = translator.translate(source_text)

    TranslationMemory.objects.create(
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        target_text=translated.strip(),
        context=context,
    )

    return translated


@shared_task(bind=True, max_retries=3)
def translate_text(self, source_text, source_lang, target_lang, context=None):
    """Фоновая задача перевода (например, для массовых операций)."""
    try:
        return perform_translation(
            source_text, source_lang, target_lang, context
        )
    except Exception as e:
        logger.error("Ошибка перевода: %s", e)
        self.retry(exc=e, countdown=5)
