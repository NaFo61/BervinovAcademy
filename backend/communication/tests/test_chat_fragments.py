"""Chat fragments: media security, edit/delete/forward ACL, code."""

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from rest_framework import status

from communication.models import ChatMessage, ChatMessageAttachment

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
    b"\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _open_thread(client, peer_public_id):
    resp = client.get(
        "/api/communication/chat/threads/open/",
        {"user": str(peer_public_id)},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.data["public_id"]


@pytest.mark.django_db
class TestChatCodeFragment:
    def test_code_always_python_language(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {
                "kind": "code",
                "body": "def f():\n    return 1\n",
                "code_language": "javascript",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["kind"] == "code"
        assert resp.data["code_language"] == "python"

    def test_empty_code_rejected(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"kind": "code", "body": "   "},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChatMediaSecurity:
    def test_png_saved_with_safe_extension(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        spoofed = SimpleUploadedFile(
            "evil.html",
            TINY_PNG,
            content_type="text/html",
        )
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"files": spoofed},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["kind"] == "image"
        url = resp.data["attachments"][0]["url"]
        assert url.endswith(".png") or ".png" in url
        assert ".html" not in url
        att = ChatMessageAttachment.objects.get()
        assert att.file.name.endswith(".png")

    def test_html_payload_rejected(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        html = SimpleUploadedFile(
            "page.html",
            b"<!DOCTYPE html><script>alert(1)</script>",
            content_type="image/jpeg",
        )
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"files": html},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert ChatMessage.objects.filter(kind="image").count() == 0

    def test_svg_rejected(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        svg = SimpleUploadedFile(
            "x.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>',
            content_type="image/svg+xml",
        )
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"files": svg},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_album_max_files(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        files = [
            SimpleUploadedFile(f"a{i}.png", TINY_PNG, content_type="image/png")
            for i in range(11)
        ]
        resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"files": files},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChatReplyForwardAcl:
    def test_reply_cross_thread_blocked(
        self, mentor_client, student_user, mentor_user
    ):
        t1 = _open_thread(mentor_client, student_user.public_id)
        msg = mentor_client.post(
            f"/api/communication/chat/threads/{t1}/messages/",
            {"body": "в первом"},
            format="json",
        )
        assert msg.status_code == 201

        other = student_user.__class__.objects.create_user(
            email="peer2@example.com",
            password="pass12345",
            role="student",
        )
        t2 = _open_thread(mentor_client, other.public_id)
        bad = mentor_client.post(
            f"/api/communication/chat/threads/{t2}/messages/",
            {"body": "ответ", "reply_to": msg.data["public_id"]},
            format="json",
        )
        assert bad.status_code == status.HTTP_400_BAD_REQUEST

    def test_outsider_cannot_edit_or_delete(
        self, mentor_client, student_client, student_user, mentor_user
    ):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        created = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "только ментор"},
            format="json",
        )
        mid = created.data["public_id"]

        outsider = student_user.__class__.objects.create_user(
            email="outsider@example.com",
            password="pass12345",
            role="student",
        )
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        from users.serializers import inject_access_claims

        client = APIClient()
        refresh = RefreshToken.for_user(outsider)
        access = refresh.access_token
        inject_access_claims(access, outsider)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        patch = client.patch(
            f"/api/communication/chat/messages/{mid}/",
            {"body": "взлом"},
            format="json",
        )
        assert patch.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

        delete = client.delete(f"/api/communication/chat/messages/{mid}/")
        assert delete.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_owner_edit_delete_text(self, mentor_client, student_user):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        created = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "черновик"},
            format="json",
        )
        mid = created.data["public_id"]

        edited = mentor_client.patch(
            f"/api/communication/chat/messages/{mid}/",
            {"body": "готово"},
            format="json",
        )
        assert edited.status_code == 200
        assert edited.data["body"] == "готово"

        deleted = mentor_client.delete(
            f"/api/communication/chat/messages/{mid}/"
        )
        assert deleted.status_code == 200
        assert deleted.data["is_deleted"] is True

    def test_forward_album_copies_attachments(
        self, mentor_client, student_user
    ):
        t1 = _open_thread(mentor_client, student_user.public_id)
        album = mentor_client.post(
            f"/api/communication/chat/threads/{t1}/messages/",
            {
                "body": "два фото",
                "files": [
                    SimpleUploadedFile(
                        "a.png", TINY_PNG, content_type="image/png"
                    ),
                    SimpleUploadedFile(
                        "b.png", TINY_PNG, content_type="image/png"
                    ),
                ],
            },
            format="multipart",
        )
        assert album.status_code == 201
        assert album.data["kind"] == "album"

        other = student_user.__class__.objects.create_user(
            email="fwd-peer@example.com",
            password="pass12345",
            role="student",
        )
        t2 = _open_thread(mentor_client, other.public_id)
        fwd = mentor_client.post(
            f"/api/communication/chat/messages/{album.data['public_id']}/forward/",
            {"thread": t2},
            format="json",
        )
        assert fwd.status_code == 201
        assert fwd.data["kind"] == "album"
        assert len(fwd.data["attachments"]) == 2
        assert (
            fwd.data["forwarded_from"]["public_id"] == album.data["public_id"]
        )

    def test_student_is_mine_false_for_peer_message(
        self, mentor_client, student_client, student_user
    ):
        thread_id = _open_thread(mentor_client, student_user.public_id)
        created = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "от ментора"},
            format="json",
        )
        listed = student_client.get(
            f"/api/communication/chat/threads/{thread_id}/messages/"
        )
        assert listed.status_code == 200
        row = next(
            m
            for m in listed.data["results"]
            if m["public_id"] == created.data["public_id"]
        )
        assert row["is_mine"] is False
