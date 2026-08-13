"""Тарифы и выдачи доступа (entitlements)."""

from __future__ import annotations

from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL

PLAN_CODE_PRO = "pro"

FEATURE_MENTOR_CHAT = "mentor_chat"
FEATURE_SOLUTION_VIDEO = "solution_video"
FEATURE_CONFERENCE = "conference"

PRO_FEATURES: tuple[str, ...] = (
    FEATURE_MENTOR_CHAT,
    FEATURE_SOLUTION_VIDEO,
    FEATURE_CONFERENCE,
)

DEFAULT_PRO_DURATION_DAYS = 30


class Plan(UUIDPublicIdMixin, models.Model):
    """Каталог тарифов. Сейчас один: Pro."""

    code = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name=_("Код"),
        help_text=_("Стабильный код, например pro"),
    )
    title = models.CharField(max_length=120, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    duration_days = models.PositiveIntegerField(
        default=DEFAULT_PRO_DURATION_DAYS,
        verbose_name=_("Срок (дней)"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    features = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Фичи"),
        help_text=_(
            "Список кодов фич: mentor_chat, solution_video, conference"
        ),
    )

    class Meta:
        verbose_name = _("Тариф")
        verbose_name_plural = _("Тарифы")
        ordering = ("code",)

    def __str__(self):
        return f"{self.title} ({self.code})"

    def feature_set(self) -> frozenset[str]:
        raw = self.features or []
        if not isinstance(raw, list):
            return frozenset()
        return frozenset(str(x) for x in raw)


class Entitlement(UUIDPublicIdMixin, models.Model):
    """Выдача тарифа пользователю (ручная или будущая покупка)."""

    class Source(models.TextChoices):
        ADMIN_GRANT = "admin_grant", _("Выдача админом")
        PURCHASE = "purchase", _("Покупка")
        PROMO = "promo", _("Промокод")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="entitlements",
        verbose_name=_("Пользователь"),
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="entitlements",
        verbose_name=_("Тариф"),
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.ADMIN_GRANT,
        verbose_name=_("Источник"),
    )
    starts_at = models.DateTimeField(
        default=timezone.now, verbose_name=_("Начало")
    )
    ends_at = models.DateTimeField(verbose_name=_("Окончание"))
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_entitlements",
        verbose_name=_("Кто выдал"),
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Отозвано"),
    )
    note = models.CharField(
        max_length=255, blank=True, verbose_name=_("Заметка")
    )
    expiry_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Напоминание об окончании отправлено"),
    )

    class Meta:
        verbose_name = _("Выдача тарифа")
        verbose_name_plural = _("Выдачи тарифов")
        ordering = ("-starts_at",)
        indexes = [
            models.Index(fields=["user", "-ends_at"]),
            models.Index(fields=["user", "revoked_at", "-ends_at"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.plan.code} до {self.ends_at:%Y-%m-%d}"

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        now = timezone.now()
        return self.starts_at <= now < self.ends_at


def _normalize_promo_code(raw: str) -> str:
    return "".join(str(raw or "").split()).upper()


class PromoCode(UUIDPublicIdMixin, models.Model):
    """Промокод: ученик вводит код — получает Про."""

    code = models.CharField(
        max_length=32,
        unique=True,
        verbose_name=_("Код"),
        help_text=_("Латиница и цифры, например EGE2026"),
    )
    duration_days = models.PositiveIntegerField(
        default=DEFAULT_PRO_DURATION_DAYS,
        verbose_name=_("Срок Про (дней)"),
    )
    max_redemptions = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Лимит использований"),
        help_text=_("Пусто — без лимита"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Действует до"),
    )
    note = models.CharField(
        max_length=255, blank=True, verbose_name=_("Заметка")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Создан")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_promo_codes",
        verbose_name=_("Кто создал"),
    )

    class Meta:
        verbose_name = _("Промокод")
        verbose_name_plural = _("Промокоды")
        ordering = ("-created_at",)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = _normalize_promo_code(self.code)
        super().save(*args, **kwargs)


class PromoRedemption(UUIDPublicIdMixin, models.Model):
    """Факт применения промокода."""

    promo = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name="redemptions",
        verbose_name=_("Промокод"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="promo_redemptions",
        verbose_name=_("Пользователь"),
    )
    entitlement = models.ForeignKey(
        Entitlement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promo_redemptions",
        verbose_name=_("Выдача"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Когда")
    )

    class Meta:
        verbose_name = _("Использование промокода")
        verbose_name_plural = _("Использования промокодов")
        ordering = ("-created_at",)
        unique_together = ("promo", "user")
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} ← {self.promo.code}"
