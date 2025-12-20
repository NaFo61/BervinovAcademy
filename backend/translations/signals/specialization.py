import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import Specialization

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Specialization)
def auto_translate_specialization(
    sender, instance, created, update_fields=None, **kwargs
):
    logger.info(f"SIGNAL: {update_fields}")
    if update_fields:
        # Если любой из update_fields заканчивается на _ru или _en —
        # пропускаем.
        if any(f.endswith(("_ru", "_en")) for f in update_fields):
            return
    logger.info("запуск auto")
    instance.auto_translate_fields()
