"""Свободные слоты внутри окон ментора."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from tutoring.models import (
    AvailabilityWindow,
    LessonTariff,
    TutoringLesson,
    TutorSettings,
)

SLOT_STEP = timedelta(minutes=30)
BLOCKING = (
    TutoringLesson.Status.BOOKED,
    TutoringLesson.Status.DONE,
    TutoringLesson.Status.MISSED,
)


class SlotError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def mentor_timezone(mentor):
    row = TutorSettings.objects.filter(user=mentor).first()
    name = (row.timezone if row else "") or "Europe/Moscow"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Europe/Moscow")


def parse_day(value: str):
    text = (value or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SlotError("Дата в формате ГГГГ-ММ-ДД.") from exc


def _overlaps(lesson, start, end) -> bool:
    return lesson.starts_at < end and start < lesson.ends_at


def slots_for_day(*, mentor, day, duration_minutes: int) -> list[datetime]:
    tariff = LessonTariff.objects.filter(
        mentor=mentor, duration_minutes=duration_minutes
    ).first()
    if tariff is None:
        raise SlotError("Такой длительности у ментора нет.")
    if duration_minutes < 15 or duration_minutes > 360:
        raise SlotError("Длительность от 15 до 360 минут.")

    tz = mentor_timezone(mentor)
    duration = timedelta(minutes=duration_minutes)
    day_start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    busy = list(
        TutoringLesson.objects.filter(
            mentor=mentor,
            status__in=BLOCKING,
            starts_at__lt=day_end,
            ends_at__gt=day_start,
        )
    )
    now = timezone.now()
    found: list[datetime] = []
    windows = AvailabilityWindow.objects.filter(
        mentor=mentor, weekday=day.weekday()
    )
    for window in windows:
        cursor = datetime.combine(day, window.start_time, tzinfo=tz)
        limit = datetime.combine(day, window.end_time, tzinfo=tz)
        while cursor + duration <= limit:
            end = cursor + duration
            start_utc = cursor.astimezone(timezone.utc)
            end_utc = end.astimezone(timezone.utc)
            taken = any(_overlaps(item, start_utc, end_utc) for item in busy)
            if start_utc > now and not taken:
                found.append(start_utc)
            cursor += SLOT_STEP
    found.sort()
    return found


def is_open_slot(*, mentor, starts_at, duration_minutes: int) -> bool:
    tz = mentor_timezone(mentor)
    local = starts_at.astimezone(tz)
    day = local.date()
    try:
        options = slots_for_day(
            mentor=mentor, day=day, duration_minutes=duration_minutes
        )
    except SlotError:
        return False
    target = starts_at.astimezone(timezone.utc).replace(microsecond=0)
    for option in options:
        if option.astimezone(timezone.utc).replace(microsecond=0) == target:
            return True
    return False
