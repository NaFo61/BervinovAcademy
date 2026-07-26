"""Проверка и выдача тарифов."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    DEFAULT_PRO_DURATION_DAYS,
    FEATURE_CONFERENCE,
    FEATURE_MENTOR_CHAT,
    FEATURE_SOLUTION_VIDEO,
    PLAN_CODE_PRO,
    PRO_FEATURES,
    Entitlement,
    Plan,
)

__all__ = [
    "FEATURE_CONFERENCE",
    "FEATURE_MENTOR_CHAT",
    "FEATURE_SOLUTION_VIDEO",
    "PLAN_CODE_PRO",
    "PRO_FEATURES",
    "active_entitlement",
    "ensure_pro_plan",
    "grant_pro",
    "subscription_payload",
    "user_has_feature",
    "user_is_pro",
]


def ensure_pro_plan() -> Plan:
    plan, _created = Plan.objects.get_or_create(
        code=PLAN_CODE_PRO,
        defaults={
            "title": "Про",
            "description": (
                "Чат с ментором, видео-разборы эталонных решений и созвоны."
            ),
            "duration_days": DEFAULT_PRO_DURATION_DAYS,
            "is_active": True,
            "features": list(PRO_FEATURES),
        },
    )
    # Keep feature list in sync if plan already existed without features.
    if not plan.features:
        plan.features = list(PRO_FEATURES)
        plan.save(update_fields=["features"])
    return plan


def _staff_bypass(user) -> bool:
    if not user or getattr(user, "is_anonymous", True):
        return False
    return getattr(user, "role", None) in ("mentor", "admin")


def active_entitlement(user) -> Entitlement | None:
    if not user or getattr(user, "is_anonymous", True):
        return None
    now = timezone.now()
    return (
        Entitlement.objects.select_related("plan")
        .filter(
            user=user,
            revoked_at__isnull=True,
            starts_at__lte=now,
            ends_at__gt=now,
            plan__is_active=True,
        )
        .order_by("-ends_at")
        .first()
    )


def user_is_pro(user) -> bool:
    if _staff_bypass(user):
        return True
    ent = active_entitlement(user)
    return bool(ent and ent.plan.code == PLAN_CODE_PRO)


def user_has_feature(user, feature: str) -> bool:
    if _staff_bypass(user):
        return True
    ent = active_entitlement(user)
    if not ent:
        return False
    return feature in ent.plan.feature_set()


@transaction.atomic
def grant_pro(
    *,
    user,
    granted_by=None,
    duration_days: int | None = None,
    note: str = "",
    source: str = Entitlement.Source.ADMIN_GRANT,
) -> Entitlement:
    """Выдать/продлить Pro. Если активная выдача есть — продлеваем от ends_at."""
    plan = ensure_pro_plan()
    days = duration_days or plan.duration_days or DEFAULT_PRO_DURATION_DAYS
    now = timezone.now()
    current = active_entitlement(user)
    start = now
    if current and current.plan_id == plan.pk and current.ends_at > now:
        start = current.ends_at
    ends = start + timedelta(days=days)
    return Entitlement.objects.create(
        user=user,
        plan=plan,
        source=source,
        starts_at=now if not current else now,
        ends_at=ends,
        granted_by=granted_by,
        note=note or "",
    )


def subscription_payload(user) -> dict:
    """Для /api/users/me/ и тестов."""
    if not user or getattr(user, "is_anonymous", True):
        return {
            "is_pro": False,
            "plan": None,
            "features": [],
            "ends_at": None,
        }
    if _staff_bypass(user):
        return {
            "is_pro": True,
            "plan": PLAN_CODE_PRO,
            "features": list(PRO_FEATURES),
            "ends_at": None,
            "staff_bypass": True,
        }
    ent = active_entitlement(user)
    if not ent:
        return {
            "is_pro": False,
            "plan": None,
            "features": [],
            "ends_at": None,
        }
    return {
        "is_pro": ent.plan.code == PLAN_CODE_PRO,
        "plan": ent.plan.code,
        "features": sorted(ent.plan.feature_set()),
        "ends_at": ent.ends_at.isoformat(),
    }
