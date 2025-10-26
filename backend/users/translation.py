from django.contrib.auth import get_user_model
from modeltranslation.translator import TranslationOptions, register

User = get_user_model()


@register(User)
class UserTranslationOptions(TranslationOptions):
    fields = ("bio",)
