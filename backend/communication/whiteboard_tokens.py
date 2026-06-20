"""HMAC-токены для доступа к tldraw sync (общий секрет с sync-сервером)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from django.conf import settings


def _secret_bytes() -> bytes:
    secret = (
        getattr(settings, "WHITEBOARD_SYNC_SECRET", "") or settings.SECRET_KEY
    )
    return secret.encode()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def issue_whiteboard_sync_token(
    conference_public_id,
    user_public_id,
    *,
    ttl_seconds: int | None = None,
) -> str:
    ttl = ttl_seconds or getattr(
        settings, "WHITEBOARD_TOKEN_TTL_SECONDS", 3600
    )
    payload = {
        "conf": str(conference_public_id),
        "sub": str(user_public_id),
        "exp": int(time.time()) + int(ttl),
    }
    body = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    sig = hmac.new(_secret_bytes(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_whiteboard_sync_token(
    token: str,
    conference_public_id,
) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None

    body, sig = token.rsplit(".", 1)
    if not body or not sig:
        return None

    expected = hmac.new(
        _secret_bytes(), body.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None

    try:
        payload = json.loads(_b64url_decode(body))
    except (json.JSONDecodeError, ValueError):
        return None

    if payload.get("conf") != str(conference_public_id):
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None

    if not payload.get("sub"):
        return None

    return payload
