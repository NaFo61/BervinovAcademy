import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import CodingChallenge, Course
from users.models import User


@pytest.mark.django_db
class TestContentEditorApi:
    @pytest.fixture
    def mentor_client(self, mentor_user):
        client = APIClient()
        client.force_authenticate(user=mentor_user)
        return client

    def test_course_outline(self, mentor_client, course, module):
        url = f"/api/mentoring/editor/courses/{course.public_id}/"
        response = mentor_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["public_id"] == str(course.public_id)
        assert len(response.data["modules"]) >= 1

    def test_create_module_and_lesson(self, mentor_client, course):
        create_mod = mentor_client.post(
            f"/api/mentoring/editor/courses/{course.public_id}/modules/",
            {"title": "Новый модуль"},
            format="json",
        )
        assert create_mod.status_code == status.HTTP_201_CREATED
        mid = create_mod.data["public_id"]

        create = mentor_client.post(
            f"/api/mentoring/editor/modules/{mid}/lessons/",
            {"kind": "coding", "title": "Editor task"},
            format="json",
        )
        assert create.status_code == status.HTTP_201_CREATED
        pid = create.data["public_id"]

        patch = mentor_client.patch(
            f"/api/mentoring/editor/lessons/coding/{pid}/",
            {
                "solution_text": "Разбор решения",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "Updated desc",
            },
            format="json",
        )
        assert patch.status_code == status.HTTP_200_OK
        assert patch.data["solution_text"] == "Разбор решения"
        assert (
            CodingChallenge.objects.get(public_id=pid).solution_text
            == "Разбор решения"
        )

        patch_prompt = mentor_client.patch(
            f"/api/mentoring/editor/lessons/coding/{pid}/",
            {"assistant_prompt": "Свой промпт {{condition}}"},
            format="json",
        )
        assert patch_prompt.status_code == status.HTTP_200_OK
        assert patch_prompt.data["assistant_prompt"] == (
            "Свой промпт {{condition}}"
        )
        assert (
            CodingChallenge.objects.get(public_id=pid).assistant_prompt
            == "Свой промпт {{condition}}"
        )

    def test_create_course_assigns_mentor(self, mentor_client, mentor_user):
        resp = mentor_client.post(
            "/api/mentoring/editor/courses/",
            {"title": "Мой курс", "description": "Desc"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        course = Course.objects.get(public_id=resp.data["public_id"])
        assert course.mentor_id == mentor_user.id

    def test_other_mentor_forbidden(self, course, module):
        other = User.objects.create_user(
            email="other-mentor@academy.com",
            phone="+79009998877",
            password="password",
            role="mentor",
        )
        client = APIClient()
        client.force_authenticate(user=other)
        response = client.get(
            f"/api/mentoring/editor/courses/{course.public_id}/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden(self, student_user, course):
        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(
            f"/api/mentoring/editor/courses/{course.public_id}/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mentor_has_no_django_staff(self, mentor_user):
        assert not mentor_user.is_staff
        assert not mentor_user.is_superuser
