"""WebSocket integration tests for chat."""

from urllib.parse import quote

from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from school_platform.asgi import application

from communication import chat_services


def _ws_path(thread_public_id, user):
    token = str(AccessToken.for_user(user))
    return (
        f"/ws/chat/threads/{thread_public_id}/?token={quote(token, safe='')}"
    )


def _run(coro):
    return async_to_sync(coro)()


class TestChatWebSocket:
    def test_unauthorized_connection_rejected(self, db):
        async def run():
            communicator = WebsocketCommunicator(
                application,
                "/ws/chat/threads/00000000-0000-0000-0000-000000000001/",
            )
            connected, _ = await communicator.connect()
            assert not connected

        _run(run)

    def test_participant_connects(self, mentor_user, student_user):
        async def run():
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            communicator = WebsocketCommunicator(
                application,
                _ws_path(thread.public_id, student_user),
            )
            connected, _ = await communicator.connect()
            assert connected
            hello = await communicator.receive_json_from()
            assert hello["event"] == "connected"
            await communicator.disconnect()

        _run(run)

    def test_outsider_connection_rejected(self, mentor_user, student_user, db):
        async def run():
            outsider = await sync_to_async(
                mentor_user.__class__.objects.create_user
            )(
                email="outsider-chat@academy.com",
                phone="+79001110088",
                password="password",
                role="student",
            )
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            communicator = WebsocketCommunicator(
                application,
                _ws_path(thread.public_id, outsider),
            )
            connected, _ = await communicator.connect()
            assert not connected

        _run(run)

    def test_message_new_broadcast_to_peer(self, mentor_user, student_user):
        async def run():
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            communicator = WebsocketCommunicator(
                application,
                _ws_path(thread.public_id, student_user),
            )
            connected, _ = await communicator.connect()
            assert connected
            await communicator.receive_json_from()

            await sync_to_async(chat_services.create_text_message)(
                thread=thread,
                sender=mentor_user,
                body="Привет по WS",
            )

            event = await communicator.receive_json_from()
            assert event["event"] == "message.new"
            assert event["payload"]["body"] == "Привет по WS"
            await communicator.disconnect()

        _run(run)

    def test_message_updated_and_deleted_events(
        self, mentor_user, student_user
    ):
        from channels.layers import get_channel_layer

        async def run():
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            message = await sync_to_async(chat_services.create_text_message)(
                thread=thread,
                sender=mentor_user,
                body="Было",
            )
            channel_layer = get_channel_layer()
            channel_name = await channel_layer.new_channel()
            await channel_layer.group_add(
                f"chat_thread_{thread.public_id}",
                channel_name,
            )

            message = await sync_to_async(chat_services.update_text_message)(
                message=message,
                editor=mentor_user,
                body="Стало",
            )
            assert message.body == "Стало"
            updated = await channel_layer.receive(channel_name)
            assert updated["event"] == "message.updated"
            assert updated["payload"]["body"] == "Стало"

            await sync_to_async(chat_services.delete_text_message)(
                message=message,
                deleter=mentor_user,
            )
            deleted = await channel_layer.receive(channel_name)
            assert deleted["event"] == "message.deleted"
            assert deleted["payload"]["is_deleted"] is True

        _run(run)

    def test_channel_layer_receives_message_new(
        self, mentor_user, student_user
    ):
        from channels.layers import get_channel_layer

        async def run():
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            channel_layer = get_channel_layer()
            channel_name = await channel_layer.new_channel()
            await channel_layer.group_add(
                f"chat_thread_{thread.public_id}",
                channel_name,
            )
            await sync_to_async(chat_services.create_text_message)(
                thread=thread,
                sender=mentor_user,
                body="layer-test",
            )
            event = await channel_layer.receive(channel_name)
            assert event["type"] == "chat.event"
            assert event["event"] == "message.new"
            assert event["payload"]["body"] == "layer-test"

        _run(run)

    def test_many_messages_stay_consistent(self, mentor_user, student_user):
        thread = chat_services.get_or_create_thread(
            actor=mentor_user,
            other=student_user,
        )
        for idx in range(100):
            chat_services.create_text_message(
                thread=thread,
                sender=mentor_user,
                body=f"msg-{idx}",
            )

        rows, _has_more = chat_services.list_thread_messages(
            thread=thread,
            limit=100,
        )
        assert len(rows) == 100
        assert rows[-1].body == "msg-99"
        assert rows[0].body == "msg-0"

    def test_ping_pong(self, mentor_user, student_user):
        async def run():
            thread = await sync_to_async(chat_services.get_or_create_thread)(
                actor=mentor_user,
                other=student_user,
            )
            communicator = WebsocketCommunicator(
                application,
                _ws_path(thread.public_id, mentor_user),
            )
            connected, _ = await communicator.connect()
            assert connected
            await communicator.receive_json_from()
            await communicator.send_json_to({"event": "ping"})
            pong = await communicator.receive_json_from()
            assert pong["event"] == "pong"
            await communicator.disconnect()

        _run(run)
