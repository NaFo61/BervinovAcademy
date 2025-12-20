import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from translations.models import TranslationMemory

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TranslationMemory)
def apply_translation_to_model(
    sender, instance: TranslationMemory, created, **kwargs
):
    if not instance.target_text:
        return
    model_name, field_name = instance.context.split(".", 1)
    try:
        model_class = apps.get_model(model_name=model_name)
    except Exception:
        model_class = None
        for app_label, models in apps.all_models.items():
            if model_name.lower() in models:
                model_class = apps.get_model(app_label, model_name)
                break
    if not model_class:
        logger.warning(f"Модель не найдена из контекста: {instance.context}")
        return
    source_value = (instance.source_text or "").strip()
    search_fields = [
        field_name,
        f"{field_name}_ru",
        f"{field_name}_en",
    ]
    objs = None
    found_field = None
    for f in search_fields:
        qs = model_class.objects.filter(**{f"{f}__iexact": source_value})
        if qs.exists():
            objs = qs
            found_field = f
            break
    if not objs:
        logger.warning(
            f"Не найден объект {model_class.__name__} по полям "
            f"{search_fields} значению: {repr(source_value)}"
        )
        return
    translated_field = f"{field_name}_{instance.target_lang}"
    if translated_field not in [
        f.name for f in model_class._meta.get_fields()
    ]:
        logger.warning(
            f"У модели {model_class.__name__} нет поля {translated_field}"
        )
        return
    for obj in objs:
        logger.info(
            f"Нашёл объект по {found_field}: {obj} -> обновляю "
            f"{translated_field} = {instance.target_text!r}"
        )
        setattr(obj, translated_field, instance.target_text)
        obj.save(update_fields=[translated_field])
    logger.info(
        f"Перевод применён к {objs.count()} объектам {model_class.__name__}"
    )
