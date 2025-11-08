from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import Specialization


@receiver(post_save, sender=Specialization)
def auto_translate_specialization(sender, instance, created, **kwargs):
    instance.auto_translate_fields(created=created)
