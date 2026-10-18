"""Настройки бота Telegram и отправка сообщений."""

from __future__ import annotations

from http import client
import json
import logging
import socket
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)


class _IPv4HTTPSConnection(client.HTTPSConnection):
    """Сервер видит Telegram только по IPv4. IPv6 до него не доходит."""

    def connect(self):
        results = socket.getaddrinfo(
            self.host,
            self.port,
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
        af, socktype, proto, _canon, address = results[0]
        sock = socket.socket(af, socktype, proto)
        if self.timeout is not None:
            sock.settimeout(self.timeout)
        sock.connect(address)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _IPv4HTTPSHandler(request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_IPv4HTTPSConnection, req)


_OPENER = request.build_opener(_IPv4HTTPSHandler)


def is_configured() -> bool:
    return bool((getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip())


def bot_username() -> str:
    raw = (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").strip()
    return raw.lstrip("@")


def start_url(token: str) -> str:
    name = bot_username()
    code = (token or "").strip()
    if not name or not code:
        return ""
    return f"https://t.me/{name}?start={code}"


def send_message(chat_id, text: str) -> bool:
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token or not chat_id or not text:
        return False
    payload = json.dumps(
        {"chat_id": chat_id, "text": text}, ensure_ascii=False
    ).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _OPENER.open(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (error.URLError, TimeoutError, ValueError):
        logger.exception("Telegram send failed")
        return False
