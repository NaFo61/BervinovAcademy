"""Мост к pivovarov-ice: статус, привязка, статистика (без живой БД ICE)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
import pytest
from rest_framework.test import APIClient

from tutoring.models import TutoringIceLink

User = get_user_model()


def _user(email, role="mentor", **extra):
    return User.objects.create_user(
        email=email,
        password="password",
        role=role,
        first_name=extra.pop("first_name", "Мирон"),
        **extra,
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_ice_status_disabled_without_dsn(settings):
    settings.ICE_DATABASE_URL = ""
    mentor = _user("ice-off@example.com")
    resp = _client(mentor).get("/api/tutoring/ice/status/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ice_enabled"] is False
    assert body["ice_linked"] is False


@pytest.mark.django_db
def test_ice_status_needs_telegram(settings):
    settings.ICE_DATABASE_URL = "postgresql://ice:ice@localhost:5432/ice"
    settings.ICE_BOT_USERNAME = "pivovarovicebot"
    mentor = _user("ice-tg@example.com")
    resp = _client(mentor).get("/api/tutoring/ice/status/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ice_enabled"] is True
    assert body["telegram_linked"] is False
    assert "Telegram" in body["hint"]


@pytest.mark.django_db
def test_ice_link_by_tutor_id(settings):
    settings.ICE_DATABASE_URL = "postgresql://ice:ice@localhost:5432/ice"
    mentor = _user("ice-link@example.com", role="admin", phone="+79001110001")
    tutor_row = {
        "id": 3,
        "display_name": "Мирон Бервинов",
        "status": "active",
        "user_id": 9,
        "timezone": "Europe/Moscow",
        "tg_id": 123456,
    }
    with patch("tutoring.ice.link._fetch_tutor", return_value=tutor_row):
        resp = _client(mentor).post(
            "/api/tutoring/ice/link/",
            {"ice_tutor_id": 3},
            format="json",
        )
    assert resp.status_code == 200, resp.content
    link = TutoringIceLink.objects.get(user=mentor)
    assert link.ice_tutor_id == 3
    assert link.display_name == "Мирон Бервинов"


@pytest.mark.django_db
def test_stats_uses_ice_when_linked(settings):
    settings.ICE_DATABASE_URL = "postgresql://ice:ice@localhost:5432/ice"
    mentor = _user("ice-stats@example.com", role="admin", phone="+79001110002")
    TutoringIceLink.objects.create(
        user=mentor, ice_tutor_id=3, display_name="Мирон"
    )
    fake = {
        "source": "ice",
        "from": "2026-11-01",
        "to": "2026-11-30",
        "group": "week",
        "month": "2026-11",
        "charged_kop": 1000,
        "received_kop": 2000,
        "forecast_kop": 500,
        "completed_count": 1,
        "cancelled_count": 0,
        "no_show_count": 0,
        "buckets": [
            {
                "period_start": "2026-11-03",
                "charged_kop": 1000,
                "received_kop": 2000,
                "forecast_kop": 500,
            }
        ],
        "by_student": [],
        "debtors": [],
    }
    with patch("tutoring.views.ice_period_stats", return_value=fake) as mocked:
        resp = _client(mentor).get(
            "/api/tutoring/stats/",
            {"from": "2026-11-01", "to": "2026-11-30", "group": "week"},
        )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["source"] == "ice"
    assert body["received_kop"] == 2000
    assert len(body["buckets"]) == 1
    mocked.assert_called_once()
    assert mocked.call_args.kwargs["tutor_id"] == 3


@pytest.mark.django_db
def test_local_stats_fallback_without_ice(settings):
    settings.ICE_DATABASE_URL = ""
    mentor = _user("local-stats@example.com", role="mentor")
    resp = _client(mentor).get("/api/tutoring/stats/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "local"
    assert "charged_kop" in body


def test_bucket_starts_week():
    from tutoring.ice.stats import _bucket_starts

    starts = _bucket_starts(date(2026, 11, 10), date(2026, 11, 20), "week")
    assert starts[0] == date(2026, 11, 9)  # monday
    assert date(2026, 11, 16) in starts


@pytest.mark.django_db
def test_ice_link_blocks_student(settings):
    settings.ICE_DATABASE_URL = "postgresql://ice:ice@localhost:5432/ice"
    student = _user("ice-student@example.com", role="student")
    resp = _client(student).post("/api/tutoring/ice/link/", {}, format="json")
    assert resp.status_code == 403
