"""Модели привязки Telegram и Web Push подписок."""

from __future__ import annotations

import secrets

from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _default_link_token() -> str:
    return secrets.token_urlsafe(24)


class TelegramLinkToken(UUIDPublicIdMixin, models.Model):
    """Одноразовый код для /start <token> в Telegram-боте."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link_tokens",
        verbose_name=_("Пользователь"),
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        default=_default_link_token,
        verbose_name=_("Токен"),
    )
    expires_at = models.DateTimeField(verbose_name=_("Истекает"))
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Токен привязки Telegram")
        verbose_name_plural = _("Токены привязки Telegram")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"tg-link:{self.user_id}"

    @property
    def is_valid(self) -> bool:
        if self.used_at:
            return False
        return self.expires_at > timezone.now()


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
