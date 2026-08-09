"""Тесты назначения ментора и ИИ-помощника."""

import pytest
from rest_framework.test import APIClient

from mentoring.assignment import resolve_student_mentor
from users.models import Student, User


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin-assign@academy.com",
        phone="+79001110010",
        password="password",
        first_name="Админ",
        last_name="Школы",
        role="admin",
    )


@pytest.fixture
def mentor_user(db):
    return User.objects.create_user(
        email="mentor-assign@academy.com",
        phone="+79001110011",
        password="password",
        first_name="Ментор",
        last_name="А",
        role="mentor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student-assign@academy.com",
        phone="+79001110012",
        password="password",
        first_name="Ученик",
        last_name="Б",
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


@pytest.mark.django_db
class TestMentorAssignment:
    def test_resolve_falls_back_to_admin(self, student_user, admin_user):
        mentor, source = resolve_student_mentor(student_user)
        assert mentor is not None
        assert mentor.pk == admin_user.pk
        assert source == "default_admin"

    def test_resolve_prefers_assigned(
        self, student_user, mentor_user, admin_user
    ):
        Student.objects.create(user=student_user, assigned_mentor=mentor_user)
        mentor, source = resolve_student_mentor(student_user)
        assert mentor.pk == mentor_user.pk
        assert source == "assigned"

    def test_assign_api(self, mentor_client, student_user, mentor_user):
        resp = mentor_client.post(
            f"/api/mentoring/students/{student_user.public_id}/assign-mentor/",
            {"mentor_public_id": str(mentor_user.public_id)},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["source"] == "assigned"
        assert resp.data["assigned_mentor"]["public_id"] == str(
            mentor_user.public_id
        )
        profile = Student.objects.get(user=student_user)
        assert profile.assigned_mentor_id == mentor_user.pk

    def test_my_mentor(self, student_client, student_user, admin_user):
        resp = student_client.get("/api/mentoring/my-mentor/")
        assert resp.status_code == 200
        assert resp.data["source"] == "default_admin"
        assert resp.data["mentor"]["public_id"] == str(admin_user.public_id)

    def test_open_assigned_thread_without_pro(
        self, student_client, student_user, mentor_user, admin_user
    ):
        Student.objects.create(user=student_user, assigned_mentor=mentor_user)
        resp = student_client.get(
            "/api/communication/chat/threads/open/",
            {"assigned": "1"},
        )
        assert resp.status_code == 200
        assert resp.data["mentor"]["public_id"] == str(mentor_user.public_id)
        assert resp.data["student"]["public_id"] == str(student_user.public_id)


@pytest.mark.django_db
class TestAssistantChat:
    def test_mock_reply_includes_context(self, student_client):
        resp = student_client.post(
            "/api/mentoring/assistant/chat/",
            {
                "message": "С чего начать?",
                "history": [],
                "context": {
                    "course_title": "ЕГЭ",
                    "lesson_kind": "coding",
                    "lesson_title": "Сумма чисел",
                    "lesson_statement": "Считайте два числа и выведите сумму.",
                },
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["mode"] == "mock"
        assert "Сумма чисел" in resp.data["reply"]
        assert "С чего начать?" in resp.data["reply"]
