"""Tests for Pro showcase API and expiry reminders."""

from datetime import datetime, time, timedelta

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from communication.models import UserNotification
from subscriptions.models import Entitlement
from subscriptions.reminders import send_expiry_reminders
from subscriptions.services import ensure_pro_plan, grant_pro
from users.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="pro-page@example.com",
        phone="+79003330001",
        password="password",
        role="student",
        first_name="Ученик",
    )


def _ends_at_in_days(days: int):
    target_date = timezone.localdate() + timedelta(days=days)
    naive = datetime.combine(target_date, time(18, 0))
    if timezone.is_aware(timezone.now()):
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return naive


@pytest.mark.django_db
class TestProPlanApi:
    def test_public_plan_payload(self):
        ensure_pro_plan()
        client = APIClient()
        resp = client.get("/api/subscriptions/plans/pro/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["code"] == "pro"
        assert resp.data["duration_days"] == 30
        assert resp.data["purchase_available"] is False
        codes = {f["code"] for f in resp.data["features"]}
        assert "mentor_chat" in codes
        assert "solution_video" in codes
        assert "conference" in codes
        assert resp.data["subscription"] is None

    def test_authenticated_includes_subscription(self, student):
        grant_pro(user=student)
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get("/api/subscriptions/plans/pro/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["subscription"]["is_pro"] is True
        assert resp.data["subscription"]["ends_at"]

    def test_me_subscription_endpoint(self, student):
        client = APIClient()
        client.force_authenticate(user=student)
        before = client.get("/api/subscriptions/me/")
        assert before.data["is_pro"] is False
        grant_pro(user=student)
        after = client.get("/api/subscriptions/me/")
        assert after.data["is_pro"] is True


@pytest.mark.django_db
class TestExpiryReminders:
    def test_sends_once_three_days_before(self, student):
        plan = ensure_pro_plan()
        now = timezone.now()
        ent = Entitlement.objects.create(
            user=student,
            plan=plan,
            starts_at=now - timedelta(days=27),
            ends_at=_ends_at_in_days(3),
        )
        sent = send_expiry_reminders(days=3)
        assert sent == 1
        ent.refresh_from_db()
        assert ent.expiry_reminder_sent_at is not None
        notes = UserNotification.objects.filter(
            user=student,
            kind=UserNotification.Kind.SUBSCRIPTION_EXPIRING,
        )
        assert notes.count() == 1
        assert "Про" in notes.get().title

        assert send_expiry_reminders(days=3) == 0
        assert notes.count() == 1

    def test_skips_when_not_in_window(self, student):
        plan = ensure_pro_plan()
        now = timezone.now()
        Entitlement.objects.create(
            user=student,
            plan=plan,
            starts_at=now,
            ends_at=_ends_at_in_days(10),
        )
        assert send_expiry_reminders(days=3) == 0
        assert UserNotification.objects.count() == 0
