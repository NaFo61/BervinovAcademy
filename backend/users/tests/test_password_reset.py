from django.core.cache import cache
import pytest
from rest_framework.test import APIClient

from users.tests.conftest import make_user


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


def test_request_code_always_returns_generic_message(client):
    resp = client.post(
        "/api/auth/password-reset/request/",
        {"login": "missing@academy.com"},
        format="json",
    )
    assert resp.status_code == 200
    assert "отправили" in resp.data["message"].lower()


def test_confirm_resets_password(client, settings):
    settings.DEBUG = True
    user = make_user(email="reset@academy.com")
    req = client.post(
        "/api/auth/password-reset/request/",
        {"login": "reset@academy.com"},
        format="json",
    )
    assert req.status_code == 200
    code = req.data.get("dev_code")
    assert code

    bad = client.post(
        "/api/auth/password-reset/confirm/",
        {
            "login": "reset@academy.com",
            "code": "000000",
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/auth/password-reset/confirm/",
        {
            "login": "reset@academy.com",
            "code": code,
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert ok.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPass1!")

    login = client.post(
        "/api/auth/login/",
        {"login": "reset@academy.com", "password": "NewPass1!"},
        format="json",
    )
    assert login.status_code == 200
