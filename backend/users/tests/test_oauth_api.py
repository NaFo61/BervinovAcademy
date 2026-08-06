"""API и логика OAuth (Яндекс / VK) — HTTP моки, без реальных провайдеров."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from model_bakery import baker
import pytest
from rest_framework.test import APIClient

from users.models import User
from users.oauth import (
    OAuthConflict,
    build_authorize_url,
    exchange_code,
    link_provider_to_user,
    resolve_or_create_user,
    unlink_provider,
)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def oauth_settings(settings):
    settings.FRONTEND_URL = "https://academy.test"
    settings.YANDEX_OAUTH_CLIENT_ID = "ya-client"
    settings.YANDEX_OAUTH_CLIENT_SECRET = "ya-secret"
    settings.VK_OAUTH_CLIENT_ID = "vk-client"
    settings.VK_OAUTH_CLIENT_SECRET = "vk-secret"
    return settings


@pytest.mark.django_db
def test_oauth_start_yandex(api, oauth_settings):
    resp = api.get("/api/auth/oauth/yandex/start/")
    assert resp.status_code == 200
    data = resp.json()
    assert "oauth.yandex.ru" in data["authorize_url"]
    assert data["provider"] == "yandex"
    assert data["state"].startswith("ba_yandex_")
    assert data["redirect_uri"].endswith("/auth-callback")


@pytest.mark.django_db
def test_oauth_start_vk(api, oauth_settings):
    resp = api.get("/api/auth/oauth/vk/start/")
    assert resp.status_code == 200
    data = resp.json()
    assert "oauth.vk.com" in data["authorize_url"]
    assert "client_id=vk-client" in data["authorize_url"]
    assert data["provider"] == "vk"


@pytest.mark.django_db
def test_oauth_start_not_configured(api, settings):
    settings.YANDEX_OAUTH_CLIENT_ID = ""
    settings.YANDEX_OAUTH_CLIENT_SECRET = ""
    resp = api.get("/api/auth/oauth/yandex/start/")
    assert resp.status_code == 503


@pytest.mark.django_db
def test_oauth_start_unknown_provider(api, oauth_settings):
    resp = api.get("/api/auth/oauth/google/start/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_build_authorize_url_custom_redirect(oauth_settings):
    data = build_authorize_url(
        provider="yandex",
        redirect_uri="http://localhost:3000/auth-callback",
    )
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth-callback" in (
        data["authorize_url"]
    )


@pytest.mark.django_db
@patch("users.oauth.requests.post")
@patch("users.oauth.requests.get")
def test_oauth_exchange_yandex_creates_user(
    mock_get, mock_post, api, oauth_settings
):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "ya-tok"},
        raise_for_status=lambda: None,
    )
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "id": "777",
            "default_email": "new@yandex.ru",
            "first_name": "Ян",
            "last_name": "Декс",
        },
        raise_for_status=lambda: None,
    )
    resp = api.post(
        "/api/auth/oauth/yandex/",
        {
            "code": "auth-code",
            "redirect_uri": "https://academy.test/auth-callback",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.json()
    assert "refresh" in resp.json()
    u = User.objects.get(yandex_id="777")
    assert u.email == "new@yandex.ru"
    assert not u.has_usable_password()


@pytest.mark.django_db
@patch("users.oauth.requests.get")
def test_oauth_exchange_vk_login_existing(mock_get, api, oauth_settings):
    existing = baker.make(
        "users.User",
        role="student",
        email="vkuser@ex.com",
        vk_id=4242,
    )
    existing.set_password("password123")
    existing.save()

    def fake_get(url, **kwargs):
        m = MagicMock()
        m.raise_for_status = lambda: None
        if "access_token" in str(url):
            m.json = lambda: {
                "access_token": "vk-tok",
                "user_id": 4242,
                "email": "vkuser@ex.com",
            }
        else:
            m.json = lambda: {
                "response": [
                    {"id": 4242, "first_name": "Вк", "last_name": "Юзер"}
                ]
            }
        return m

    mock_get.side_effect = fake_get
    resp = api.post(
        "/api/auth/oauth/vk/",
        {
            "code": "code",
            "redirect_uri": "https://academy.test/auth-callback",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert User.objects.filter(vk_id=4242).count() == 1


@pytest.mark.django_db
def test_oauth_link_requires_auth(api, oauth_settings):
    resp = api.post(
        "/api/auth/oauth/yandex/link/",
        {"code": "x"},
        format="json",
    )
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
@patch("users.viewsets.exchange_code")
def test_oauth_link_and_unlink(mock_ex, api, oauth_settings):
    user = baker.make(
        "users.User",
        role="student",
        email="link@ex.com",
        phone="+79990001122",
    )
    user.set_password("password12345")
    user.save()

    login = api.post(
        "/api/auth/login/",
        {"login": "link@ex.com", "password": "password12345"},
        format="json",
    )
    assert login.status_code == 200, login.content
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    mock_ex.return_value = {
        "provider": "yandex",
        "provider_user_id": "ya-link-1",
        "email": "link@ex.com",
        "first_name": "L",
        "last_name": "Ink",
    }
    resp = api.post(
        "/api/auth/oauth/yandex/link/",
        {
            "code": "c",
            "redirect_uri": "https://academy.test/auth-callback",
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    user.refresh_from_db()
    assert user.yandex_id == "ya-link-1"

    resp = api.post("/api/auth/oauth/yandex/unlink/", format="json")
    assert resp.status_code == 200, resp.content
    user.refresh_from_db()
    assert user.yandex_id is None


@pytest.mark.django_db
def test_oauth_unlink_keeps_vk_when_yandex_removed():
    user = baker.make(
        "users.User",
        role="student",
        email=None,
        phone=None,
        yandex_id="ya-a",
        vk_id=99,
        vk_messages_allowed=True,
    )
    user.set_unusable_password()
    user.save()
    unlink_provider(user, "yandex")
    user.refresh_from_db()
    assert user.yandex_id is None
    assert user.vk_id == 99


@pytest.mark.django_db
def test_link_provider_conflict():
    baker.make(
        "users.User", role="student", email="a@ex.com", yandex_id="taken"
    )
    other = baker.make("users.User", role="student", email="b@ex.com")
    with pytest.raises(OAuthConflict):
        link_provider_to_user(
            other,
            {
                "provider": "yandex",
                "provider_user_id": "taken",
                "email": None,
                "first_name": "X",
                "last_name": "Y",
            },
        )


@pytest.mark.django_db
def test_resolve_login_by_social_id():
    existing = baker.make(
        "users.User",
        role="student",
        email="s@ex.com",
        yandex_id="ya-exist",
    )
    user, created = resolve_or_create_user(
        {
            "provider": "yandex",
            "provider_user_id": "ya-exist",
            "email": "other@ex.com",
            "first_name": "A",
            "last_name": "B",
        }
    )
    assert not created
    assert user.pk == existing.pk


@pytest.mark.django_db
@patch("users.oauth.requests.post")
@patch("users.oauth.requests.get")
def test_exchange_yandex_unit(mock_get, mock_post, oauth_settings):
    mock_post.return_value = MagicMock(
        raise_for_status=lambda: None,
        json=lambda: {"access_token": "t"},
    )
    mock_get.return_value = MagicMock(
        raise_for_status=lambda: None,
        json=lambda: {
            "id": "1",
            "default_email": "u@yandex.ru",
            "first_name": "A",
            "last_name": "B",
        },
    )
    profile = exchange_code(
        provider="yandex",
        code="c",
        redirect_uri="https://academy.test/auth-callback",
    )
    assert profile["provider_user_id"] == "1"
    assert profile["email"] == "u@yandex.ru"
