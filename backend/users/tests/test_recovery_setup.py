"""Recovery setup: пароль + контакты после OAuth."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.oauth import resolve_or_create_user
from users.serializers import inject_access_claims
from users.tests.conftest import make_user


@pytest.fixture
def api():
    return APIClient()


def _auth(client, user):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    inject_access_claims(access, user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def _oauth_user(**kwargs):
    defaults = {
        "email": None,
        "phone": None,
        "first_name": "Олег",
        "last_name": "OAuth",
        "role": "student",
        "vk_id": 9001,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(**defaults)
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


@pytest.mark.django_db
def test_me_recovery_flags_before_after(api):
    user = _oauth_user(email=None, phone=None, vk_id=11)
    _auth(api, user)
    before = api.get("/api/users/me/")
    assert before.status_code == 200
    rec = before.json()["recovery"]
    assert rec["needs_setup"] is True
    assert rec["has_usable_password"] is False
    assert rec["has_email"] is False
    assert rec["has_phone"] is False
    assert rec["ready"] is False

    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "email": "vk11@ex.com",
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    rec = resp.json()["recovery"]
    assert rec["ready"] is True
    assert rec["needs_setup"] is False
    assert rec["has_usable_password"] is True
    assert rec["has_email"] is True


@pytest.mark.django_db
def test_setup_password_and_both_contacts(api):
    user = _oauth_user(email=None, phone=None, vk_id=22)
    _auth(api, user)
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "email": "both@ex.com",
            "phone": "+79002220022",
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    user.refresh_from_db()
    assert user.email == "both@ex.com"
    assert user.phone == "+79002220022"
    assert user.check_password("NewPass1!")
    assert resp.json()["recovery"]["ready"] is True

    login = api.post(
        "/api/auth/login/",
        {"login": "both@ex.com", "password": "NewPass1!"},
        format="json",
    )
    assert login.status_code == 200


@pytest.mark.django_db
def test_setup_password_plus_one_contact_then_second(api):
    user = _oauth_user(
        email="one@ex.com", phone=None, yandex_id="ya-1", vk_id=None
    )
    user.set_unusable_password()
    user.save()
    _auth(api, user)

    first = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert first.status_code == 200, first.content
    assert first.json()["recovery"]["ready"] is True
    assert first.json()["recovery"]["has_phone"] is False

    second = api.post(
        "/api/auth/recovery/setup/",
        {"phone": "+79001110011"},
        format="json",
    )
    # Только контакт — смена пароля не нужна
    assert second.status_code == 200, second.content
    user.refresh_from_db()
    assert user.phone == "+79001110011"
    assert second.json()["recovery"]["has_phone"] is True


@pytest.mark.django_db
def test_setup_password_only_when_email_from_oauth(api):
    user = _oauth_user(
        email="oauth@ex.com", phone=None, yandex_id="ya-2", vk_id=None
    )
    _auth(api, user)
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["recovery"]["ready"] is True
    login = APIClient().post(
        "/api/auth/login/",
        {"login": "oauth@ex.com", "password": "NewPass1!"},
        format="json",
    )
    assert login.status_code == 200


@pytest.mark.django_db
def test_setup_duplicate_email_409(api):
    make_user(email="taken@ex.com")
    user = _oauth_user(email=None, phone=None, vk_id=33)
    _auth(api, user)
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "email": "taken@ex.com",
        },
        format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_setup_duplicate_phone_409(api):
    make_user(email="other@ex.com", phone="+79003330033")
    user = _oauth_user(email=None, phone=None, vk_id=34)
    _auth(api, user)
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "phone": "+79003330033",
        },
        format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_setup_without_jwt_401(api):
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "email": "x@ex.com",
        },
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_change_password_requires_current(api):
    user = make_user(email="pwd@ex.com")
    user.set_password("OldPass1!")
    user.save()
    _auth(api, user)
    bad = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert bad.status_code == 400
    assert "current_password" in bad.json()

    ok = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
            "current_password": "OldPass1!",
        },
        format="json",
    )
    assert ok.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPass1!")


@pytest.mark.django_db
def test_password_only_without_contacts_400(api):
    user = _oauth_user(email=None, phone=None, vk_id=44)
    _auth(api, user)
    resp = api.post(
        "/api/auth/recovery/setup/",
        {
            "password": "NewPass1!",
            "password_confirm": "NewPass1!",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_resolve_vk_saves_phone():
    user, created = resolve_or_create_user(
        {
            "provider": "vk",
            "provider_user_id": "5555",
            "email": None,
            "phone": "+79005550055",
            "first_name": "Вк",
            "last_name": "Тест",
        }
    )
    assert created
    assert user.vk_id == 5555
    assert user.phone == "+79005550055"
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_resolve_yandex_saves_email():
    user, created = resolve_or_create_user(
        {
            "provider": "yandex",
            "provider_user_id": "ya-55",
            "email": "ya55@yandex.ru",
            "phone": "+79005551122",
            "first_name": "Ян",
            "last_name": "Декс",
        }
    )
    assert created
    assert user.yandex_id == "ya-55"
    assert user.email == "ya55@yandex.ru"
    assert user.phone == "+79005551122"


@pytest.mark.django_db
def test_resolve_fills_phone_on_existing_vk_user():
    user = _oauth_user(email=None, phone=None, vk_id=6666)
    updated, created = resolve_or_create_user(
        {
            "provider": "vk",
            "provider_user_id": "6666",
            "email": None,
            "phone": "+79006660066",
            "first_name": "Вк",
            "last_name": "Есть",
        }
    )
    assert created is False
    assert updated.pk == user.pk
    updated.refresh_from_db()
    assert updated.phone == "+79006660066"


@pytest.mark.django_db
def test_resolve_skips_taken_phone():
    make_user(email="owner@ex.com", phone="+79007770077")
    user, created = resolve_or_create_user(
        {
            "provider": "vk",
            "provider_user_id": "7777",
            "email": None,
            "phone": "+79007770077",
            "first_name": "Вк",
            "last_name": "Конфликт",
        }
    )
    assert created
    assert user.vk_id == 7777
    assert user.phone is None


@pytest.mark.django_db
@patch("users.oauth.requests.post")
def test_oauth_exchange_vk_saves_phone(mock_post, api, settings):
    from django.core.cache import cache

    from users.oauth import VK_VERIFIER_CACHE_PREFIX, build_authorize_url

    settings.FRONTEND_URL = "https://academy.test"
    settings.VK_OAUTH_CLIENT_ID = "vk-client"
    settings.VK_OAUTH_CLIENT_SECRET = "vk-secret"

    start = build_authorize_url(
        provider="vk",
        redirect_uri="https://academy.test/auth-callback",
    )
    state = start["state"]

    def fake_post(url, **kwargs):
        m = MagicMock()
        m.status_code = 200
        m.content = b"{}"
        if "oauth2/auth" in str(url):
            m.json = lambda: {
                "access_token": "vk-tok",
                "user_id": 8888,
            }
        else:
            m.json = lambda: {
                "user": {
                    "user_id": "8888",
                    "first_name": "Вк",
                    "last_name": "Новый",
                    "phone": "+79008880088",
                }
            }
        return m

    mock_post.side_effect = fake_post
    resp = api.post(
        "/api/auth/oauth/vk/",
        {
            "code": "code",
            "redirect_uri": "https://academy.test/auth-callback",
            "device_id": "dev-1",
            "state": state,
            "code_verifier": cache.get(f"{VK_VERIFIER_CACHE_PREFIX}{state}"),
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    u = User.objects.get(vk_id=8888)
    assert u.phone == "+79008880088"
    assert not u.has_usable_password()
