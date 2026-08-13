"""Security: Web Push vapid/subscribe auth and ownership."""

from __future__ import annotations

from notify.models import PushSubscription
import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="push-a@academy.com",
        phone="+79002220001",
        password="password",
        role="student",
        first_name="Push",
        last_name="A",
    )


@pytest.fixture
def other(db):
    return User.objects.create_user(
        email="push-b@academy.com",
        phone="+79002220002",
        password="password",
        role="student",
        first_name="Push",
        last_name="B",
    )


@pytest.fixture
def vapid_on(settings):
    settings.VAPID_PUBLIC_KEY = "BPtestPublicKeyForUnitTestsOnly0123456789"
    # Fake material for is_configured(); not a real PEM key.
    settings.VAPID_PRIVATE_KEY = "test-vapid-private-material-not-a-real-key"


@pytest.mark.django_db
class TestWebPushAuth:
    def test_vapid_anonymous_401(self):
        client = APIClient()
        assert client.get("/api/push/vapid/").status_code == 401

    def test_subscribe_anonymous_401(self):
        client = APIClient()
        resp = client.post(
            "/api/push/subscribe/",
            {
                "endpoint": "https://push.example/x",
                "keys": {"p256dh": "a", "auth": "b"},
            },
            format="json",
        )
        assert resp.status_code == 401

    def test_vk_status_anonymous_401(self):
        client = APIClient()
        assert client.get("/api/vk/status/").status_code == 401

    def test_vapid_authenticated_no_private_key(self, student, vapid_on):
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get("/api/push/vapid/")
        assert resp.status_code == 200
        assert resp.data["configured"] is True
        assert resp.data["public_key"]
        body = str(resp.data).lower()
        assert "private" not in body
        assert "begin private" not in body


@pytest.mark.django_db
class TestWebPushSubscribe:
    def test_not_configured_503(self, student, settings):
        settings.VAPID_PUBLIC_KEY = ""
        settings.VAPID_PRIVATE_KEY = ""
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.post(
            "/api/push/subscribe/",
            {
                "endpoint": "https://push.example/a",
                "keys": {"p256dh": "p", "auth": "a"},
            },
            format="json",
        )
        assert resp.status_code == 503

    def test_missing_keys_400(self, student, vapid_on):
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.post(
            "/api/push/subscribe/",
            {"endpoint": "https://push.example/a", "keys": {}},
            format="json",
        )
        assert resp.status_code == 400

    def test_subscribe_owned_by_caller(self, student, vapid_on):
        client = APIClient()
        client.force_authenticate(user=student)
        endpoint = "https://push.example/owned"
        resp = client.post(
            "/api/push/subscribe/",
            {
                "endpoint": endpoint,
                "keys": {"p256dh": "p256", "auth": "authkey"},
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert resp.data["public_id"]
        sub = PushSubscription.objects.get(endpoint=endpoint)
        assert sub.user_id == student.pk
        assert sub.p256dh == "p256"

    def test_same_endpoint_reassigns_to_latest_user(
        self, student, other, vapid_on
    ):
        """Documents current contract: endpoint is unique, last writer wins."""
        endpoint = "https://push.example/shared"
        for user in (student, other):
            client = APIClient()
            client.force_authenticate(user=user)
            resp = client.post(
                "/api/push/subscribe/",
                {
                    "endpoint": endpoint,
                    "keys": {"p256dh": "p", "auth": "a"},
                },
                format="json",
            )
            assert resp.status_code == 200
        sub = PushSubscription.objects.get(endpoint=endpoint)
        assert sub.user_id == other.pk
        assert PushSubscription.objects.filter(endpoint=endpoint).count() == 1

    def test_delete_only_own_subscription(self, student, other, vapid_on):
        endpoint_a = "https://push.example/a"
        endpoint_b = "https://push.example/b"
        PushSubscription.objects.create(
            user=student,
            endpoint=endpoint_a,
            p256dh="p",
            auth="a",
        )
        PushSubscription.objects.create(
            user=other,
            endpoint=endpoint_b,
            p256dh="p",
            auth="a",
        )
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.delete(
            "/api/push/subscribe/",
            {"endpoint": endpoint_b},
            format="json",
        )
        assert resp.status_code == 200
        # Cannot delete another user's endpoint by posting their URL
        assert PushSubscription.objects.filter(endpoint=endpoint_b).exists()
        resp2 = client.delete(
            "/api/push/subscribe/",
            {"endpoint": endpoint_a},
            format="json",
        )
        assert resp2.status_code == 200
        assert not PushSubscription.objects.filter(
            endpoint=endpoint_a
        ).exists()
