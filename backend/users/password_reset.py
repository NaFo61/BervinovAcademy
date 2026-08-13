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

PREFIX = "pwd_reset"


def normalize_login(login: str) -> str:
    value = (login or "").strip()
    if "@" in value:
        return value.lower()
    return value


def find_user_by_login(login: str) -> User | None:
    normalized = normalize_login(login)
    if not normalized:
        return None
    if "@" in normalized:
        return User.objects.filter(email=normalized, is_active=True).first()
    return User.objects.filter(phone=normalized, is_active=True).first()


def deliver_reset_code(user: User, code: str) -> None:
    if user.email:
        send_code_email(
            to_email=user.email,
            kind="password_reset",
            code=code,
            recipient_name=user.get_full_name(),
        )
        return
    import logging

    logging.getLogger(__name__).info(
        "Password reset requested for phone user id=%s", user.pk
    )


def issue_reset_code(login: str) -> tuple[bool, str | None]:
    """Returns (user_found, dev_code for DEBUG)."""
    user = find_user_by_login(login)
    if not user:
        return False, None

    code = generate_code()
    store_code(PREFIX, normalize_login(login), code)
    deliver_reset_code(user, code)
    dev_code = code if settings.DEBUG else None
    return True, dev_code


def confirm_reset_code(
    login: str, code: str, password: str
) -> tuple[bool, str | None]:
    identity = normalize_login(login)
    entry = get_code_entry(PREFIX, identity)
    ok, error = validate_code_entry(entry, code)
    if not ok:
        if error and "истёк" in error.lower():
            clear_code(PREFIX, identity)
        return False, error

    user = find_user_by_login(login)
    if not user:
        return False, "Пользователь не найден."

    user.set_password(password)
    user.save(update_fields=["password"])
    clear_code(PREFIX, identity)
    return True, None
