"""WebSocket consumers: чат и общая доска."""

from __future__ import annotations

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from . import chat_services
from .board_document import (
    BoardDocumentError,
    commit_item,
    load_document,
    remove_items,
    validate_item,
)
from .viewsets import user_may_open_board


class ChatConsumer(AsyncJsonWebsocketConsumer):
    thread_public_id = None
    group_name = None

    async def connect(self):
        user = self.scope.get("user")
        if (
            not user
            or isinstance(user, AnonymousUser)
            or not user.is_authenticated
        ):
            await self.close(code=4401)
            return

        self.thread_public_id = self.scope["url_route"]["kwargs"][
            "thread_public_id"
        ]
        try:
            thread = await self._get_thread(user)
        except Exception:
            await self.close(code=4403)
            return

        self.group_name = f"chat_thread_{thread.public_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "payload": {"thread_id": str(thread.public_id)},
            }
        )

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        event = content.get("event")
        if event == "ping":
            await self.send_json({"event": "pong", "payload": {}})
            return
        await self.send_json(
            {
                "event": "error",
                "payload": {
                    "detail": "Используйте REST API для отправки сообщений."
                },
            }
        )

    async def chat_event(self, event):
        await self.send_json(
            {
                "event": event.get("event"),
                "payload": event.get("payload"),
            }
        )

    async def _get_thread(self, user):
        from asgiref.sync import sync_to_async

        return await sync_to_async(chat_services.thread_for_user)(
            user=user,
            thread_public_id=self.thread_public_id,
        )


def board_group_name(owner_public_id) -> str:
    return f"user_board_{owner_public_id}"


class BoardConsumer(AsyncJsonWebsocketConsumer):
    """Одна доска, несколько человек: штрихи уходят всем сразу."""

    owner_public_id = None
    group_name = None

    async def connect(self):
        user = self.scope.get("user")
        if (
            not user
            or isinstance(user, AnonymousUser)
            or not user.is_authenticated
        ):
            await self.close(code=4401)
            return
        if not settings.WHITEBOARD_ENABLED:
            await self.close(code=4404)
            return

        self.owner_public_id = self.scope["url_route"]["kwargs"][
            "user_public_id"
        ]
        opened = await self._open_board(user)
        if opened is None:
            await self.close(code=4403)
            return

        self.group_name = board_group_name(self.owner_public_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        document, owner_id = opened
        await self.send_json(
            {
                "event": "hello",
                "payload": {
                    "document": document,
                    "actor_public_id": str(user.public_id),
                    "owner_public_id": owner_id,
                },
            }
        )

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        event = content.get("event")
        payload = content.get("payload") or {}
        if event == "ping":
            await self.send_json({"event": "pong", "payload": {}})
            return
        if event == "live":
            await self._live(payload)
            return
        if event == "commit":
            await self._commit(payload)
            return
        if event == "remove":
            await self._remove(payload)
            return
        await self.send_json(
            {
                "event": "error",
                "payload": {"detail": "Неизвестное событие доски."},
            }
        )

    async def board_event(self, event):
        await self.send_json(
            {
                "event": event.get("event"),
                "payload": event.get("payload"),
            }
        )

    async def _live(self, payload):
        try:
            item = validate_item((payload or {}).get("item"))
        except BoardDocumentError:
            return
        await self._broadcast(
            "live",
            {"item": item, "client": _client_id(payload)},
        )

    async def _commit(self, payload):
        user = self.scope["user"]
        try:
            document, item = await self._save_item(user, payload)
        except BoardDocumentError as exc:
            await self.send_json(
                {"event": "error", "payload": {"detail": str(exc)}}
            )
            return
        if item is None:
            item_id = ""
            raw_item = None
            if isinstance(payload, dict):
                raw_item = payload.get("item")
            if isinstance(raw_item, dict):
                candidate = raw_item.get("id")
                if isinstance(candidate, str):
                    item_id = candidate
            await self._broadcast(
                "remove",
                {
                    "ids": [item_id] if item_id else [],
                    "revision": document["revision"],
                    "client": _client_id(payload),
                    "author": str(user.public_id),
                },
            )
            return
        await self._broadcast(
            "commit",
            {
                "item": item,
                "revision": document["revision"],
                "client": _client_id(payload),
                "author": str(user.public_id),
            },
        )

    async def _remove(self, payload):
        user = self.scope["user"]
        try:
            document = await self._drop_items(user, payload)
        except BoardDocumentError as exc:
            await self.send_json(
                {"event": "error", "payload": {"detail": str(exc)}}
            )
            return
        ids = payload.get("ids") if isinstance(payload, dict) else []
        await self._broadcast(
            "remove",
            {
                "ids": ids if isinstance(ids, list) else [],
                "revision": document["revision"],
                "client": _client_id(payload),
                "author": str(user.public_id),
            },
        )

    async def _broadcast(self, event, payload):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "board.event", "event": event, "payload": payload},
        )

    @database_sync_to_async
    def _open_board(self, user):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        try:
            owner = user_model.objects.get(public_id=self.owner_public_id)
        except user_model.DoesNotExist:
            return None
        if not user_may_open_board(user, owner):
            return None
        return load_document(owner), str(owner.public_id)

    @database_sync_to_async
    def _save_item(self, user, payload):
        owner = self._owner_or_error(user)
        body = payload or {}
        return commit_item(
            owner,
            user,
            body.get("item"),
            restore=bool(body.get("restore")),
        )

    @database_sync_to_async
    def _drop_items(self, user, payload):
        owner = self._owner_or_error(user)
        ids = (payload or {}).get("ids")
        return remove_items(owner, user, ids)

    def _owner_or_error(self, user):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        owner = user_model.objects.get(public_id=self.owner_public_id)
        if not user_may_open_board(user, owner):
            raise BoardDocumentError("Нет доступа к этой доске.")
        return owner


def _client_id(payload) -> str:
    raw = ""
    if isinstance(payload, dict):
        raw = payload.get("client") or ""
    if not isinstance(raw, str):
        return ""
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in "_-")
    return cleaned[:40]
