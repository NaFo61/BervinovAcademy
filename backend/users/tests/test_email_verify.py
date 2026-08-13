from django.core import mail
from django.core.cache import cache
import pytest
from rest_framework.test import APIClient

from users.tests.conftest import make_user

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


def test_email_verify_requires_auth(api):
    resp = api.post("/api/auth/email-verify/request/", {}, format="json")
    assert resp.status_code in (401, 403)


def test_email_verify_without_email(api):
    user = make_user(email=None, phone="+79001112233")
    api.force_authenticate(user)
    resp = api.post("/api/auth/email-verify/request/", {}, format="json")
    assert resp.status_code == 400


def test_email_verify_happy_path(api, settings):
    settings.DEBUG = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    user = make_user(email="verify@academy.com")
    assert user.email_verified is False
    api.force_authenticate(user)

    req = api.post("/api/auth/email-verify/request/", {}, format="json")
    assert req.status_code == 200
    code = req.data.get("dev_code")
    assert code
    assert len(mail.outbox) == 1
    assert code in mail.outbox[0].body

    bad = api.post(
        "/api/auth/email-verify/confirm/",
        {"code": "000000"},
        format="json",
    )
    assert bad.status_code == 400

    ok = api.post(
        "/api/auth/email-verify/confirm/",
        {"code": code},
        format="json",
    )
    assert ok.status_code == 200
    assert ok.data["email_verified"] is True
    user.refresh_from_db()
    assert user.email_verified is True

    me = api.get("/api/users/me/")
    assert me.status_code == 200
    assert me.data["email_verified"] is True
    assert me.data["recovery"]["email_verified"] is True


def test_email_verify_already_verified(api, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    user = make_user(email="done@academy.com")
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    api.force_authenticate(user)
    resp = api.post("/api/auth/email-verify/request/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["email_verified"] is True
    assert len(mail.outbox) == 0


def test_password_reset_sends_email(api, settings):
    settings.DEBUG = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    make_user(email="reset2@academy.com")
    resp = api.post(
        "/api/auth/password-reset/request/",
        {"login": "reset2@academy.com"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data.get("dev_code")
    assert len(mail.outbox) == 1
    assert "Восстановление" in mail.outbox[0].subject
