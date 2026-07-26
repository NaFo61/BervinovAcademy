"""Напоминания об окончании тарифа."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.formats import date_format

from communication.models import UserNotification

from .models import PLAN_CODE_PRO, Entitlement

EXPIRY_REMINDER_DAYS = 3


def _format_ends_at(dt) -> str:
    local = timezone.localtime(dt)
    return date_format(local, "j E Y", use_l10n=True)


@transaction.atomic
def send_expiry_reminders(*, days: int = EXPIRY_REMINDER_DAYS) -> int:
    """Создать in-app уведомления для Про, которые кончаются через `days` дней.

    Идемпотентно: повторно не шлём, пока expiry_reminder_sent_at пуст.
    """
    today = timezone.localdate()
    target = today + timedelta(days=days)
    now = timezone.now()

    qs = Entitlement.objects.select_related("user", "plan").filter(
        revoked_at__isnull=True,
        expiry_reminder_sent_at__isnull=True,
        ends_at__date=target,
        ends_at__gt=now,
        plan__code=PLAN_CODE_PRO,
        plan__is_active=True,
    )

    sent = 0
    for ent in qs:
        ends_label = _format_ends_at(ent.ends_at)
        from notify.dispatch import create_and_deliver, site_url

        create_and_deliver(
            user=ent.user,
            kind=UserNotification.Kind.SUBSCRIPTION_EXPIRING,
            title="Тариф Про скоро закончится",
            body=(
                f"Ваш тариф Про действует до {ends_label}. "
                "Напишите администратору, чтобы продлить доступ "
                "к чату с ментором, видео-разборам и созвонам."
            ),
            url=site_url("/pro"),
        )
        ent.expiry_reminder_sent_at = now
        ent.save(update_fields=["expiry_reminder_sent_at"])
        sent += 1
    return sent
