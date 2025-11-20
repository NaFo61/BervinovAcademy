from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from translations.models import TranslationMemory


@receiver(post_save, sender=TranslationMemory)
def apply_translation_to_model(sender, instance, created, **kwargs):
    if not instance.context or not instance.target_text:
        return

    try:
        model_name, field_name = instance.context.split(".", 1)
    except ValueError:
        print("")
        return

    model_class = None

    for app_label, models in apps.all_models.items():
        if model_name.lower() in models:
            model_class = apps.get_model(app_label, model_name)
            break

    if model_class is None:
        print(f"⚠️ Model '{model_name}' not found in any registered app.")
        return

    obj = model_class.objects.filter(
        **{field_name: instance.source_text}
    ).first()
    if not obj:
        return

    lang = instance.target_lang
    field_translated = f"{field_name}_{lang}"

    if hasattr(obj, field_translated):
        setattr(obj, field_translated, instance.target_text)
        obj.save(update_fields=[field_translated])
        print(
            f"Updated {model_name}.{field_translated} → {instance.target_text}"
        )
