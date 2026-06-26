import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import CodingChallenge


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

    def test_create_and_update_coding_lesson(self, mentor_client, module):
        create = mentor_client.post(
            f"/api/mentoring/editor/modules/{module.public_id}/lessons/",
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

    def test_student_forbidden(self, student_user, course):
        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(
            f"/api/mentoring/editor/courses/{course.public_id}/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
