"""Тесты привязки Telegram и напоминаний об учёбе."""

from datetime import timedelta

from django.utils import timezone
from model_bakery import baker
from notify.linking import consume_link_token, issue_link_token
from notify.study_reminders import send_abandoned_and_streak_reminders
import pytest

from communication.models import UserNotification
from education.models import Enrollment


@pytest.mark.django_db
def test_telegram_link_token_consume(settings):
    settings.TELEGRAM_BOT_TOKEN = "x"
    settings.TELEGRAM_BOT_USERNAME = "ba_bot"
    user = baker.make("users.User", role="student", email="a@ex.com")
    data = issue_link_token(user=user)
    linked = consume_link_token(
        token=data["token"],
        telegram_id=123456,
        telegram_username="dir",
    )
    assert linked is not None
    user.refresh_from_db()
    assert user.telegram_id == 123456
    assert user.telegram_username == "dir"
    # повторно нельзя
    assert consume_link_token(token=data["token"], telegram_id=999) is None


@pytest.mark.django_db
def test_study_reminder_for_stale_enrollment(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    user = baker.make("users.User", role="student", email="b@ex.com")
    course = baker.make("content.Course", title="Python")
    en = baker.make(
        Enrollment,
        user=user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )
    Enrollment.objects.filter(pk=en.pk).update(
        last_activity_at=timezone.now() - timedelta(days=5),
        last_study_reminder_at=None,
    )
    result = send_abandoned_and_streak_reminders()
    assert result["study"] >= 1
    assert UserNotification.objects.filter(
        user=user, kind=UserNotification.Kind.STUDY_REMINDER
    ).exists()
