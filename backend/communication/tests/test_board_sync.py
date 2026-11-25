"""Общая доска: снимок и живые штрихи двоих людей."""

from urllib.parse import quote

from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from school_platform.asgi import application

from communication.models import UserBoard


def _ws_path(owner, actor):
    token = str(AccessToken.for_user(actor))
    return f"/ws/whiteboard/{owner.public_id}/?token={quote(token, safe='')}"


def _run(coro):
    return async_to_sync(coro)()


def _stroke(item_id="stroke01"):
    return {
        "id": item_id,
        "type": "stroke",
        "color": "#0B1226",
        "size": 5,
        "points": [[10, 10], [40, 30]],
    }


@override_settings(WHITEBOARD_ENABLED=True)
def test_two_people_see_the_same_stroke(mentor_user, student_user):
    async def run():
        student = WebsocketCommunicator(
            application, _ws_path(student_user, student_user)
        )
        mentor = WebsocketCommunicator(
            application, _ws_path(student_user, mentor_user)
        )
        student_ok, _ = await student.connect()
        mentor_ok, _ = await mentor.connect()
        assert student_ok
        assert mentor_ok
        hello = await student.receive_json_from()
        await mentor.receive_json_from()
        assert hello["event"] == "hello"
        assert hello["payload"]["document"]["kind"] == "academy-board"

        await student.send_json_to(
            {
                "event": "commit",
                "payload": {"client": "tab-student", "item": _stroke()},
            }
        )
        own = await student.receive_json_from()
        peer = await mentor.receive_json_from()
        assert own["event"] == "commit"
        assert peer["event"] == "commit"
        assert peer["payload"]["item"]["id"] == "stroke01"
        assert peer["payload"]["revision"] == 1

        await mentor.send_json_to(
            {
                "event": "remove",
                "payload": {"client": "tab-mentor", "ids": ["stroke01"]},
            }
        )
        removed_for_student = await student.receive_json_from()
        await mentor.receive_json_from()
        assert removed_for_student["event"] == "remove"
        assert removed_for_student["payload"]["ids"] == ["stroke01"]

        board = await sync_to_async(UserBoard.objects.get)(owner=student_user)
        assert board.snapshot_json["items"] == []
        assert board.snapshot_json["revision"] == 2

        await student.disconnect()
        await mentor.disconnect()

    _run(run)


@override_settings(WHITEBOARD_ENABLED=True)
def test_student_cannot_join_other_board(mentor_user, student_user):
    async def run():
        communicator = WebsocketCommunicator(
            application, _ws_path(mentor_user, student_user)
        )
        connected, _ = await communicator.connect()
        assert not connected

    _run(run)


@override_settings(WHITEBOARD_ENABLED=True)
def test_snapshot_put_keeps_both_formats(
    student_client, student_user, mentor_client
):
    tldraw = {"document": {"store": {"shape:1": {}}}, "session": {}}
    snap_url = (
        "/api/communication/whiteboard/users/"
        f"{student_user.public_id}/snapshot/"
    )
    saved = student_client.put(snap_url, {"snapshot": tldraw}, format="json")
    assert saved.status_code == status.HTTP_200_OK

    academy = {
        "kind": "academy-board",
        "version": 1,
        "revision": 0,
        "items": [_stroke("stroke99")],
    }
    drawn = student_client.put(
        snap_url,
        {"snapshot": academy, "base_revision": 0},
        format="json",
    )
    assert drawn.status_code == status.HTTP_200_OK
    board = UserBoard.objects.get(owner=student_user)
    assert board.snapshot_json["document"]["store"]["shape:1"] == {}
    assert board.snapshot_json["academy_board"]["items"][0]["id"] == "stroke99"

    overwritten = student_client.put(
        snap_url, {"snapshot": tldraw}, format="json"
    )
    assert overwritten.status_code == status.HTTP_200_OK
    board.refresh_from_db()
    assert board.snapshot_json["academy_board"]["items"][0]["id"] == "stroke99"
    assert board.snapshot_json["document"]["store"]["shape:1"] == {}

    token_url = (
        "/api/communication/whiteboard/users/"
        f"{student_user.public_id}/token/"
    )
    opened = mentor_client.post(token_url)
    assert opened.status_code == status.HTTP_200_OK
    assert (
        opened.data["snapshot"]["academy_board"]["items"][0]["id"]
        == "stroke99"
    )


