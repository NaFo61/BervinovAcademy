"""Security: login/register/logout/refresh, JWT claims, throttles, PII."""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
import pytest
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users.serializers import inject_access_claims
from users.tests.conftest import make_user

STRONG_PASSWORD = "SecurePass1!"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


def _user(**kwargs):
    """make_user always sets password='password'; override when needed."""
    password = kwargs.pop("password", "password")
    user = make_user(**kwargs)
    if password != "password":
        user.set_password(password)
        user.save(update_fields=["password"])
    return user


def _auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    inject_access_claims(access, user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client, str(refresh), str(access)


@pytest.mark.django_db
class TestLoginAntiEnumeration:
    def test_unknown_user_same_message(self, api):
        resp = api.post(
            "/api/auth/login/",
            {"login": "nobody@academy.com", "password": STRONG_PASSWORD},
            format="json",
        )
        assert resp.status_code == 400
        body = str(resp.data)
        assert "Неверные учетные данные" in body
        assert "не найден" not in body.lower()
        assert "not found" not in body.lower()

    def test_wrong_password_same_message(self, api):
        _user(email="known@academy.com", phone="+79001112201")
        resp = api.post(
            "/api/auth/login/",
            {"login": "known@academy.com", "password": "WrongPass1!"},
            format="json",
        )
        assert resp.status_code == 400
        assert "Неверные учетные данные" in str(resp.data)

    def test_inactive_user_distinct_message(self, api):
        user = _user(
            email="inactive@academy.com",
            phone="+79001112202",
            password=STRONG_PASSWORD,
        )
        user.is_active = False
        user.save(update_fields=["is_active"])
        resp = api.post(
            "/api/auth/login/",
            {"login": "inactive@academy.com", "password": STRONG_PASSWORD},
            format="json",
        )
        assert resp.status_code == 400
        assert "неактивн" in str(resp.data).lower()

    def test_success_returns_jwt_with_public_id_claims(self, api):
        user = _user(
            email="ok@academy.com",
            phone="+79001112203",
            password=STRONG_PASSWORD,
            role="student",
        )
        resp = api.post(
            "/api/auth/login/",
            {"login": "ok@academy.com", "password": STRONG_PASSWORD},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data and "refresh" in resp.data
        access = AccessToken(resp.data["access"])
        assert str(access["user_id"]) == str(user.public_id)
        assert access["public_id"] == str(user.public_id)
        assert access["role"] == "student"
        assert access["email"] == "ok@academy.com"
        # Never put password / internal pk into JWT
        assert "password" not in access
        assert access.get("user_id") != user.pk


@pytest.mark.django_db
class TestRegisterSecurity:
    def test_register_issues_tokens_as_student(self, api):
        resp = api.post(
            "/api/auth/register/",
            {
                "login": "new@academy.com",
                "first_name": "New",
                "last_name": "Student",
                "password": STRONG_PASSWORD,
                "password_confirm": STRONG_PASSWORD,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert "access" in resp.data and "refresh" in resp.data
        access = AccessToken(resp.data["access"])
        assert access["role"] == "student"
        assert access["email"] == "new@academy.com"

    def test_duplicate_email_rejected(self, api):
        _user(email="dup@academy.com", phone="+79001112204")
        resp = api.post(
            "/api/auth/register/",
            {
                "login": "dup@academy.com",
                "first_name": "Dup",
                "last_name": "User",
                "password": STRONG_PASSWORD,
                "password_confirm": STRONG_PASSWORD,
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "уже существует" in str(resp.data).lower()

    def test_password_mismatch_rejected(self, api):
        resp = api.post(
            "/api/auth/register/",
            {
                "login": "mismatch@academy.com",
                "first_name": "A",
                "last_name": "B",
                "password": STRONG_PASSWORD,
                "password_confirm": "OtherPass1!",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_weak_password_rejected(self, api):
        resp = api.post(
            "/api/auth/register/",
            {
                "login": "weak@academy.com",
                "first_name": "A",
                "last_name": "B",
                "password": "123",
                "password_confirm": "123",
            },
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogoutAndRefresh:
    def test_logout_requires_auth(self, api):
        resp = api.post("/api/auth/logout/", {}, format="json")
        assert resp.status_code == 401

    def test_logout_blacklists_refresh(self, api):
        user = _user(
            email="logout@academy.com",
            phone="+79001112205",
            password=STRONG_PASSWORD,
        )
        client, refresh, _access = _auth_client(user)
        resp = client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
        )
        assert resp.status_code == 200

        again = api.post(
            "/api/auth/refresh/",
            {"refresh": refresh},
            format="json",
        )
        assert again.status_code == 401

    def test_logout_without_refresh_still_ok(self):
        user = _user(
            email="logout2@academy.com",
            phone="+79001112206",
            password=STRONG_PASSWORD,
        )
        client, _refresh, _access = _auth_client(user)
        resp = client.post("/api/auth/logout/", {}, format="json")
        assert resp.status_code == 200

    def test_logout_garbage_refresh_400(self):
        user = _user(
            email="logout3@academy.com",
            phone="+79001112207",
            password=STRONG_PASSWORD,
        )
        client, _refresh, _access = _auth_client(user)
        resp = client.post(
            "/api/auth/logout/",
            {"refresh": "not.a.valid.token"},
            format="json",
        )
        assert resp.status_code == 400
        assert "refresh" in str(resp.data).lower()

    def test_refresh_rotates_and_rejects_old(self, api):
        _user(
            email="refresh@academy.com",
            phone="+79001112208",
            password=STRONG_PASSWORD,
        )
        login = api.post(
            "/api/auth/login/",
            {"login": "refresh@academy.com", "password": STRONG_PASSWORD},
            format="json",
        )
        assert login.status_code == 200
        old_refresh = login.data["refresh"]

        first = api.post(
            "/api/auth/refresh/",
            {"refresh": old_refresh},
            format="json",
        )
        assert first.status_code == 200
        assert "access" in first.data
        new_refresh = first.data.get("refresh") or old_refresh

        # Old refresh must be blacklisted after rotation
        second = api.post(
            "/api/auth/refresh/",
            {"refresh": old_refresh},
            format="json",
        )
        assert second.status_code == 401

        # New refresh (if rotated) still works
        if new_refresh != old_refresh:
            third = api.post(
                "/api/auth/refresh/",
                {"refresh": new_refresh},
                format="json",
            )
            assert third.status_code == 200

    def test_refresh_invalid_401(self, api):
        resp = api.post(
            "/api/auth/refresh/",
            {"refresh": "totally-invalid"},
            format="json",
        )
        assert resp.status_code == 401

    def test_refresh_token_lives_about_six_months(self, api):
        _user(
            email="longlived@academy.com",
            phone="+79001112219",
            password=STRONG_PASSWORD,
        )
        login = api.post(
            "/api/auth/login/",
            {
                "login": "longlived@academy.com",
                "password": STRONG_PASSWORD,
            },
            format="json",
        )
        assert login.status_code == 200
        refresh = RefreshToken(login.data["refresh"])
        assert refresh["exp"] - refresh["iat"] >= int(
            timedelta(days=170).total_seconds()
        )


@pytest.mark.django_db
class TestPasswordResetProdShape:
    def test_request_hides_dev_code_when_debug_off(self, api, settings):
        settings.DEBUG = False
        _user(
            email="reset-prod@academy.com",
            phone="+79001112209",
            password=STRONG_PASSWORD,
        )
        existing = api.post(
            "/api/auth/password-reset/request/",
            {"login": "reset-prod@academy.com"},
            format="json",
        )
        missing = api.post(
            "/api/auth/password-reset/request/",
            {"login": "missing-prod@academy.com"},
            format="json",
        )
        assert existing.status_code == 200
        assert missing.status_code == 200
        assert "dev_code" not in existing.data
        assert "dev_code" not in missing.data
        assert existing.data.get("message") == missing.data.get("message")


@pytest.mark.django_db
class TestProfilePiiLeak:
    def test_public_profile_hides_email_phone(self, api):
        owner = _user(
            email="owner@academy.com",
            phone="+79001112210",
        )
        other = _user(
            email="viewer@academy.com",
            phone="+79001112211",
        )
        client, *_ = _auth_client(other)
        resp = client.get(f"/api/users/{owner.public_id}/")
        assert resp.status_code == 200
        assert "email" not in resp.data
        assert "phone" not in resp.data
        assert resp.data["public_id"] == str(owner.public_id)

    def test_me_requires_auth(self, api):
        resp = api.get("/api/users/me/")
        assert resp.status_code == 401

    def test_lookup_by_internal_pk_rejected(self, api):
        user = _user(
            email="pkleak@academy.com",
            phone="+79001112212",
        )
        resp = api.get(f"/api/users/{user.pk}/")
        # UUID regex → 404, never resolve internal id
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAuthThrottles:
    def _patch_scope_rate(self, monkeypatch, scope: str, rate: str):
        # DRF caches rates on the throttle class at import time.
        rates = dict(ScopedRateThrottle.THROTTLE_RATES or {})
        rates[scope] = rate
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", rates)
        cache.clear()

    def test_login_throttle_returns_429(self, api, monkeypatch):
        self._patch_scope_rate(monkeypatch, "login", "2/min")
        payload = {
            "login": "throttle@academy.com",
            "password": "x",
        }
        assert api.post("/api/auth/login/", payload, format="json").status_code
        assert api.post("/api/auth/login/", payload, format="json").status_code
        third = api.post("/api/auth/login/", payload, format="json")
        assert third.status_code == 429

    def test_password_reset_throttle_returns_429(self, api, monkeypatch):
        self._patch_scope_rate(monkeypatch, "password_reset", "2/min")
        payload = {"login": "throttle-reset@academy.com"}
        assert (
            api.post(
                "/api/auth/password-reset/request/", payload, format="json"
            ).status_code
            == 200
        )
        assert (
            api.post(
                "/api/auth/password-reset/request/", payload, format="json"
            ).status_code
            == 200
        )
        third = api.post(
            "/api/auth/password-reset/request/", payload, format="json"
        )
        assert third.status_code == 429
