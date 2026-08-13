"""Security: LiveKit webhook must verify signature; no open relay."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def livekit_on(settings):
    settings.LIVEKIT_API_KEY = "testkey"
    settings.LIVEKIT_API_SECRET = "testsecret"


@pytest.mark.django_db
class TestLiveKitWebhookSecurity:
    def test_unconfigured_503(self, settings):
        settings.LIVEKIT_API_KEY = ""
        settings.LIVEKIT_API_SECRET = ""
        client = APIClient()
        resp = client.post(
            "/api/communication/livekit/webhook/",
            {"event": "room_finished"},
            format="json",
        )
        assert resp.status_code == 503

    def test_missing_authorization_401(self, livekit_on):
        client = APIClient()
        resp = client.post(
            "/api/communication/livekit/webhook/",
            {"event": "room_finished"},
            format="json",
        )
        assert resp.status_code == 401
        assert "подпис" in str(resp.data).lower()

    def test_invalid_bearer_400(self, livekit_on):
        client = APIClient()
        resp = client.post(
            "/api/communication/livekit/webhook/",
            {"event": "room_finished"},
            format="json",
            HTTP_AUTHORIZATION="Bearer not-a-real-livekit-jwt",
        )
        assert resp.status_code == 400
        assert "некорректн" in str(resp.data).lower()

    def test_valid_mocked_receiver_ok(self, livekit_on):
        fake_event = SimpleNamespace(event="room_finished")
        fake_conference = SimpleNamespace(
            public_id="11111111-1111-1111-1111-111111111111"
        )

        with (
            patch("livekit.api.WebhookReceiver") as receiver_cls,
            patch(
                "communication.viewsets.services.apply_livekit_webhook_event",
                return_value=fake_conference,
            ) as apply_mock,
        ):
            receiver = MagicMock()
            receiver.receive.return_value = fake_event
            receiver_cls.return_value = receiver

            client = APIClient()
            resp = client.post(
                "/api/communication/livekit/webhook/",
                {"event": "room_finished"},
                format="json",
                HTTP_AUTHORIZATION="Bearer mocked-token",
            )

        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert resp.data["event"] == "room_finished"
        assert resp.data["conference"] == str(fake_conference.public_id)
        apply_mock.assert_called_once_with(fake_event)
        receiver.receive.assert_called_once()
