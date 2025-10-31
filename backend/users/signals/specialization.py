from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import Specialization
from users.tasks import translate_specialization_title


@receiver(post_save, sender=Specialization)
def schedule_specialization_translation(sender, instance, created, **kwargs):
    if created or instance.has_title_changed():
        print("запускаем перевод")
        translate_specialization_title(instance.id)
