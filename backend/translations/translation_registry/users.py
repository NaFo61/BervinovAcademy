from modeltranslation.translator import TranslationOptions, register

from users.models import Specialization


@register(Specialization)
class SpecializationTranslationOptions(TranslationOptions):
    fields = ("title", "description")
