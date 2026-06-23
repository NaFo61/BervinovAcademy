import pytest
from rest_framework import status
from rest_framework.test import APIClient

from progress.models import LessonUserComment


@pytest.mark.django_db
class TestLessonUserCommentsApi:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_list_comments_public(self, client, student_user, radio_question):
        LessonUserComment.objects.create(
            user=student_user,
            lesson_kind="radio",
            lesson_public_id=radio_question.public_id,
            body="Полезный вопрос",
        )
        url = (
            f"/api/progress/lesson-comments/"
            f"?lesson_kind=radio&lesson={radio_question.public_id}"
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["body"] == "Полезный вопрос"

    def test_create_requires_auth(self, client, radio_question):
        response = client.post(
            "/api/progress/lesson-comments/",
            {
                "lesson_kind": "radio",
                "lesson_public_id": str(radio_question.public_id),
                "body": "Мой комментарий",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_comment(self, client, student_user, radio_question):
        client.force_authenticate(user=student_user)
        response = client.post(
            "/api/progress/lesson-comments/",
            {
                "lesson_kind": "radio",
                "lesson_public_id": str(radio_question.public_id),
                "body": "Не понял условие",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["body"] == "Не понял условие"
        assert response.data["is_mine"] is True
        assert LessonUserComment.objects.filter(user=student_user).count() == 1

    def test_delete_own_comment(self, client, student_user, radio_question):
        comment = LessonUserComment.objects.create(
            user=student_user,
            lesson_kind="radio",
            lesson_public_id=radio_question.public_id,
            body="Удалить меня",
        )
        client.force_authenticate(user=student_user)
        response = client.delete(
            f"/api/progress/lesson-comments/{comment.public_id}/"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LessonUserComment.objects.filter(pk=comment.pk).exists()
