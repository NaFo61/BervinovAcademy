"""Запись, деньги, напоминания."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from tutoring.access import assigned_mentor, can_book, lessons_enabled
from tutoring.models import (
    AvailabilityWindow,
    LedgerEntry,
    LessonReminder,
    LessonTariff,
    PaymentClaim,
    TutoringLesson,
    TutorSettings,
)
from tutoring.slots import is_open_slot, mentor_timezone
from users.models import Student

User = get_user_model()

REMIND_BEFORE = (24 * 60, 60)
MAX_CLAIM_KOP = 100_000_000_00


class TutoringError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def person(user) -> dict:
    name = f"{user.first_name} {user.last_name}".strip()
    return {
        "public_id": str(user.public_id),
        "name": name or user.email or user.phone or "Ученик",
    }


def balance_kop(*, student, mentor) -> int:
    total = LedgerEntry.objects.filter(
        student=student, mentor=mentor
    ).aggregate(total=Sum("amount_kop"))["total"]
    return int(total or 0)


def lesson_payload(lesson: TutoringLesson) -> dict:
    return {
        "public_id": str(lesson.public_id),
        "starts_at": lesson.starts_at.isoformat(),
        "ends_at": lesson.ends_at.isoformat(),
        "duration_minutes": lesson.duration_minutes,
        "price_kop": lesson.price_kop,
        "status": lesson.status,
        "homework_status": lesson.homework_status,
        "learned_note": lesson.learned_note,
        "student": person(lesson.student),
        "mentor": person(lesson.mentor),
    }


def claim_payload(claim: PaymentClaim) -> dict:
    return {
        "public_id": str(claim.public_id),
        "amount_kop": claim.amount_kop,
        "status": claim.status,
        "created_at": claim.created_at.isoformat(),
        "student": person(claim.student),
    }


def parse_starts_at(value) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = parse_datetime(str(value or ""))
    if parsed is None:
        raise TutoringError("Нужны дата и время начала.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, ZoneInfo("Europe/Moscow"))
    return parsed


def _lock_mentor(mentor):
    row, _ = TutorSettings.objects.get_or_create(user=mentor)
    TutorSettings.objects.select_for_update().get(pk=row.pk)


def _require_booked(lesson: TutoringLesson) -> None:
    if lesson.status != TutoringLesson.Status.BOOKED:
        raise TutoringError("Занятие уже не в записи.", 409)


def schedule_reminders(lesson: TutoringLesson) -> None:
    LessonReminder.objects.filter(
        lesson=lesson, status=LessonReminder.Status.PENDING
    ).update(status=LessonReminder.Status.CANCELLED)
    now = timezone.now()
    for minutes in REMIND_BEFORE:
        send_at = lesson.starts_at - timedelta(minutes=minutes)
        if send_at <= now:
            continue
        LessonReminder.objects.update_or_create(
            lesson=lesson,
            offset_minutes=minutes,
            defaults={
                "send_at": send_at,
                "status": LessonReminder.Status.PENDING,
            },
        )


def cancel_pending_reminders(lesson: TutoringLesson) -> None:
    LessonReminder.objects.filter(
        lesson=lesson, status=LessonReminder.Status.PENDING
    ).update(status=LessonReminder.Status.CANCELLED)


def _lesson_for(user, public_id) -> TutoringLesson:
    try:
        lesson = TutoringLesson.objects.select_related(
            "student", "mentor"
        ).get(public_id=public_id)
    except TutoringLesson.DoesNotExist as exc:
        raise TutoringError("Занятие не найдено.", 404) from exc
    if user.role == "admin":
        return lesson
    if user.role == "mentor" and lesson.mentor_id == user.id:
        return lesson
    if lesson.student_id == user.id:
        return lesson
    raise TutoringError("Чужое занятие.", 403)


def book_lesson(
    *, student, starts_at, duration_minutes: int
) -> TutoringLesson:
    if not can_book(student):
        raise TutoringError("Запись на занятия закрыта.", 403)
    mentor = assigned_mentor(student)
    try:
        duration_minutes = int(duration_minutes)
    except (TypeError, ValueError) as exc:
        raise TutoringError("Нужна длительность.") from exc
    tariff = LessonTariff.objects.filter(
        mentor=mentor, duration_minutes=duration_minutes
    ).first()
    if tariff is None:
        raise TutoringError("Такой длительности у ментора нет.")
    starts_at = parse_starts_at(starts_at)
    ends_at = starts_at + timedelta(minutes=duration_minutes)
    with transaction.atomic():
        _lock_mentor(mentor)
        if not is_open_slot(
            mentor=mentor,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
        ):
            raise TutoringError("Это время уже занято или закрыто.", 409)
        try:
            lesson = TutoringLesson.objects.create(
                student=student,
                mentor=mentor,
                starts_at=starts_at,
                ends_at=ends_at,
                duration_minutes=duration_minutes,
                price_kop=tariff.price_kop,
                status=TutoringLesson.Status.BOOKED,
            )
        except IntegrityError as exc:
            raise TutoringError("Это время уже занято.", 409) from exc
        schedule_reminders(lesson)
    return lesson


def cancel_lesson(*, actor, public_id) -> TutoringLesson:
    with transaction.atomic():
        lesson = _lesson_for(actor, public_id)
        _require_booked(lesson)
        lesson.status = TutoringLesson.Status.CANCELLED
        lesson.save(update_fields=["status"])
        cancel_pending_reminders(lesson)
    return lesson


def move_lesson(*, actor, public_id, starts_at) -> TutoringLesson:
    starts_at = parse_starts_at(starts_at)
    with transaction.atomic():
        try:
            lesson = (
                TutoringLesson.objects.select_for_update()
                .select_related("student", "mentor")
                .get(public_id=public_id)
            )
        except TutoringLesson.DoesNotExist as exc:
            raise TutoringError("Занятие не найдено.", 404) from exc
        if actor.role != "admin" and lesson.mentor_id != actor.id:
            if lesson.student_id != actor.id:
                raise TutoringError("Чужое занятие.", 403)
            if not can_book(actor):
                raise TutoringError("Запись на занятия закрыта.", 403)
        _require_booked(lesson)
        _lock_mentor(lesson.mentor)
        ends_at = starts_at + timedelta(minutes=lesson.duration_minutes)
        lesson.starts_at = starts_at
        lesson.ends_at = ends_at
        if not is_open_slot(
            mentor=lesson.mentor,
            starts_at=starts_at,
            duration_minutes=lesson.duration_minutes,
        ):
            # Свой текущий слот is_open_slot считает занятым. Сдвигаем проверку:
            # временно прячем занятие из выборки, сохранив новые границы.
            lesson.status = TutoringLesson.Status.CANCELLED
            lesson.save(update_fields=["status", "starts_at", "ends_at"])
            open_now = is_open_slot(
                mentor=lesson.mentor,
                starts_at=starts_at,
                duration_minutes=lesson.duration_minutes,
            )
            if not open_now:
                raise TutoringError("Это время уже занято или закрыто.", 409)
        lesson.status = TutoringLesson.Status.BOOKED
        try:
            lesson.save(update_fields=["status", "starts_at", "ends_at"])
        except IntegrityError as exc:
            raise TutoringError("Это время уже занято.", 409) from exc
        schedule_reminders(lesson)
    return lesson


def mark_lesson(*, actor, public_id, status: str) -> TutoringLesson:
    if status not in (
        TutoringLesson.Status.DONE,
        TutoringLesson.Status.MISSED,
    ):
        raise TutoringError("Неизвестный статус.")
    with transaction.atomic():
        lesson = _lesson_for(actor, public_id)
        if actor.role == "student":
            raise TutoringError("Отметить занятие может ментор.", 403)
        _require_booked(lesson)
        lesson.status = status
        lesson.save(update_fields=["status"])
        cancel_pending_reminders(lesson)
        if status == TutoringLesson.Status.DONE:
            already = LedgerEntry.objects.filter(
                lesson=lesson, kind=LedgerEntry.Kind.CHARGE
            ).exists()
            if not already:
                LedgerEntry.objects.create(
                    student=lesson.student,
                    mentor=lesson.mentor,
                    lesson=lesson,
                    kind=LedgerEntry.Kind.CHARGE,
                    amount_kop=-lesson.price_kop,
                )
    return lesson


def save_lesson_journal(*, actor, public_id, homework_status, learned_note):
    if actor.role == "student":
        raise TutoringError("Домашку отмечает ментор.", 403)
    status = "" if homework_status is None else str(homework_status).strip()
    if status not in ("", "done", "not_done"):
        raise TutoringError("Домашка: сдано, не сдано или пусто.")
    note = "" if learned_note is None else str(learned_note).strip()
    if len(note) > 2000:
        raise TutoringError("Заметка длиннее 2000 символов.")
    with transaction.atomic():
        lesson = _lesson_for(actor, public_id)
        if actor.role not in ("mentor", "admin"):
            raise TutoringError("Домашку отмечает ментор.", 403)
        lesson.homework_status = status
        lesson.learned_note = note
        lesson.save(update_fields=["homework_status", "learned_note"])
    return lesson


def create_claim(*, student, amount_kop: int) -> PaymentClaim:
    mentor = assigned_mentor(student)
    if mentor is None:
        raise TutoringError("Ментор не назначен.", 403)
    try:
        amount_kop = int(amount_kop)
    except (TypeError, ValueError) as exc:
        raise TutoringError("Нужна сумма в копейках.") from exc
    if amount_kop <= 0 or amount_kop > MAX_CLAIM_KOP:
        raise TutoringError("Сумма должна быть больше нуля.")
    return PaymentClaim.objects.create(
        student=student,
        mentor=mentor,
        amount_kop=amount_kop,
        status=PaymentClaim.Status.PENDING,
    )


def confirm_claim(*, actor, public_id) -> PaymentClaim:
    with transaction.atomic():
        try:
            claim = (
                PaymentClaim.objects.select_for_update()
                .select_related("student", "mentor")
                .get(public_id=public_id)
            )
        except PaymentClaim.DoesNotExist as exc:
            raise TutoringError("Заявка не найдена.", 404) from exc
        if actor.role != "admin" and claim.mentor_id != actor.id:
            raise TutoringError("Чужая заявка.", 403)
        if claim.status != PaymentClaim.Status.PENDING:
            raise TutoringError("Заявка уже решена.", 409)
        claim.status = PaymentClaim.Status.CONFIRMED
        claim.decided_at = timezone.now()
        claim.save(update_fields=["status", "decided_at"])
        LedgerEntry.objects.create(
            student=claim.student,
            mentor=claim.mentor,
            kind=LedgerEntry.Kind.PAYMENT,
            amount_kop=claim.amount_kop,
        )
    return claim


def reject_claim(*, actor, public_id) -> PaymentClaim:
    with transaction.atomic():
        try:
            claim = PaymentClaim.objects.select_for_update().get(
                public_id=public_id
            )
        except PaymentClaim.DoesNotExist as exc:
            raise TutoringError("Заявка не найдена.", 404) from exc
        if actor.role != "admin" and claim.mentor_id != actor.id:
            raise TutoringError("Чужая заявка.", 403)
        if claim.status != PaymentClaim.Status.PENDING:
            raise TutoringError("Заявка уже решена.", 409)
        before = balance_kop(student=claim.student, mentor=claim.mentor)
        claim.status = PaymentClaim.Status.REJECTED
        claim.decided_at = timezone.now()
        claim.save(update_fields=["status", "decided_at"])
        after = balance_kop(student=claim.student, mentor=claim.mentor)
        if before != after:
            raise TutoringError("Баланс не должен меняться.")
    return claim


def visible_lessons(user):
    qs = TutoringLesson.objects.select_related("student", "mentor").exclude(
        status=TutoringLesson.Status.CANCELLED
    )
    if user.role == "admin":
        return qs.order_by("starts_at")
    if user.role == "mentor":
        return qs.filter(mentor=user).order_by("starts_at")
    return qs.filter(student=user).order_by("starts_at")


def pending_and_debtors(user) -> dict:
    if user.role == "student":
        claims = PaymentClaim.objects.filter(
            student=user, status=PaymentClaim.Status.PENDING
        ).select_related("student")
        return {
            "pending": [claim_payload(item) for item in claims],
            "debtors": [],
        }
    mentor_ids = None
    if user.role == "mentor":
        mentor_ids = [user.id]
    claims = PaymentClaim.objects.filter(
        status=PaymentClaim.Status.PENDING
    ).select_related("student")
    if mentor_ids is not None:
        claims = claims.filter(mentor_id__in=mentor_ids)
    totals = LedgerEntry.objects.values("student", "mentor").annotate(
        balance=Sum("amount_kop")
    )
    if mentor_ids is not None:
        totals = totals.filter(mentor_id__in=mentor_ids)
    debtors = []
    user_ids = [row["student"] for row in totals if (row["balance"] or 0) < 0]
    people = {item.id: item for item in User.objects.filter(id__in=user_ids)}
    for row in totals:
        balance = int(row["balance"] or 0)
        if balance >= 0:
            continue
        student = people.get(row["student"])
        if student is None:
            continue
        debtors.append({"student": person(student), "balance_kop": balance})
    return {
        "pending": [claim_payload(item) for item in claims],
        "debtors": debtors,
    }


def me_payload(user) -> dict:
    mentor = assigned_mentor(user) if user.role == "student" else None
    tariffs = []
    if mentor is not None:
        tariffs = [
            {
                "duration_minutes": item.duration_minutes,
                "price_kop": item.price_kop,
            }
            for item in LessonTariff.objects.filter(mentor=mentor).order_by(
                "duration_minutes"
            )
        ]
    reason = None
    if user.role == "student":
        if not lessons_enabled(user):
            reason = "no_access"
        elif mentor is None:
            reason = "no_mentor"
    return {
        "role": user.role,
        "lessons_enabled": lessons_enabled(user),
        "can_book": can_book(user),
        "reason": reason,
        "mentor": person(mentor) if mentor else None,
        "balance_kop": (
            balance_kop(student=user, mentor=mentor) if mentor else 0
        ),
        "telegram_linked": bool(user.telegram_id),
        "tariffs": tariffs,
    }


def _parse_time(value):
    text = str(value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise TutoringError("Время в формате ЧЧ:ММ.")


def _check_timezone(name: str) -> str:
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise TutoringError("Неизвестный часовой пояс.") from exc
    return name


def replace_availability(*, mentor, timezone_name: str, windows: list) -> dict:
    timezone_name = _check_timezone(
        (timezone_name or "Europe/Moscow").strip() or "Europe/Moscow"
    )
    parsed = []
    for raw in windows or []:
        weekday = int(raw.get("weekday"))
        if weekday < 0 or weekday > 6:
            raise TutoringError("День недели от 0 до 6.")
        start = _parse_time(raw.get("start") or raw.get("start_time"))
        end = _parse_time(raw.get("end") or raw.get("end_time"))
        if end <= start:
            raise TutoringError("Конец окна должен быть позже начала.")
        parsed.append((weekday, start, end))
    for index, (weekday, start, end) in enumerate(parsed):
        for other_day, other_start, other_end in parsed[index + 1 :]:
            if weekday != other_day:
                continue
            if start < other_end and other_start < end:
                raise TutoringError("Окна одного дня пересекаются.")
    with transaction.atomic():
        row, _ = TutorSettings.objects.get_or_create(user=mentor)
        row.timezone = timezone_name
        row.save(update_fields=["timezone"])
        AvailabilityWindow.objects.filter(mentor=mentor).delete()
        AvailabilityWindow.objects.bulk_create(
            [
                AvailabilityWindow(
                    mentor=mentor,
                    weekday=weekday,
                    start_time=start,
                    end_time=end,
                )
                for weekday, start, end in parsed
            ]
        )
    return availability_payload(mentor)


def availability_payload(mentor) -> dict:
    row = TutorSettings.objects.filter(user=mentor).first()
    windows = [
        {
            "weekday": item.weekday,
            "start": item.start_time.strftime("%H:%M"),
            "end": item.end_time.strftime("%H:%M"),
        }
        for item in AvailabilityWindow.objects.filter(mentor=mentor)
    ]
    return {
        "timezone": row.timezone if row else "Europe/Moscow",
        "windows": windows,
    }


def replace_tariffs(*, mentor, tariffs: list) -> list[dict]:
    parsed = []
    seen = set()
    for raw in tariffs or []:
        try:
            minutes = int(raw.get("duration_minutes"))
            price = int(raw.get("price_kop"))
        except (TypeError, ValueError) as exc:
            raise TutoringError("Нужны длительность и цена.") from exc
        if minutes < 15 or minutes > 360:
            raise TutoringError("Длительность от 15 до 360 минут.")
        if price <= 0:
            raise TutoringError("Цена должна быть больше нуля.")
        if minutes in seen:
            raise TutoringError("Длительность повторяется.")
        seen.add(minutes)
        parsed.append((minutes, price))
    with transaction.atomic():
        LessonTariff.objects.filter(mentor=mentor).delete()
        LessonTariff.objects.bulk_create(
            [
                LessonTariff(
                    mentor=mentor,
                    duration_minutes=minutes,
                    price_kop=price,
                )
                for minutes, price in parsed
            ]
        )
    return tariffs_payload(mentor)


def tariffs_payload(mentor) -> list[dict]:
    return [
        {
            "duration_minutes": item.duration_minutes,
            "price_kop": item.price_kop,
        }
        for item in LessonTariff.objects.filter(mentor=mentor).order_by(
            "duration_minutes"
        )
    ]


def month_stats(*, mentor, month: str) -> dict:
    tz = mentor_timezone(mentor)
    text = (month or "").strip()
    if not text:
        local_now = timezone.now().astimezone(tz)
        year, mon = local_now.year, local_now.month
    else:
        try:
            year_text, mon_text = text.split("-", 1)
            year, mon = int(year_text), int(mon_text)
            if mon < 1 or mon > 12:
                raise ValueError
        except ValueError as exc:
            raise TutoringError("Месяц в формате ГГГГ-ММ.") from exc
    start = datetime(year, mon, 1, tzinfo=tz)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=tz)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=tz)
    charged = LedgerEntry.objects.filter(
        mentor=mentor,
        kind=LedgerEntry.Kind.CHARGE,
        created_at__gte=start,
        created_at__lt=end,
    ).aggregate(total=Sum("amount_kop"))["total"]
    received = LedgerEntry.objects.filter(
        mentor=mentor,
        kind=LedgerEntry.Kind.PAYMENT,
        created_at__gte=start,
        created_at__lt=end,
    ).aggregate(total=Sum("amount_kop"))["total"]
    forecast = TutoringLesson.objects.filter(
        mentor=mentor,
        status=TutoringLesson.Status.BOOKED,
        starts_at__gte=timezone.now(),
    ).aggregate(total=Sum("price_kop"))["total"]
    return {
        "month": f"{year:04d}-{mon:02d}",
        "charged_kop": abs(int(charged or 0)),
        "received_kop": int(received or 0),
        "forecast_kop": int(forecast or 0),
    }


def grant_access(*, actor, student, enabled: bool, mentor=None) -> dict:
    if getattr(student, "role", None) != "student":
        raise TutoringError("Доступ выдаётся ученику.")
    from tutoring.models import LessonAccess

    with transaction.atomic():
        Student.objects.get_or_create(user=student)
        row, _ = LessonAccess.objects.get_or_create(user=student)
        row.enabled = bool(enabled)
        row.granted_by = actor
        row.save(update_fields=["enabled", "granted_by", "updated_at"])
        if mentor is not None:
            from rest_framework.exceptions import ValidationError

            from mentoring.assignment import assign_mentor_to_student

            try:
                assign_mentor_to_student(
                    student=student, mentor=mentor, actor=actor
                )
            except ValidationError as exc:
                detail = exc.detail
                if isinstance(detail, dict):
                    detail = " ".join(str(item) for item in detail.values())
                raise TutoringError(str(detail)) from exc
    return me_payload(student)


def resolve_mentor_actor(user, mentor_public_id: str | None):
    if user.role not in ("mentor", "admin"):
        raise TutoringError("Нет доступа.", 403)
    if user.role == "admin" and mentor_public_id:
        mentor = User.objects.filter(
            public_id=mentor_public_id,
            role__in=("mentor", "admin"),
            is_active=True,
        ).first()
        if mentor is None:
            raise TutoringError("Ментор не найден.", 404)
        return mentor
    return user


def find_student(*, email: str = "", public_id: str = ""):
    if public_id:
        student = User.objects.filter(public_id=public_id).first()
    else:
        student = User.objects.filter(
            email__iexact=(email or "").strip()
        ).first()
    if student is None:
        raise TutoringError("Ученик не найден.", 404)
    return student
