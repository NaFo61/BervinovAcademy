from django.apps import AppConfig


class TutoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tutoring"
    verbose_name = "Занятия с ментором"

    def ready(self):
        from django.db.models.signals import pre_migrate

        pre_migrate.connect(
            ensure_btree_gist,
            sender=self,
            dispatch_uid="tutoring.btree_gist",
        )


def ensure_btree_gist(sender, using, **kwargs):
    """Нужно до ограничения «уроки ментора не пересекаются»."""
    from django.db import connections

    connection = connections[using]
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
