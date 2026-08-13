"""Подтверждение email кодом из письма."""

from __future__ import annotations

from django.conf import settings

from .email_codes import (
    clear_code,
    generate_code,
    get_code_entry,
    send_code_email,
    store_code,
    validate_code_entry,
)
from .models import User

PREFIX = "email_verify"


def _identity(user: User) -> str:
    return f"user:{user.pk}:{(user.email or '').lower()}"


def issue_verify_code(user: User) -> tuple[bool, str | None, str | None]:
    """
    Returns (ok, error_message, dev_code).
    ok=True и error=None — код отправлен или уже подтверждён.
    """
    email = (user.email or "").strip().lower()
    if not email:
        return False, "Сначала укажите email в профиле.", None
    if user.email_verified:
        return True, None, None

    code = generate_code()
    store_code(PREFIX, _identity(user), code)
    body = (
        f"Код для подтверждения почты в Bervinov Academy: {code}\n"
        f"Код действует 15 минут.\n\n"
        f"Если вы не запрашивали подтверждение — проигнорируйте письмо."
    )
    sent = send_code_email(
        to_email=email,
        subject="Подтверждение почты — Bervinov Academy",
        body=body,
    )
    if not sent and not settings.DEBUG:
        return (
            False,
            "Не удалось отправить письмо. Попробуйте позже.",
            None,
        )
    dev_code = code if settings.DEBUG else None
    return True, None, dev_code


def confirm_verify_code(user: User, code: str) -> tuple[bool, str | None]:
    email = (user.email or "").strip().lower()
    if not email:
        return False, "Сначала укажите email в профиле."
    if user.email_verified:
        return True, None

    identity = _identity(user)
    entry = get_code_entry(PREFIX, identity)
    ok, error = validate_code_entry(entry, code)
    if not ok:
        if error and "истёк" in error.lower():
            clear_code(PREFIX, identity)
        return False, error

    user.email_verified = True
    user.save(update_fields=["email_verified"])
    clear_code(PREFIX, identity)
    return True, None
