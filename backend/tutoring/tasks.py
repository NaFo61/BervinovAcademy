"""Напоминания о занятиях в Telegram."""

from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from tutoring.models import LessonReminder, TutoringLesson


def _reminder_text(lesson: TutoringLesson, offset_minutes: int) -> str:
    from tutoring.slots import mentor_timezone

    local = lesson.starts_at.astimezone(mentor_timezone(lesson.mentor))
    when = local.strftime("%d.%m %H:%M")
    mentor_name = (
        f"{lesson.mentor.first_name} {lesson.mentor.last_name}".strip()
    )
    if offset_minutes >= 24 * 60:
        head = "Завтра занятие"
    else:
        head = "Через час занятие"
    who = f" с {mentor_name}" if mentor_name else ""
    return f"{head}{who}: {when}."


@shared_task(name="tutoring.send_lesson_reminders")
def send_lesson_reminders() -> dict:
    from notify.telegram_api import send_message

    now = timezone.now()
    due = list(
        LessonReminder.objects.select_related(
            "lesson__student", "lesson__mentor"
        ).filter(status=LessonReminder.Status.PENDING, send_at__lte=now)[:50]
    )
    sent = 0
    skipped = 0
    for reminder in due:
        lesson = reminder.lesson
        if lesson.status != TutoringLesson.Status.BOOKED:
            reminder.status = LessonReminder.Status.CANCELLED
            reminder.save(update_fields=["status"])
            continue
        student = lesson.student
        chat_id = student.telegram_chat_id
        if not chat_id:
            reminder.status = LessonReminder.Status.SKIPPED
            reminder.save(update_fields=["status"])
            skipped += 1
            continue
        ok = send_message(
            chat_id,
            _reminder_text(lesson, reminder.offset_minutes),
        )
        if not ok:
            continue
        reminder.status = LessonReminder.Status.SENT
        reminder.save(update_fields=["status"])
        sent += 1
    return {"sent": sent, "skipped": skipped, "seen": len(due)}
