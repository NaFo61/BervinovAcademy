"""Напоминания о заброшенных курсах и риске сорвать streak."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone
from notify.dispatch import create_and_deliver, site_url

from communication.models import UserNotification
from education.models import Enrollment
from progress.stats import compute_streak_days

User = get_user_model()

ABANDONED_DAYS = 2
STREAK_WARN_IF_STREAK_GE = 2


def send_abandoned_and_streak_reminders() -> dict:
    now = timezone.now()
    abandoned_cutoff = now - timedelta(days=ABANDONED_DAYS)
    today = timezone.localdate()
    sent_study = 0
    sent_streak = 0

    # Заброшенные активные курсы (не чаще раза в 2 дня на enrollment)
    ens = (
        Enrollment.objects.filter(
            status=Enrollment.Status.ACTIVE,
            last_activity_at__lt=abandoned_cutoff,
        )
        .select_related("user", "course")
        .order_by("user_id", "-last_activity_at")
    )
    seen_users: set[int] = set()
    for e in ens:
        if e.user_id in seen_users:
            continue
        if (
            e.last_study_reminder_at
            and e.last_study_reminder_at > abandoned_cutoff
        ):
            continue
        seen_users.add(e.user_id)
        title = e.course.title if e.course_id else "курс"
        create_and_deliver(
            user=e.user,
            kind=UserNotification.Kind.STUDY_REMINDER,
            title="Пора вернуться к учёбе",
            body=(
                f"Курс «{title}» ждёт тебя уже "
                f"{ABANDONED_DAYS}+ дня. "
                "Небольшой урок сегодня — и streak в безопасности."
            ),
            url=site_url(
                f"/learn?course={e.course.public_id}"
                if getattr(e.course, "public_id", None)
                else "/catalog"
            ),
        )
        Enrollment.objects.filter(pk=e.pk).update(last_study_reminder_at=now)
        sent_study += 1

    # Streak под угрозой: был streak, сегодня ещё не было активности
    # (упрощённо: streak>=2 и max enrollment activity не сегодня)
    for user in User.objects.filter(is_active=True, role="student").iterator(
        chunk_size=200
    ):
        streak = compute_streak_days(user)
        if streak < STREAK_WARN_IF_STREAK_GE:
            continue
        last = Enrollment.objects.filter(user=user).aggregate(
            m=Max("last_activity_at")
        )["m"]
        if last and timezone.localdate(last) == today:
            continue
        # не спамим: одно streak-напоминание в сутки
        already = UserNotification.objects.filter(
            user=user,
            kind=UserNotification.Kind.STREAK_REMINDER,
            created_at__date=today,
        ).exists()
        if already:
            continue
        create_and_deliver(
            user=user,
            kind=UserNotification.Kind.STREAK_REMINDER,
            title=f"Streak {streak} под угрозой",
            body=(
                "Сегодня ещё не было активности. "
                "Пройди короткий урок — сохрани серию."
            ),
            url=site_url("/catalog"),
        )
        sent_streak += 1

    return {"study": sent_study, "streak": sent_streak}
