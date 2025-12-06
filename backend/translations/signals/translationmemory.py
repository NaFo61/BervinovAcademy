import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from translations.models import TranslationMemory

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TranslationMemory)
def apply_translation_to_model(sender, instance, created, **kwargs):
    # нет контекста или текста — пропускаем
    if not instance.context or not instance.target_text:
        return

    # context = "Specialization.title"
    try:
        model_name, field_name = instance.context.split(".", 1)
    except ValueError:
        return

    # Ищем модель среди всех
    model_class = None
    for app_label, models in apps.all_models.items():
        if model_name.lower() in models:
            model_class = apps.get_model(app_label, model_name)
            break

    if not model_class:
        logger.info(f"Не нашел {instance.context = }")
        return
    logger.info(f"Нашел {instance.context = }")

    d = {field_name: instance.source_text}

    # Ищем объект по исходному полю
    objs = model_class.objects.filter(**d)

    logger.info(
        f"{model_class}.objects.filter(**{d}) | {model_class.objects.all()}"
    )

    if not objs.exists():
        logger.info(f"Не нашел {objs = }")
        return
    logger.info(f"Нашел {objs = }")

    # Определяем target-поле (title_ru, title_en, description_en, ...)
    field_translated = f"{field_name}_{instance.target_lang}"

    for obj in objs:
        setattr(obj, field_translated, instance.target_text)

        try:
            obj.save(update_fields=[field_translated])
            obj.save()
        except Exception:
            pass
