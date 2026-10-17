"""Напоминания об учёбе и OAuth (вход через VK остаётся)."""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from model_bakery import baker
import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from communication.models import UserNotification
from education.models import Enrollment
from notify.study_reminders import send_abandoned_and_streak_reminders
from users.oauth import resolve_or_create_user, unlink_provider


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


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


@pytest.mark.django_db
def test_me_payload_has_oauth_and_telegram():
    user = baker.make(
        "users.User",
        role="student",
        email="me@ex.com",
        yandex_id="ya-me",
        vk_id=77,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/users/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["oauth"]["yandex"] is True
    assert data["oauth"]["vk"] is True
    assert "vk" not in data
    assert data["telegram"]["linked"] is False


@pytest.mark.django_db
def test_oauth_resolve_by_email_merge():
    existing = baker.make("users.User", role="student", email="merge@ex.com")
    user, created = resolve_or_create_user(
        {
            "provider": "yandex",
            "provider_user_id": "ya-99",
            "email": "merge@ex.com",
            "first_name": "A",
            "last_name": "B",
        }
    )
    assert not created
    assert user.pk == existing.pk
    existing.refresh_from_db()
    assert existing.yandex_id == "ya-99"


@pytest.mark.django_db
def test_oauth_create_vk_user():
    user, created = resolve_or_create_user(
        {
            "provider": "vk",
            "provider_user_id": "555",
            "email": None,
            "first_name": "Иван",
            "last_name": "VK",
        }
    )
    assert created
    assert user.vk_id == 555
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_oauth_unlink_last_method_forbidden():
    user = baker.make(
        "users.User",
        role="student",
        email=None,
        phone=None,
        yandex_id="only-ya",
        vk_id=None,
    )
    user.set_unusable_password()
    user.save()
    with pytest.raises(ValidationError):
        unlink_provider(user, "yandex")
