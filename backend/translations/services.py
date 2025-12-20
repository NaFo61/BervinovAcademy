from django.db import transaction


class TranslationService:
    @staticmethod
    def get_translation(text, source_lang, target_lang, context=None):
        from translations.models import TranslationMemory  # noqa
        from translations.tasks import translate_text  # noqa

        text = text.strip()
        existing = TranslationMemory.objects.filter(
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        ).first()

        if existing:
            return existing.target_text

        # Если нет перевода — отправляем в Celery
        # translate_text.delay(text, source_lang, target_lang, context)
        transaction.on_commit(
            lambda: translate_text.delay(
                text, source_lang, target_lang, context
            )
        )
        return "в процессе"  # можно вернуть "в процессе"
