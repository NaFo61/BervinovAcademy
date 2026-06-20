"""Tests for conference whiteboard API."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from communication.models import Conference, ConferenceWhiteboard
from communication.whiteboard_tokens import (
    issue_whiteboard_sync_token,
    verify_whiteboard_sync_token,
)
from users.models import User


@pytest.mark.django_db
class TestWhiteboardTokens:
    @override_settings(WHITEBOARD_SYNC_SECRET="test-whiteboard-secret")
    def test_issue_and_verify(self, mentor_user, student_user):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-token-test",
        )
        token = issue_whiteboard_sync_token(
            conference.public_id,
            mentor_user.public_id,
            ttl_seconds=600,
        )
        payload = verify_whiteboard_sync_token(token, conference.public_id)
        assert payload is not None
        assert payload["sub"] == str(mentor_user.public_id)

    @override_settings(WHITEBOARD_SYNC_SECRET="test-whiteboard-secret")
    def test_wrong_room_rejected(self, mentor_user, student_user):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-token-test-2",
        )
        token = issue_whiteboard_sync_token(
            conference.public_id,
            mentor_user.public_id,
        )
        assert (
            verify_whiteboard_sync_token(
                token, "00000000-0000-0000-0000-000000000000"
            )
            is None
        )


@pytest.mark.django_db
class TestWhiteboardApi:
    @override_settings(
        **{
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "testkey",
            "LIVEKIT_API_SECRET": "testsecret",
            "WHITEBOARD_SYNC_SECRET": "test-whiteboard-secret",
        }
    )
    def test_whiteboard_token_for_participant(
        self, mentor_client, student_client, mentor_user, student_user
    ):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]

        mentor_token = mentor_client.post(
            f"/api/communication/conferences/{conf_id}/whiteboard/token/",
        )
        assert mentor_token.status_code == status.HTTP_200_OK
        assert mentor_token.data["token"]
        assert mentor_token.data["room_id"] == conf_id

        student_token = student_client.post(
            f"/api/communication/conferences/{conf_id}/whiteboard/token/",
        )
        assert student_token.status_code == status.HTTP_200_OK

    @override_settings(
        **{
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "testkey",
            "LIVEKIT_API_SECRET": "testsecret",
        }
    )
    def test_export_whiteboard_png(
        self, mentor_client, student_user, mentor_user
    ):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-export-test",
            status=Conference.Status.ACTIVE,
        )
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload = SimpleUploadedFile(
            "board.png",
            png_bytes,
            content_type="image/png",
        )
        resp = mentor_client.post(
            f"/api/communication/conferences/{conference.public_id}/whiteboard/export/",
            {"image": upload},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["image_url"]
        assert (
            ConferenceWhiteboard.objects.filter(conference=conference).count()
            == 1
        )

        get_resp = mentor_client.get(
            f"/api/communication/conferences/{conference.public_id}/whiteboard/",
        )
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.data["image_url"]

    def test_export_requires_access(self, mentor_user, student_user):
        outsider = User.objects.create_user(
            email="outsider-wb@academy.com",
            phone="+79009990099",
            password="password",
            first_name="Out",
            last_name="Side",
            role="student",
        )
        client = APIClient()
        client.force_authenticate(user=outsider)
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-export-deny",
            status=Conference.Status.ACTIVE,
        )
        png = SimpleUploadedFile(
            "board.png", b"fake", content_type="image/png"
        )
        resp = client.post(
            f"/api/communication/conferences/{conference.public_id}/whiteboard/export/",
            {"image": png},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(
        **{
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "testkey",
            "LIVEKIT_API_SECRET": "testsecret",
        }
    )
    def test_conference_list_has_whiteboard_flag(
        self, mentor_client, mentor_user, student_user
    ):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-list-wb",
            status=Conference.Status.COMPLETED,
        )
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        ConferenceWhiteboard.objects.create(
            conference=conference,
            image=SimpleUploadedFile(
                "board.png", png_bytes, content_type="image/png"
            ),
            exported_by=mentor_user,
        )

        resp = mentor_client.get("/api/communication/conferences/")
        assert resp.status_code == status.HTTP_200_OK
        row = next(
            item
            for item in resp.data
            if item["public_id"] == str(conference.public_id)
        )
        assert row["has_whiteboard"] is True
        assert row["whiteboard_exported_at"] is not None
