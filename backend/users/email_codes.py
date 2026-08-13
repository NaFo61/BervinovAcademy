"""Общая логика 6-значных кодов на email (сброс пароля / подтверждение)."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

CODE_TTL = timedelta(minutes=15)
CODE_LENGTH = 6


def generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(CODE_LENGTH))


def hash_code(code: str) -> str:
    return make_password(code)


def code_matches(code: str, code_hash: str) -> bool:
    return check_password(code, code_hash)


def cache_key(prefix: str, identity: str) -> str:
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"{prefix}:{digest}"


def store_code(prefix: str, identity: str, code: str) -> None:
    from django.core.cache import cache

    payload = {
        "code_hash": hash_code(code),
        "expires_at": (timezone.now() + CODE_TTL).isoformat(),
    }
    cache.set(
        cache_key(prefix, identity),
        payload,
        timeout=int(CODE_TTL.total_seconds()),
    )


def get_code_entry(prefix: str, identity: str) -> dict | None:
    from django.core.cache import cache

    return cache.get(cache_key(prefix, identity))


def clear_code(prefix: str, identity: str) -> None:
    from django.core.cache import cache

    cache.delete(cache_key(prefix, identity))


def validate_code_entry(
    entry: dict | None, code: str
) -> tuple[bool, str | None]:
    if not entry:
        return False, "Код не найден или истёк. Запросите новый."
    try:
        expires_at = timezone.datetime.fromisoformat(entry["expires_at"])
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)
    except (TypeError, ValueError, KeyError):
        return False, "Код недействителен. Запросите новый."
    if timezone.now() > expires_at:
        return False, "Код истёк. Запросите новый."
    if not code_matches((code or "").strip(), entry.get("code_hash") or ""):
        return False, "Неверный код."
    return True, None


def send_code_email(*, to_email: str, subject: str, body: str) -> bool:
    """Отправить письмо. False при ошибке SMTP (уже залогировано)."""
    from_email = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@bervinov.dev"
    )
    try:
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return bool(sent)
    except Exception:
        logger.exception(
            "Email send failed to=%s subject=%s", to_email, subject
        )
        return False
