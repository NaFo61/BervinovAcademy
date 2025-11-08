from translations.services import TranslationService


class AutoTranslateMixin:
    def get_translatable_fields(self):
        return getattr(self, "translatable_fields", [])

    def auto_translate_fields(self, created=False):
        for field in self.get_translatable_fields():
            old_value = getattr(self, f"_{field}_cache", None)
            new_value = getattr(self, field, None)

            if created or old_value != new_value:
                TranslationService.get_translation(
                    new_value,
                    "ru",
                    "en",
                    context=f"{self.__class__.__name__}.{field}",
                )
                TranslationService.get_translation(
                    new_value,
                    "en",
                    "ru",
                    context=f"{self.__class__.__name__}.{field}",
                )

            setattr(self, f"_{field}_cache", new_value)
