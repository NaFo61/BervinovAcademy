"""Генерация JWT для подключения к LiveKit."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings


class LiveKitNotConfiguredError(RuntimeError):
    """LiveKit credentials не заданы в настройках."""


def livekit_configured() -> bool:
    return bool(
        getattr(settings, "LIVEKIT_URL", "")
        and getattr(settings, "LIVEKIT_API_KEY", "")
        and getattr(settings, "LIVEKIT_API_SECRET", "")
    )


def issue_room_token(
    *,
    room_name: str,
    identity: str,
    name: str,
    ttl_hours: int | None = None,
) -> str:
    if not livekit_configured():
        raise LiveKitNotConfiguredError(
            "LiveKit не настроен. Задайте LIVEKIT_URL, LIVEKIT_API_KEY "
            "и LIVEKIT_API_SECRET."
        )

    from livekit.api import AccessToken, VideoGrants

    hours = ttl_hours or getattr(settings, "LIVEKIT_TOKEN_TTL_HOURS", 4)
    token = AccessToken(
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    token.with_identity(identity)
    token.with_name(name)
    token.with_ttl(timedelta(hours=hours))
    token.with_grants(
        VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    )
    return token.to_jwt()
