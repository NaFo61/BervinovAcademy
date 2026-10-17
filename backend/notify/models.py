"""Модели Web Push и привязки Telegram."""

from __future__ import annotations

import secrets

from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def _default_link_token() -> str:
    """Одноразовый код для deep link /start в Telegram."""
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


class TelegramLinkToken(UUIDPublicIdMixin, models.Model):
    """Одноразовый код: ученик открывает бота и жмёт Start."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link_tokens",
        verbose_name=_("Пользователь"),
    )
    token = models.CharField(
        verbose_name=_("Токен"),
        max_length=64,
        unique=True,
        default=_default_link_token,
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
