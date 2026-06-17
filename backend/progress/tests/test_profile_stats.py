import pytest
from rest_framework import status
from rest_framework.test import APIClient

from progress.models import Achievement, UserAchievement, UserAnswerRadio


@pytest.mark.django_db
class TestProfileProgressApi:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_me_includes_progress_and_achievements(self, client):
        resp = client.get("/api/users/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert "progress" in resp.data
        assert resp.data["progress"]["tasks_solved"] == 0
        assert "achievements" in resp.data
        assert "items" in resp.data["achievements"]
        assert resp.data["achievements"]["total_count"] >= 1

    def test_correct_radio_unlocks_first_task_achievement(
        self, client, student_user, radio_question, radio_answers
    ):
        correct = next(a for a in radio_answers if a.is_correct)
        client.post(
            "/api/progress/radio/",
            {
                "question": str(radio_question.public_id),
                "selected_answer": str(correct.public_id),
            },
            format="json",
        )
        resp = client.get("/api/users/me/")
        assert resp.data["progress"]["tasks_solved"] == 1
        first = Achievement.objects.get(code="tasks_1")
        assert UserAchievement.objects.filter(
            user=student_user, achievement=first
        ).exists()
        unlocked = [
            item
            for item in resp.data["achievements"]["items"]
            if item["unlocked"]
        ]
        codes = {item["code"] for item in unlocked}
        assert "tasks_1" in codes

    def test_wrong_radio_does_not_count_as_solved(
        self, client, student_user, radio_question, radio_answers
    ):
        wrong = next(a for a in radio_answers if not a.is_correct)
        client.post(
            "/api/progress/radio/",
            {
                "question": str(radio_question.public_id),
                "selected_answer": str(wrong.public_id),
            },
            format="json",
        )
        resp = client.get("/api/users/me/")
        assert resp.data["progress"]["tasks_solved"] == 0
        assert UserAnswerRadio.objects.filter(user=student_user).count() == 1
