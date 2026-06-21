"""WebSocket consumer для чата."""

from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from . import chat_services


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
