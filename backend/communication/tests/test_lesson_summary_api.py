"""Tests for AI lesson summary and board assets API."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
import pytest
from rest_framework import status

from communication.models import (
    BoardAsset,
    Conference,
    ConferenceLessonSummary,
)


@pytest.mark.django_db
class TestLessonSummaryApi:
    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="testkey",
        LIVEKIT_API_SECRET="testsecret",
        CELERY_TASK_ALWAYS_EAGER=True,
        ASSISTANT_LLM_ENABLED=False,
    )
    def test_mentor_can_create_and_get_summary(
        self, mentor_client, mentor_user, student_user, monkeypatch
    ):
        def fake_process(summary_id):
            summary = ConferenceLessonSummary.objects.get(pk=summary_id)
            summary.transcript = "разобрали циклы"
            summary.summary_md = "- Циклы for/while\n- ДЗ: 3 задачи"
            summary.status = ConferenceLessonSummary.Status.READY
            summary.error_message = ""
            summary.save()

        monkeypatch.setattr(
            "communication.tasks.process_summary_record",
            fake_process,
        )

        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-summary-1",
            status=Conference.Status.ACTIVE,
        )
        audio = SimpleUploadedFile(
            "lesson.webm",
            b"fake-audio-bytes",
            content_type="audio/webm",
        )
        post = mentor_client.post(
            f"/api/communication/conferences/{conference.public_id}/lesson-summary/",
            {"audio": audio},
            format="multipart",
        )
        assert post.status_code == status.HTTP_202_ACCEPTED
        assert post.data["status"] == ConferenceLessonSummary.Status.READY
        assert "Циклы" in post.data["summary_md"]

        get_resp = mentor_client.get(
            f"/api/communication/conferences/{conference.public_id}/lesson-summary/",
        )
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.data["status"] == "ready"

        list_resp = mentor_client.get("/api/communication/conferences/")
        row = next(
            item
            for item in list_resp.data
            if item["public_id"] == str(conference.public_id)
        )
        assert row["has_lesson_summary"] is True
        assert row["lesson_summary_status"] == "ready"

    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="testkey",
        LIVEKIT_API_SECRET="testsecret",
    )
    def test_student_cannot_post_summary(
        self, student_client, mentor_user, student_user
    ):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-summary-deny",
            status=Conference.Status.ACTIVE,
        )
        audio = SimpleUploadedFile(
            "lesson.webm", b"x", content_type="audio/webm"
        )
        resp = student_client.post(
            f"/api/communication/conferences/{conference.public_id}/lesson-summary/",
            {"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="testkey",
        LIVEKIT_API_SECRET="testsecret",
    )
    def test_get_summary_404_when_missing(
        self, mentor_client, mentor_user, student_user
    ):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-summary-missing",
            status=Conference.Status.COMPLETED,
        )
        resp = mentor_client.get(
            f"/api/communication/conferences/{conference.public_id}/lesson-summary/",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_post_summary_requires_audio(
        self, mentor_client, mentor_user, student_user
    ):
        conference = Conference.objects.create(
            mentor=mentor_user,
            guest=student_user,
            room_name="room-summary-no-audio",
            status=Conference.Status.ACTIVE,
        )
        resp = mentor_client.post(
            f"/api/communication/conferences/{conference.public_id}/lesson-summary/",
            {},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBoardAssetApi:
    def test_upload_board_asset(self, student_client, student_user):
        upload = SimpleUploadedFile(
            "scheme.png",
            b"\x89PNG\r\n\x1a\n",
            content_type="image/png",
        )
        resp = student_client.post(
            "/api/communication/board-assets/",
            {"file": upload},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["url"]
        assert resp.data["original_name"] == "scheme.png"
        assert BoardAsset.objects.filter(uploaded_by=student_user).count() == 1

    def test_reject_oversized(self, student_client, settings):
        settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
        big = SimpleUploadedFile(
            "big.pdf",
            b"x" * (20 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )
        resp = student_client.post(
            "/api/communication/board-assets/",
            {"file": big},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_forbidden_extension(self, student_client):
        upload = SimpleUploadedFile(
            "malware.exe",
            b"MZ",
            content_type="application/octet-stream",
        )
        resp = student_client.post(
            "/api/communication/board-assets/",
            {"file": upload},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_rejected(self):
        from rest_framework.test import APIClient

        client = APIClient()
        upload = SimpleUploadedFile("a.png", b"x", content_type="image/png")
        resp = client.post(
            "/api/communication/board-assets/",
            {"file": upload},
            format="multipart",
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
