"""Привязка аккаунта к боту Telegram."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from model_bakery import baker
import pytest
from rest_framework.test import APIClient

from notify.models import TelegramLinkToken


@pytest.mark.django_db
def test_link_issues_start_url(settings):
    settings.TELEGRAM_BOT_TOKEN = "123:abc"
    settings.TELEGRAM_BOT_USERNAME = "@academy_bot"
    user = baker.make("users.User", role="student", email="tg@ex.com")
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post("/api/telegram/link/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bot_configured"] is True
    assert data["start_url"].startswith("https://t.me/academy_bot?start=")
    assert (
        TelegramLinkToken.objects.filter(user=user, used_at=None).count() == 1
    )


@pytest.mark.django_db
def test_webhook_start_links_user(settings):
    settings.TELEGRAM_WEBHOOK_SECRET = "hook-secret"
    user = baker.make("users.User", role="student", email="link@ex.com")
    token = TelegramLinkToken.objects.create(
        user=user,
        token="one-time-code",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    client = APIClient()
    resp = client.post(
        "/api/telegram/webhook/hook-secret/",
        {
            "update_id": 1,
            "message": {
                "text": "/start one-time-code",
                "from": {"id": 4242, "username": "pupil"},
                "chat": {"id": 4242, "type": "private"},
            },
        },
        format="json",
    )
    assert resp.status_code == 200
    user.refresh_from_db()
    token.refresh_from_db()
    assert user.telegram_id == 4242
    assert user.telegram_chat_id == 4242
    assert user.telegram_username == "pupil"
    assert user.telegram_linked_at is not None
    assert token.used_at is not None


@pytest.mark.django_db
def test_webhook_does_not_steal_foreign_telegram(settings):
    settings.TELEGRAM_WEBHOOK_SECRET = "hook-secret"
    owner = baker.make(
        "users.User",
        role="student",
        email="owner@ex.com",
        telegram_id=7,
    )
    other = baker.make("users.User", role="student", email="other@ex.com")
    TelegramLinkToken.objects.create(
        user=other,
        token="stolen",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    client = APIClient()
    resp = client.post(
        "/api/telegram/webhook/hook-secret/",
        {
            "update_id": 2,
            "message": {
                "text": "/start stolen",
                "from": {"id": 7, "username": "owner"},
                "chat": {"id": 7},
            },
        },
        format="json",
    )
    assert resp.status_code == 200
    other.refresh_from_db()
    owner.refresh_from_db()
    assert other.telegram_id is None
    assert owner.telegram_id == 7


@pytest.mark.django_db
def test_unlink_clears_telegram():
    user = baker.make(
        "users.User",
        role="student",
        email="bye@ex.com",
        telegram_id=9,
        telegram_chat_id=9,
        telegram_username="bye",
        telegram_linked_at=timezone.now(),
    )
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.delete("/api/telegram/link/")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.telegram_id is None
    assert user.telegram_username == ""
    assert user.telegram_linked_at is None
