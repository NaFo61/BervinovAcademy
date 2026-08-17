"""Сводка по видеозвонкам для админки."""

from __future__ import annotations

from collections import OrderedDict
from datetime import timedelta

from django.utils import timezone

from .models import Conference

IN_PROGRESS_STATUSES = (
    Conference.Status.WAITING,
    Conference.Status.ACTIVE,
)


def normalize_stats_days(raw, default: int = 7) -> int:
    try:
        days = int(raw)
    except (TypeError, ValueError):
        return default
    if days in (7, 30):
        return days
    return default


def format_duration_label(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    if seconds == 0:
        return "0 мин"
    if seconds < 60:
        return "меньше минуты"
    hours, rem = divmod(seconds, 3600)
    minutes, _ = divmod(rem, 60)
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def _person_name(user) -> str:
    if user is None:
        return "—"
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email or "—"


def _duration_seconds(conference) -> int | None:
    if not conference.started_at or not conference.ended_at:
        return None
    delta = conference.ended_at - conference.started_at
    return max(0, int(delta.total_seconds()))


def empty_call_stats(days: int = 7) -> dict:
    days = normalize_stats_days(days)
    return {
        "days": days,
        "total": 0,
        "completed": 0,
        "in_progress": 0,
        "total_duration_seconds": 0,
        "total_duration_label": format_duration_label(0),
        "by_day": [],
        "recent": [],
    }


def build_call_stats(*, days: int = 7) -> dict:
    days = normalize_stats_days(days)
    now = timezone.now()
    since = now - timedelta(days=days)
    rows = list(
        Conference.objects.filter(created_at__gte=since)
        .select_related("mentor", "guest")
        .order_by("-created_at")
    )

    local_since = timezone.localtime(since).date()
    today = timezone.localdate()
    buckets: OrderedDict = OrderedDict()
    cursor = local_since
    while cursor <= today:
        buckets[cursor] = {
            "date": cursor.isoformat(),
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "duration_seconds": 0,
            "duration_label": format_duration_label(0),
        }
        cursor += timedelta(days=1)

    completed = 0
    in_progress = 0
    duration_total = 0
    for conf in rows:
        if conf.status == Conference.Status.COMPLETED:
            completed += 1
        elif conf.status in IN_PROGRESS_STATUSES:
            in_progress += 1
        local_d = timezone.localtime(conf.created_at).date()
        bucket = buckets.get(local_d)
        if bucket is not None:
            bucket["total"] += 1
            if conf.status == Conference.Status.COMPLETED:
                bucket["completed"] += 1
            elif conf.status in IN_PROGRESS_STATUSES:
                bucket["in_progress"] += 1
        sec = _duration_seconds(conf)
        if sec is not None and conf.status == Conference.Status.COMPLETED:
            duration_total += sec
            if bucket is not None:
                bucket["duration_seconds"] += sec
                bucket["duration_label"] = format_duration_label(
                    bucket["duration_seconds"]
                )

    recent = []
    for conf in rows[:10]:
        sec = _duration_seconds(conf)
        if conf.status != Conference.Status.COMPLETED:
            sec = None
        recent.append(
            {
                "public_id": str(conf.public_id),
                "mentor_name": _person_name(conf.mentor),
                "guest_name": _person_name(conf.guest),
                "status": conf.status,
                "created_at": conf.created_at.isoformat(),
                "duration_seconds": sec,
                "duration_label": (
                    format_duration_label(sec) if sec is not None else "—"
                ),
            }
        )

    by_day = list(reversed(list(buckets.values())))
    return {
        "days": days,
        "total": len(rows),
        "completed": completed,
        "in_progress": in_progress,
        "total_duration_seconds": duration_total,
        "total_duration_label": format_duration_label(duration_total),
        "by_day": by_day,
        "recent": recent,
    }
