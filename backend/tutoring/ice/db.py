"""Подключение к Postgres ICE (read/write одной кассы с ботом)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

from django.conf import settings

from tutoring.services import TutoringError


def ice_configured() -> bool:
    return bool((getattr(settings, "ICE_DATABASE_URL", "") or "").strip())


def _dsn() -> str:
    raw = (getattr(settings, "ICE_DATABASE_URL", "") or "").strip()
    if not raw:
        raise TutoringError(
            "Кабинет бота не подключён (ICE_DATABASE_URL).", 503
        )
    # Django/psycopg2 не понимают sqlalchemy async-схему.
    return raw.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgres+asyncpg://", "postgresql://"
    )


@contextmanager
def ice_cursor() -> Iterator:
    import psycopg2
    import psycopg2.extras

    try:
        conn = psycopg2.connect(_dsn())
    except Exception as exc:  # noqa: BLE001 — сеть/DSN
        raise TutoringError(
            "Не удалось подключиться к базе бота.", 503
        ) from exc
    try:
        with conn:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                yield cur
    finally:
        conn.close()


def ice_host_hint() -> str:
    raw = (getattr(settings, "ICE_DATABASE_URL", "") or "").strip()
    if not raw:
        return ""
    try:
        return urlparse(_dsn()).hostname or ""
    except Exception:  # noqa: BLE001
        return ""
