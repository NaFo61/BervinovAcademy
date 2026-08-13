"""Общая логика 6-значных кодов на email (сброс пароля / подтверждение)."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import logging
import secrets
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
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


CODE_EMAILS = {
    "email_verify": {
        "subject": "Подтверждение почты — Bervinov Academy",
        "heading": "Подтверждение почты",
        "intro": (
            "Введите этот код в Bervinov Academy, " "чтобы подтвердить почту."
        ),
        "plain_lead": ("Код для подтверждения почты в Bervinov Academy"),
        "disclaimer": (
            "Если вы не запрашивали подтверждение — " "проигнорируйте письмо."
        ),
        "preheader": "Код подтверждения почты, действует 15 минут",
        "cta_label": "Открыть Академию",
        "cta_path": "/profile",
    },
    "password_reset": {
        "subject": "Восстановление пароля — Bervinov Academy",
        "heading": "Восстановление пароля",
        "intro": ("Введите этот код на сайте, чтобы задать новый пароль."),
        "plain_lead": ("Код для восстановления пароля в Bervinov Academy"),
        "disclaimer": (
            "Если вы не запрашивали сброс — просто " "проигнорируйте письмо."
        ),
        "preheader": "Код для сброса пароля, действует 15 минут",
        "cta_label": "Открыть Академию",
        "cta_path": "/auth",
    },
}


def _frontend_base() -> str:
    return (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")


def _recipient_label(name: str | None, email: str) -> str:
    cleaned = (name or "").strip()
    return cleaned or email


def _recipient_initial(name: str | None, email: str) -> str:
    label = _recipient_label(name, email)
    for char in label:
        if char.isalnum():
            return char.upper()
    return "B"


def build_code_email(
    *,
    kind: str,
    code: str,
    to_email: str,
    recipient_name: str | None = None,
) -> tuple[str, str, str]:
    """Тема, обычный текст и HTML для письма с кодом."""
    spec = CODE_EMAILS[kind]
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    base = _frontend_base()
    site_host = urlparse(base).netloc if base else ""
    context = {
        "subject": spec["subject"],
        "heading": spec["heading"],
        "intro": spec["intro"],
        "plain_lead": spec["plain_lead"],
        "code": code,
        "ttl_minutes": ttl_minutes,
        "disclaimer": spec["disclaimer"],
        "preheader": spec["preheader"],
        "cta_label": spec["cta_label"],
        "cta_url": f"{base}{spec['cta_path']}" if base else "",
        "catalog_url": f"{base}/catalog" if base else "",
        "auth_url": f"{base}/auth" if base else "",
        "site_url": base,
        "site_host": site_host or base,
        "recipient_email": to_email,
        "recipient_name": _recipient_label(recipient_name, to_email),
        "recipient_initial": _recipient_initial(recipient_name, to_email),
        "year": timezone.now().year,
    }
    plain = render_to_string("emails/code.txt", context).strip() + "\n"
    html = render_to_string("emails/code.html", context)
    return spec["subject"], plain, html


def send_code_email(
    *,
    to_email: str,
    kind: str,
    code: str,
    recipient_name: str | None = None,
) -> bool:
    """Отправить HTML-письмо с текстовой копией. False при ошибке SMTP."""
    subject, body, html = build_code_email(
        kind=kind,
        code=code,
        to_email=to_email,
        recipient_name=recipient_name,
    )
    from_email = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@bervinov.dev"
    )
    try:
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html,
            fail_silently=False,
        )
        return bool(sent)
    except Exception:
        logger.exception(
            "Email send failed to=%s subject=%s", to_email, subject
        )
        return False
