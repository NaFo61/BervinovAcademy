"""Модели Web Push подписок."""

from __future__ import annotations

import secrets

from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def _default_link_token() -> str:
    """Оставлено для старых миграций TelegramLinkToken."""
    return secrets.token_urlsafe(24)


class PushSubscription(UUIDPublicIdMixin, models.Model):
    """Подписка браузера на Web Push."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name=_("Пользователь"),
    )
    endpoint = models.URLField(max_length=2048, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_success_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Web Push подписка")
        verbose_name_plural = _("Web Push подписки")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"push:{self.user_id}"
