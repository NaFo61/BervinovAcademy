from datetime import timedelta
import uuid

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from communication.models import Conference
from users.models import User


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin-calls@academy.com",
        phone="+79001110009",
        password="password",
        first_name="Админ",
        last_name="Звонки",
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


def _make_conference(*, mentor, guest, status, **extra):
    conf = Conference.objects.create(
        mentor=mentor,
        guest=guest,
        room_name=f"conf-{uuid.uuid4()}",
        status=status,
    )
    if extra:
        Conference.objects.filter(pk=conf.pk).update(**extra)
        conf.refresh_from_db()
    return conf


@pytest.mark.django_db
class TestAdminCallStatsApi:
    def test_student_forbidden(self, student_client):
        resp = student_client.get("/api/communication/admin/call-stats/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_mentor_forbidden(self, mentor_client):
        resp = mentor_client.get("/api/communication/admin/call-stats/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_numbers_match_fixtures(
        self, admin_client, mentor_user, student_user
    ):
        now = timezone.now()
        _make_conference(
            mentor=mentor_user,
            guest=student_user,
            status=Conference.Status.COMPLETED,
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(hours=1),
        )
        _make_conference(
            mentor=mentor_user,
            guest=student_user,
            status=Conference.Status.ACTIVE,
            started_at=now - timedelta(minutes=10),
        )
        _make_conference(
            mentor=mentor_user,
            guest=student_user,
            status=Conference.Status.WAITING,
        )
        old = _make_conference(
            mentor=mentor_user,
            guest=student_user,
            status=Conference.Status.COMPLETED,
            started_at=now - timedelta(days=20, hours=1),
            ended_at=now - timedelta(days=20),
        )
        Conference.objects.filter(pk=old.pk).update(
            created_at=now - timedelta(days=20)
        )

        resp = admin_client.get("/api/communication/admin/call-stats/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["days"] == 7
        assert resp.data["total"] == 3
        assert resp.data["completed"] == 1
        assert resp.data["in_progress"] == 2
        assert resp.data["total_duration_seconds"] == 3600
        assert resp.data["total_duration_label"] == "1 ч 0 мин"
        assert len(resp.data["recent"]) == 3
        today = timezone.localdate().isoformat()
        today_row = next(
            row for row in resp.data["by_day"] if row["date"] == today
        )
        assert today_row["total"] == 3
        assert today_row["completed"] == 1
        assert today_row["in_progress"] == 2
        assert today_row["duration_seconds"] == 3600

        resp30 = admin_client.get(
            "/api/communication/admin/call-stats/?days=30"
        )
        assert resp30.status_code == status.HTTP_200_OK
        assert resp30.data["days"] == 30
        assert resp30.data["total"] == 4
        assert resp30.data["completed"] == 2
        assert resp30.data["total_duration_seconds"] == 7200
