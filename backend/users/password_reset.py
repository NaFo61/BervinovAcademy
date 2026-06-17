from datetime import timedelta
import hashlib
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import User

logger = logging.getLogger(__name__)

CODE_TTL = timedelta(minutes=15)
CODE_LENGTH = 6


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


def _hash_code(code: str) -> str:
    return make_password(code)


def _code_matches(code: str, code_hash: str) -> bool:
    return check_password(code, code_hash)


def generate_reset_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(CODE_LENGTH))


def _cache_key(login: str) -> str:
    digest = hashlib.sha256(normalize_login(login).encode()).hexdigest()
    return f"pwd_reset:{digest}"


def store_reset_code(login: str, code: str) -> None:
    from django.core.cache import cache

    payload = {
        "code_hash": _hash_code(code),
        "expires_at": (timezone.now() + CODE_TTL).isoformat(),
    }
    cache.set(
        _cache_key(login), payload, timeout=int(CODE_TTL.total_seconds())
    )


def get_reset_entry(login: str) -> dict | None:
    from django.core.cache import cache

    return cache.get(_cache_key(login))


def clear_reset_code(login: str) -> None:
    from django.core.cache import cache

    cache.delete(_cache_key(login))


def deliver_reset_code(user: User, code: str) -> None:
    contact = user.email or user.phone or "пользователь"
    message = (
        f"Код для восстановления пароля в Bervinov Academy: {code}\n"
        f"Код действует 15 минут."
    )
    if user.email:
        send_mail(
            subject="Восстановление пароля — Bervinov Academy",
            message=message,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@bervinov.dev"
            ),
            recipient_list=[user.email],
            fail_silently=True,
        )
        return
    logger.info("Password reset code for %s: %s", contact, code)


def issue_reset_code(login: str) -> tuple[bool, str | None]:
    """Returns (user_found, dev_code for DEBUG)."""
    user = find_user_by_login(login)
    if not user:
        return False, None

    code = generate_reset_code()
    store_reset_code(login, code)
    deliver_reset_code(user, code)
    dev_code = code if settings.DEBUG else None
    return True, dev_code


def confirm_reset_code(
    login: str, code: str, password: str
) -> tuple[bool, str | None]:
    entry = get_reset_entry(login)
    if not entry:
        return False, "Код не найден или истёк. Запросите новый."

    try:
        expires_at = timezone.datetime.fromisoformat(entry["expires_at"])
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)
    except (TypeError, ValueError):
        return False, "Код недействителен. Запросите новый."

    if timezone.now() > expires_at:
        clear_reset_code(login)
        return False, "Код истёк. Запросите новый."

    if not _code_matches(code.strip(), entry["code_hash"]):
        return False, "Неверный код."

    user = find_user_by_login(login)
    if not user:
        return False, "Пользователь не найден."

    user.set_password(password)
    user.save(update_fields=["password"])
    clear_reset_code(login)
    return True, None
