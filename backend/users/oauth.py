"""OAuth: Яндекс ID и VK ID (id.vk.ru + PKCE)."""

from __future__ import annotations

import base64
import hashlib
import logging
import re
import secrets
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
import requests
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotFound,
    ValidationError,
)

logger = logging.getLogger(__name__)
User = get_user_model()

PROVIDERS = frozenset({"yandex", "vk"})

VK_AUTHORIZE_URL = "https://id.vk.ru/authorize"
VK_TOKEN_URL = "https://id.vk.ru/oauth2/auth"
VK_USER_INFO_URL = "https://id.vk.ru/oauth2/user_info"
VK_VERIFIER_CACHE_PREFIX = "oauth_vk_pkce:"
VK_VERIFIER_TTL = 600
_STATE_RE = re.compile(r"^[A-Za-z0-9_-]{32,}$")


class OAuthConflict(Exception):
    """Social id уже привязан к другому аккаунту."""

    def __init__(self, message: str = "Соц. аккаунт уже привязан."):
        self.message = message
        super().__init__(message)


def _frontend_base() -> str:
    return (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")


def default_redirect_uri() -> str:
    base = _frontend_base()
    if not base:
        return "/auth-callback"
    return f"{base}/auth-callback"


def _yandex_configured() -> bool:
    return bool(
        (getattr(settings, "YANDEX_OAUTH_CLIENT_ID", "") or "").strip()
        and (getattr(settings, "YANDEX_OAUTH_CLIENT_SECRET", "") or "").strip()
    )


def _vk_oauth_configured() -> bool:
    return bool(
        (getattr(settings, "VK_OAUTH_CLIENT_ID", "") or "").strip()
        and (getattr(settings, "VK_OAUTH_CLIENT_SECRET", "") or "").strip()
    )


def provider_configured(provider: str) -> bool:
    if provider == "yandex":
        return _yandex_configured()
    if provider == "vk":
        return _vk_oauth_configured()
    return False


def _pkce_pair() -> tuple[str, str]:
    """code_verifier + S256 code_challenge (RFC 7636)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _oauth_state(provider: str) -> str:
    # VK ID требует state ≥ 32 символов из [A-Za-z0-9_-]
    raw = f"ba_{provider}_{secrets.token_urlsafe(24)}"
    if not _STATE_RE.match(raw):
        raw = secrets.token_urlsafe(32)
    return raw


def build_authorize_url(
    *, provider: str, redirect_uri: str | None = None
) -> dict[str, str]:
    if provider not in PROVIDERS:
        raise ValidationError({"provider": "Неизвестный провайдер."})
    if not provider_configured(provider):
        raise ValidationError(
            {"detail": f"OAuth {provider} не настроен на сервере."}
        )

    redirect = (redirect_uri or default_redirect_uri()).strip()
    state = _oauth_state(provider)

    if provider == "yandex":
        client_id = settings.YANDEX_OAUTH_CLIENT_ID.strip()
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect,
            "state": state,
            "force_confirm": "yes",
        }
        url = "https://oauth.yandex.ru/authorize?" + urlencode(params)
        return {
            "authorize_url": url,
            "state": state,
            "redirect_uri": redirect,
            "provider": provider,
        }

    client_id = settings.VK_OAUTH_CLIENT_ID.strip()
    verifier, challenge = _pkce_pair()
    # Дублируем в cache (если Redis) и отдаём клиенту — LocMem
    # не шарится между gunicorn-воркерами.
    cache.set(
        f"{VK_VERIFIER_CACHE_PREFIX}{state}",
        verifier,
        timeout=VK_VERIFIER_TTL,
    )
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "scope": "email phone",
    }
    url = f"{VK_AUTHORIZE_URL}?" + urlencode(params)
    return {
        "authorize_url": url,
        "state": state,
        "redirect_uri": redirect,
        "provider": provider,
        "code_verifier": verifier,
    }


def exchange_code(
    *,
    provider: str,
    code: str,
    redirect_uri: str | None = None,
    device_id: str | None = None,
    state: str | None = None,
    code_verifier: str | None = None,
) -> dict[str, Any]:
    """Обменять code на профиль: {provider_user_id, email, first_name, last_name}."""
    if provider not in PROVIDERS:
        raise ValidationError({"provider": "Неизвестный провайдер."})
    code = (code or "").strip()
    if not code:
        raise ValidationError({"code": "Нужен authorization code."})
    redirect = (redirect_uri or default_redirect_uri()).strip()

    if provider == "yandex":
        return _exchange_yandex(code=code, redirect_uri=redirect)
    return _exchange_vk(
        code=code,
        redirect_uri=redirect,
        device_id=(device_id or "").strip(),
        state=(state or "").strip(),
        code_verifier=(code_verifier or "").strip(),
    )


def _exchange_yandex(*, code: str, redirect_uri: str) -> dict[str, Any]:
    if not _yandex_configured():
        raise ValidationError({"detail": "Yandex OAuth не настроен."})
    try:
        token_resp = requests.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_OAUTH_CLIENT_ID.strip(),
                "client_secret": settings.YANDEX_OAUTH_CLIENT_SECRET.strip(),
            },
            timeout=20,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access = token_data.get("access_token")
        if not access:
            raise AuthenticationFailed("Yandex не вернул access_token.")

        info_resp = requests.get(
            "https://login.yandex.ru/info",
            params={"format": "json"},
            headers={"Authorization": f"OAuth {access}"},
            timeout=20,
        )
        info_resp.raise_for_status()
        info = info_resp.json()
    except AuthenticationFailed:
        raise
    except Exception as exc:
        logger.exception("Yandex OAuth exchange failed")
        raise AuthenticationFailed("Не удалось войти через Яндекс.") from exc

    uid = str(info.get("id") or "").strip()
    if not uid:
        raise AuthenticationFailed("Yandex не вернул id.")
    email = info.get("default_email") or info.get("emails") or [None]
    if isinstance(email, list):
        email = email[0] if email else None
    email = (email or "").strip().lower() or None
    first = (
        info.get("first_name") or info.get("real_name") or "Ученик"
    ).strip()
    last = (info.get("last_name") or "").strip() or "Яндекс"
    if info.get("real_name") and not info.get("first_name"):
        parts = str(info["real_name"]).split(None, 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else last
    return {
        "provider": "yandex",
        "provider_user_id": uid,
        "email": email,
        "first_name": first[:255],
        "last_name": last[:255],
    }


def _exchange_vk(
    *,
    code: str,
    redirect_uri: str,
    device_id: str,
    state: str,
    code_verifier: str,
) -> dict[str, Any]:
    if not _vk_oauth_configured():
        raise ValidationError({"detail": "VK OAuth не настроен."})
    if not device_id:
        raise ValidationError({"device_id": "Нужен device_id от VK ID."})
    if not state:
        raise ValidationError({"state": "Нужен state от старта OAuth."})

    cache_key = f"{VK_VERIFIER_CACHE_PREFIX}{state}"
    verifier = (code_verifier or "").strip() or cache.get(cache_key)
    if not verifier:
        raise AuthenticationFailed("Сессия VK ID истекла. Начни вход заново.")
    cache.delete(cache_key)

    client_id = settings.VK_OAUTH_CLIENT_ID.strip()
    try:
        token_resp = requests.post(
            VK_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": verifier,
                "client_id": client_id,
                "client_secret": settings.VK_OAUTH_CLIENT_SECRET.strip(),
                "device_id": device_id,
                "redirect_uri": redirect_uri,
                "state": state,
            },
            timeout=20,
        )
        token_data = token_resp.json() if token_resp.content else {}
        if token_resp.status_code >= 400 or token_data.get("error"):
            desc = (
                token_data.get("error_description")
                or token_data.get("error")
                or f"HTTP {token_resp.status_code}"
            )
            logger.warning("VK ID token error: %s", token_data)
            raise AuthenticationFailed(str(desc))
        access = token_data.get("access_token")
        user_id = token_data.get("user_id")
        email = (token_data.get("email") or "").strip().lower() or None
        if not access or not user_id:
            raise AuthenticationFailed("VK не вернул токен.")

        info_resp = requests.post(
            VK_USER_INFO_URL,
            data={
                "access_token": access,
                "client_id": client_id,
            },
            timeout=20,
        )
        info_payload = info_resp.json() if info_resp.content else {}
        if info_resp.status_code >= 400 or info_payload.get("error"):
            logger.warning("VK ID user_info error: %s", info_payload)
            profile = {}
        else:
            profile = info_payload.get("user") or {}
            if not email:
                email = (profile.get("email") or "").strip().lower() or None
    except AuthenticationFailed:
        raise
    except Exception as exc:
        logger.exception("VK OAuth exchange failed")
        raise AuthenticationFailed("Не удалось войти через VK.") from exc

    first = (profile.get("first_name") or "Ученик").strip()
    last = (profile.get("last_name") or "VK").strip()
    return {
        "provider": "vk",
        "provider_user_id": str(int(user_id)),
        "email": email,
        "first_name": first[:255],
        "last_name": last[:255],
    }


def resolve_or_create_user(profile: dict[str, Any]):
    """Найти или создать пользователя по OAuth-профилю."""
    provider = profile["provider"]
    pid = profile["provider_user_id"]
    email = profile.get("email")

    if provider == "yandex":
        user = User.objects.filter(yandex_id=pid).first()
    else:
        user = User.objects.filter(vk_id=int(pid)).first()
    if user:
        return user, False

    if email:
        user = User.objects.filter(email__iexact=email).first()
        if user:
            _attach_provider(user, provider, pid)
            return user, False

    kwargs: dict[str, Any] = {
        "first_name": profile.get("first_name") or "Ученик",
        "last_name": profile.get("last_name") or provider.upper(),
        "role": "student",
        "email": email,
    }
    if provider == "yandex":
        kwargs["yandex_id"] = pid
    else:
        kwargs["vk_id"] = int(pid)

    user = User.objects.create_user(**kwargs)
    return user, True


def link_provider_to_user(user, profile: dict[str, Any]) -> None:
    provider = profile["provider"]
    pid = profile["provider_user_id"]
    if provider == "yandex":
        other = User.objects.filter(yandex_id=pid).exclude(pk=user.pk).first()
        if other:
            raise OAuthConflict("Этот Яндекс уже привязан к другому аккаунту.")
        user.yandex_id = pid
        user.save(update_fields=["yandex_id"])
    else:
        vk_id = int(pid)
        other = User.objects.filter(vk_id=vk_id).exclude(pk=user.pk).first()
        if other:
            raise OAuthConflict("Этот VK уже привязан к другому аккаунту.")
        user.vk_id = vk_id
        user.save(update_fields=["vk_id"])


def unlink_provider(user, provider: str) -> None:
    if provider not in PROVIDERS:
        raise ValidationError({"provider": "Неизвестный провайдер."})

    has_password = user.has_usable_password()
    has_email_or_phone = bool(user.email or user.phone)
    if provider == "yandex":
        if not user.yandex_id:
            raise NotFound("Яндекс не привязан.")
        remaining = has_password or has_email_or_phone or bool(user.vk_id)
        if not remaining:
            raise ValidationError(
                {"detail": "Нельзя отвязать единственный способ входа."}
            )
        user.yandex_id = None
        user.save(update_fields=["yandex_id"])
    else:
        if not user.vk_id:
            raise NotFound("VK не привязан.")
        remaining = has_password or has_email_or_phone or bool(user.yandex_id)
        if not remaining:
            raise ValidationError(
                {"detail": "Нельзя отвязать единственный способ входа."}
            )
        user.vk_id = None
        user.vk_messages_allowed = False
        user.save(update_fields=["vk_id", "vk_messages_allowed"])


def _attach_provider(user, provider: str, pid: str) -> None:
    if provider == "yandex":
        if user.yandex_id and user.yandex_id != pid:
            raise OAuthConflict()
        if not user.yandex_id:
            conflict = (
                User.objects.filter(yandex_id=pid).exclude(pk=user.pk).exists()
            )
            if conflict:
                raise OAuthConflict()
            user.yandex_id = pid
            user.save(update_fields=["yandex_id"])
    else:
        vk_id = int(pid)
        if user.vk_id and user.vk_id != vk_id:
            raise OAuthConflict()
        if not user.vk_id:
            conflict = (
                User.objects.filter(vk_id=vk_id).exclude(pk=user.pk).exists()
            )
            if conflict:
                raise OAuthConflict()
            user.vk_id = vk_id
            user.save(update_fields=["vk_id"])
