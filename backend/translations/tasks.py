from celery import shared_task
from googletrans import Translator

from translations.models import TranslationMemory


@shared_task(bind=True, max_retries=3)
def translate_text(self, source_text, source_lang, target_lang, context=None):
    translator = Translator()

    try:
        # Проверяем, есть ли уже перевод
        existing = TranslationMemory.objects.filter(
            source_text=source_text.strip(),
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        ).first()

        if existing:
            return existing.target_text

        translated = translator.translate(
            source_text, src=source_lang, dest=target_lang
        ).text

        TranslationMemory.objects.create(
            source_text=source_text.strip(),
            source_lang=source_lang,
            target_lang=target_lang,
            target_text=translated.strip(),
            context=context,
        )

        return f"✅ Переведено: {translated}"

    except Exception as e:
        self.retry(exc=e, countdown=5)
        return f"❌ Ошибка перевода: {e}"
