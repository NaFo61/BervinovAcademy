"""Tests for conference API."""

from django.test import override_settings
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from communication.models import Conference, UserNotification
from users.models import User


@pytest.fixture
def mentor_user(db):
    return User.objects.create_user(
        email="mentor-conf@academy.com",
        phone="+79001110001",
        password="password",
        first_name="Ментор",
        last_name="Созвон",
        role="mentor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student-conf@academy.com",
        phone="+79001110002",
        password="password",
        first_name="Студент",
        last_name="Созвон",
        role="student",
    )


@pytest.fixture
def mentor_client(mentor_user):
    client = APIClient()
    client.force_authenticate(user=mentor_user)
    return client


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


LIVEKIT_SETTINGS = {
    "LIVEKIT_URL": "wss://test.livekit.cloud",
    "LIVEKIT_API_KEY": "testkey",
    "LIVEKIT_API_SECRET": "testsecret",
}


@pytest.mark.django_db
class TestConferenceApi:
    def test_student_cannot_create(self, student_client, student_user):
        resp = student_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_mentor_creates_conference(
        self, mentor_client, mentor_user, student_user
    ):
        resp = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["status"] == "waiting"
        assert resp.data["guest"]["public_id"] == str(student_user.public_id)
        assert Conference.objects.count() == 1
        assert UserNotification.objects.filter(user=student_user).count() == 1

    def test_cannot_call_self(self, mentor_client, mentor_user):
        resp = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(mentor_user.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @override_settings(**LIVEKIT_SETTINGS)
    def test_join_issues_token(
        self, mentor_client, student_client, mentor_user, student_user
    ):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        join = mentor_client.post(
            f"/api/communication/conferences/{conf_id}/join/",
        )
        assert join.status_code == status.HTTP_200_OK
        assert join.data["token"]
        assert join.data["livekit_url"] == LIVEKIT_SETTINGS["LIVEKIT_URL"]

        guest_join = student_client.post(
            f"/api/communication/conferences/{conf_id}/join/",
        )
        assert guest_join.status_code == status.HTTP_200_OK
        conf = Conference.objects.get(public_id=conf_id)
        assert conf.status == Conference.Status.ACTIVE

    def test_guest_declines(self, mentor_client, student_client, student_user):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        resp = student_client.post(
            f"/api/communication/conferences/{conf_id}/decline/",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "declined"

    def test_conference_history(
        self, mentor_client, student_client, student_user
    ):
        mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        mentor_list = mentor_client.get("/api/communication/conferences/")
        student_list = student_client.get("/api/communication/conferences/")
        assert mentor_list.status_code == status.HTTP_200_OK
        assert student_list.status_code == status.HTTP_200_OK
        assert len(mentor_list.data) >= 1
        assert len(student_list.data) >= 1

    def test_user_search_requires_mentor(self, student_client):
        resp = student_client.get("/api/communication/users/search/?q=student")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_notifications_list(
        self, mentor_client, student_client, student_user
    ):
        mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        resp = student_client.get("/api/communication/notifications/?unread=1")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1
        assert resp.data[0]["kind"] == "conference_invite"
