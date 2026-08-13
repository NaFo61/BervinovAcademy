"""Промокоды: ввод кода выдаёт тариф Про."""

from datetime import timedelta

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from subscriptions.models import Entitlement, PromoCode, PromoRedemption
from subscriptions.services import grant_pro, user_is_pro
from users.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="promo-student@example.com",
        phone="+79003330001",
        password="password",
        role="student",
        first_name="Ученик",
    )


@pytest.fixture
def client(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


@pytest.fixture
def promo(db):
    return PromoCode.objects.create(
        code="ege2026",
        duration_days=30,
        is_active=True,
    )


@pytest.mark.django_db
class TestRedeemPromo:
    def test_redeem_grants_pro(self, client, student, promo):
        assert user_is_pro(student) is False
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["ok"] is True
        assert resp.data["subscription"]["is_pro"] is True
        student.refresh_from_db()
        assert user_is_pro(student) is True
        assert PromoRedemption.objects.filter(
            promo=promo, user=student
        ).exists()
        ent = Entitlement.objects.get(user=student)
        assert ent.source == Entitlement.Source.PROMO

    def test_code_is_case_insensitive(self, client, promo):
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "  ege 2026 "},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_unknown_code(self, client):
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "NOPE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "нет" in str(resp.data).lower()

    def test_cannot_reuse(self, client, promo):
        first = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert first.status_code == status.HTTP_200_OK
        second = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert second.status_code == status.HTTP_400_BAD_REQUEST
        assert "уже" in str(second.data).lower()

    def test_expired(self, client, promo):
        promo.expires_at = timezone.now() - timedelta(hours=1)
        promo.save(update_fields=["expires_at"])
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_inactive(self, client, promo):
        promo.is_active = False
        promo.save(update_fields=["is_active"])
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_max_redemptions(self, client, student, promo, db):
        promo.max_redemptions = 1
        promo.save(update_fields=["max_redemptions"])
        other = User.objects.create_user(
            email="promo-other@example.com",
            phone="+79003330002",
            password="password",
            role="student",
        )
        grant_pro(
            user=other,
            source=Entitlement.Source.PROMO,
            note="promo:EGE2026",
        )
        PromoRedemption.objects.create(
            promo=promo,
            user=other,
            entitlement=Entitlement.objects.filter(user=other).first(),
        )
        resp = client.post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_anonymous_forbidden(self, promo):
        resp = APIClient().post(
            "/api/subscriptions/redeem/",
            {"code": "EGE2026"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
