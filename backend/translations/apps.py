from django.apps import AppConfig


class TranslationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "translations"

    def ready(self):
        import translations.signals  # noqa
        import translations.translation_registry.users  # noqa