@override_settings(WHITEBOARD_ENABLED=True)
def test_stale_put_does_not_drop_newer_stroke(student_client, student_user):
    snap_url = (
        "/api/communication/whiteboard/users/"
        f"{student_user.public_id}/snapshot/"
    )
    first = {
        "kind": "academy-board",
        "version": 1,
        "revision": 0,
        "items": [_stroke("stroke-a")],
    }
    assert (
        student_client.put(
            snap_url,
            {"snapshot": first, "base_revision": 0},
            format="json",
        ).status_code
        == status.HTTP_200_OK
    )
    stale = {
        "kind": "academy-board",
        "version": 1,
        "revision": 0,
        "items": [_stroke("stroke-b")],
    }
    resp = student_client.put(
        snap_url,
        {"snapshot": stale, "base_revision": 0},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    board = UserBoard.objects.get(owner=student_user)
    ids = [item["id"] for item in board.snapshot_json["items"]]
    assert ids == ["stroke-a", "stroke-b"]


def _snap_url(user):
    return "/api/communication/whiteboard/users/" f"{user.public_id}/snapshot/"


def _put_board(client, user, items, base, removed=None):
    body = {
        "snapshot": {
            "kind": "academy-board",
            "version": 1,
            "revision": base,
            "items": items,
        },
        "base_revision": base,
        "removed_ids": removed or [],
    }
    return client.put(_snap_url(user), body, format="json")


@override_settings(WHITEBOARD_ENABLED=True)
def test_put_keeps_stroke_the_client_never_saw(student_client, student_user):
    """Копия с той же версией не должна стирать чужой штрих."""
    first = _put_board(student_client, student_user, [_stroke("stroke-a")], 0)
    assert first.status_code == status.HTTP_200_OK
    board = UserBoard.objects.get(owner=student_user)
    revision = board.snapshot_json["revision"]
    second = _put_board(
        student_client,
        student_user,
        [_stroke("stroke-b")],
        revision,
    )
    assert second.status_code == status.HTTP_200_OK
    board.refresh_from_db()
    ids = [item["id"] for item in board.snapshot_json["items"]]
    assert ids == ["stroke-a", "stroke-b"]


@override_settings(WHITEBOARD_ENABLED=True)
def test_removed_ids_do_not_come_back(student_client, student_user):
    saved = _put_board(
        student_client,
        student_user,
        [_stroke("stroke-a"), _stroke("stroke-b")],
        0,
    )
    assert saved.status_code == status.HTTP_200_OK
    board = UserBoard.objects.get(owner=student_user)
    revision = board.snapshot_json["revision"]
    erased = _put_board(
        student_client,
        student_user,
        [_stroke("stroke-a")],
        revision,
        removed=["stroke-b"],
    )
    assert erased.status_code == status.HTTP_200_OK
    board.refresh_from_db()
    ids = [item["id"] for item in board.snapshot_json["items"]]
    assert ids == ["stroke-a"]

    stale = _put_board(
        student_client,
        student_user,
        [_stroke("stroke-a"), _stroke("stroke-b")],
        0,
    )
    assert stale.status_code == status.HTTP_200_OK
    board.refresh_from_db()
    ids = [item["id"] for item in board.snapshot_json["items"]]
    assert ids == ["stroke-a"]


@override_settings(WHITEBOARD_ENABLED=True)
def test_erased_stroke_is_not_drawn_again(student_user):
    async def run():
        student = WebsocketCommunicator(
            application, _ws_path(student_user, student_user)
        )
        connected, _ = await student.connect()
        assert connected
        await student.receive_json_from()
        await student.send_json_to(
            {
                "event": "remove",
                "payload": {"client": "tab-student", "ids": ["stroke01"]},
            }
        )
        removed = await student.receive_json_from()
        assert removed["event"] == "remove"
        await student.send_json_to(
            {
                "event": "commit",
                "payload": {"client": "tab-student", "item": _stroke()},
            }
        )
        again = await student.receive_json_from()
        assert again["event"] == "remove"
        assert again["payload"]["ids"] == ["stroke01"]
        board = await sync_to_async(UserBoard.objects.get)(owner=student_user)
        assert board.snapshot_json["items"] == []
        await student.disconnect()

    _run(run)


@override_settings(WHITEBOARD_ENABLED=True)
def test_far_stroke_and_picture_fit_on_the_canvas(
    student_client, student_user
):
    stroke = _stroke("strokefar")
    stroke["points"] = [[-40000, 250000], [80000, -10]]
    picture = {
        "id": "imagefar01",
        "type": "image",
        "src": "/media/board.png",
        "x": -12000,
        "y": 90000,
        "w": 320,
        "h": 180,
    }
    saved = _put_board(student_client, student_user, [stroke, picture], 0)
    assert saved.status_code == status.HTTP_200_OK
    board = UserBoard.objects.get(owner=student_user)
    stored = {item["id"]: item for item in board.snapshot_json["items"]}
    assert stored["strokefar"]["points"][0] == [-40000, 250000]
    assert stored["imagefar01"]["x"] == -12000

    outside = _stroke("strokeout")
    outside["points"] = [[10_000_000, 0], [0, 0]]
    rejected = _put_board(
        student_client,
        student_user,
        [outside],
        board.snapshot_json["revision"],
    )
    assert rejected.status_code == status.HTTP_400_BAD_REQUEST
