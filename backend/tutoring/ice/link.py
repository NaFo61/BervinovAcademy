"""Привязка academy user ↔ ICE tutor по Telegram / явному tutor id."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from tutoring.ice.db import ice_configured, ice_cursor
from tutoring.models import TutoringIceLink
from tutoring.services import TutoringError


def _bot_username() -> str:
    return (getattr(settings, "ICE_BOT_USERNAME", "") or "").strip() or (
        getattr(settings, "TELEGRAM_BOT_USERNAME", "") or ""
    ).lstrip("@").strip()


def _fetch_tutor(tutor_id: int) -> dict | None:
    with ice_cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.display_name, t.status::text AS status,
                   t.user_id, t.timezone, u.tg_id
            FROM tutors t
            LEFT JOIN users u ON u.id = t.user_id
            WHERE t.id = %s
            """,
            (tutor_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def _fetch_tutor_by_tg(telegram_id: int) -> dict | None:
    with ice_cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.display_name, t.status::text AS status,
                   t.user_id, t.timezone, u.tg_id
            FROM tutors t
            JOIN users u ON u.id = t.user_id
            WHERE u.tg_id = %s
              AND t.status::text <> 'blocked'
            ORDER BY t.id
            LIMIT 1
            """,
            (int(telegram_id),),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def link_user_to_ice(
    *, user, ice_tutor_id: int | None = None
) -> TutoringIceLink:
    if not ice_configured():
        raise TutoringError("Кабинет бота не подключён.", 503)
    if user.role not in ("mentor", "admin"):
        raise TutoringError("Только ментор или админ.", 403)

    tutor = None
    if ice_tutor_id:
        tutor = _fetch_tutor(int(ice_tutor_id))
        if tutor is None:
            raise TutoringError("Репетитор в боте не найден.", 404)
        if tutor["status"] == "blocked":
            raise TutoringError("Этот кабинет в боте заблокирован.", 403)
    else:
        tg = getattr(user, "telegram_id", None)
        if not tg:
            raise TutoringError("Сначала привяжите Telegram в профиле.", 400)
        tutor = _fetch_tutor_by_tg(int(tg))
        if tutor is None:
            raise TutoringError(
                "В боте нет активного кабинета репетитора "
                "для этого Telegram. Откройте инвайт-ссылку в "
                f"@{_bot_username() or 'боте'}.",
                404,
            )

    link, _ = TutoringIceLink.objects.update_or_create(
        user=user,
        defaults={
            "ice_tutor_id": int(tutor["id"]),
            "telegram_id": tutor.get("tg_id")
            or getattr(user, "telegram_id", None),
            "display_name": (tutor.get("display_name") or "")[:255],
            "linked_at": timezone.now(),
        },
    )
    return link


def resolve_ice_tutor_id(user, mentor_public_id: str | None = None) -> int:
    """ICE tutor id для текущего ментора/админа."""
    from django.contrib.auth import get_user_model

    target = user
    if user.role == "admin" and mentor_public_id:
        found = (
            get_user_model()
            .objects.filter(
                public_id=mentor_public_id,
                role__in=("mentor", "admin"),
                is_active=True,
            )
            .first()
        )
        if found is None:
            raise TutoringError("Ментор не найден.", 404)
        target = found

    link = TutoringIceLink.objects.filter(user=target).first()
    if link is not None:
        return int(link.ice_tutor_id)

    # Авто-попытка по Telegram.
    if ice_configured() and getattr(target, "telegram_id", None):
        try:
            link = link_user_to_ice(user=target)
            return int(link.ice_tutor_id)
        except TutoringError:
            pass

    raise TutoringError(
        "Кабинет бота ещё не привязан. Привяжите Telegram "
        "и активируйте инвайт репетитора.",
        409,
    )


def ice_status(user) -> dict:
    bot = _bot_username()
    payload = {
        "ice_enabled": ice_configured(),
        "telegram_linked": bool(getattr(user, "telegram_id", None)),
        "ice_linked": False,
        "bot_username": bot,
        "bot_url": f"https://t.me/{bot}" if bot else "",
        "tutor": None,
        "hint": "",
    }
    if not payload["ice_enabled"]:
        payload["hint"] = (
            "На сервере ещё не указан ICE_DATABASE_URL — "
            "связь с ботом выключена."
        )
        return payload

    link = TutoringIceLink.objects.filter(user=user).first()
    if link is None and getattr(user, "telegram_id", None):
        try:
            link = link_user_to_ice(user=user)
        except TutoringError as exc:
            payload["hint"] = exc.detail
            return payload

    if link is None:
        payload["hint"] = (
            "Привяжите Telegram в профиле, затем откройте "
            f"инвайт репетитора в боте @{bot or '…'}."
            if not payload["telegram_linked"]
            else (
                "Telegram есть, но кабинет в боте ещё не активирован. "
                f"Нужна инвайт-ссылка репетитора (@{bot or '…'})."
            )
        )
        return payload

    tutor = None
    try:
        tutor = _fetch_tutor(link.ice_tutor_id)
    except TutoringError as exc:
        payload["hint"] = exc.detail
        return payload

    payload["ice_linked"] = True
    payload["tutor"] = {
        "ice_tutor_id": link.ice_tutor_id,
        "display_name": (tutor or {}).get("display_name") or link.display_name,
        "status": (tutor or {}).get("status") or "unknown",
        "timezone": (tutor or {}).get("timezone") or "",
    }
    if tutor and tutor.get("status") == "invited":
        payload["hint"] = (
            "Кабинет в боте создан, но ещё не активирован. "
            f"Откройте инвайт в @{bot or 'боте'} своим Telegram."
        )
    return payload
