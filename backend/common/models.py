import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDPublicIdMixin(models.Model):
    """Стабильный публичный UUID для внешнего API (URL и JSON без bigint id)."""

    public_id = models.UUIDField(
        _("Публичный идентификатор"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    class Meta:
        abstract = True
