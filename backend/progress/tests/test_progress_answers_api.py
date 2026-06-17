import uuid

from django.urls import resolve
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from progress.models import CodeSubmission, UserAnswerCheckBox, UserAnswerRadio


@pytest.mark.django_db
class TestProgressAnswersRouting:
    def test_resolves_radio_collection(self):
        match = resolve("/api/progress/radio/")
        assert match.url_name == "answers-radio-list"

    def test_resolves_radio_detail(self):
        pid = str(uuid.uuid4())
        match = resolve(f"/api/progress/radio/{pid}/")
        assert match.url_name == "answers-radio-detail"

    def test_resolves_checkbox_collection(self):
        match = resolve("/api/progress/checkbox/")
        assert match.url_name == "answers-checkbox-list"

    def test_resolves_code_collection(self):
        match = resolve("/api/progress/code/")
        assert match.url_name == "answers-code-list"

    def test_resolves_theory_collection(self):
        match = resolve("/api/progress/theory/")
        assert match.url_name == "reads-theory-list"


@pytest.mark.django_db
class TestProgressAnswersUnauthenticated:
    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.mark.parametrize(
        "path",
        [
            "/api/progress/radio/",
            "/api/progress/checkbox/",
            "/api/progress/code/",
            "/api/progress/theory/",
        ],
    )
    def test_list_requires_auth(self, client, path):
        response = client.get(path)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProgressAnswersAuthenticated:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_post_theory_creates_read(self, client, theory_lesson):
        resp = client.post(
            "/api/progress/theory/",
            {"lesson": str(theory_lesson.public_id)},
            format="json",
        )
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        )

    def test_post_radio_creates_answer(
        self, client, student_user, radio_question, radio_answers
    ):
        correct = next(a for a in radio_answers if a.is_correct)
        payload = {
            "question": str(radio_question.public_id),
            "selected_answer": str(correct.public_id),
        }
        response = client.post("/api/progress/radio/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_correct"] is True
        assert response.data["solved_ever"] is True
        assert set(response.data.keys()) == {
            "public_id",
            "question",
            "question_title",
            "selected_answer",
            "selected_answer_text",
            "is_correct",
            "points_earned",
            "solved_ever",
            "created_at",
        }
        assert UserAnswerRadio.objects.filter(user=student_user).count() == 1

    def test_post_radio_second_attempt_solved_ever(
        self, client, student_user, radio_question, radio_answers
    ):
        wrong = next(a for a in radio_answers if not a.is_correct)
        correct = next(a for a in radio_answers if a.is_correct)
        base = {
            "question": str(radio_question.public_id),
        }
        r1 = client.post(
            "/api/progress/radio/",
            {**base, "selected_answer": str(wrong.public_id)},
            format="json",
        )
        assert r1.status_code == status.HTTP_201_CREATED
        assert r1.data["is_correct"] is False
        assert r1.data["solved_ever"] is False

        r2 = client.post(
            "/api/progress/radio/",
            {**base, "selected_answer": str(correct.public_id)},
            format="json",
        )
        assert r2.status_code == status.HTTP_201_CREATED
        assert r2.data["is_correct"] is True
        assert r2.data["solved_ever"] is True

        assert UserAnswerRadio.objects.filter(user=student_user).count() == 2
        list_resp = client.get("/api/progress/radio/")
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.data) == 2
        assert all(row["solved_ever"] is True for row in list_resp.data)

    def test_post_checkbox_creates_answer(
        self, client, student_user, checkbox_question, checkbox_answers
    ):
        evens = [
            str(a.public_id) for a in checkbox_answers if a.text in ("2", "4")
        ]
        payload = {
            "question": str(checkbox_question.public_id),
            "selected_answers": evens,
        }
        response = client.post(
            "/api/progress/checkbox/",
            payload,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert set(response.data.keys()) == {
            "public_id",
            "question",
            "question_title",
            "selected_answers",
            "selected_answers_text",
            "is_correct",
            "points_earned",
            "created_at",
            "saved",
        }
        assert (
            UserAnswerCheckBox.objects.filter(user=student_user).count() == 1
        )

    def test_post_checkbox_empty_selected_answers(
        self, client, student_user, checkbox_question
    ):
        payload = {
            "question": str(checkbox_question.public_id),
            "selected_answers": [],
        }
        response = client.post(
            "/api/progress/checkbox/",
            payload,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["selected_answers"] == []
        assert response.data["selected_answers_text"] == []
        assert response.data["is_correct"] is False
        assert response.data["points_earned"] == 0
        assert response.data["saved"] is False
        assert (
            UserAnswerCheckBox.objects.filter(user=student_user).count() == 0
        )

    def test_post_code_creates_submission(
        self, client, student_user, coding_challenge
    ):
        payload = {
            "challenge": str(coding_challenge.public_id),
            "code": "print('ok')",
        }
        response = client.post("/api/progress/code/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert set(response.data.keys()) == {
            "public_id",
            "challenge_public_id",
            "challenge_title",
            "code",
            "status",
            "tests_passed",
            "total_tests",
            "error_message",
            "failed_test_number",
            "actual_output",
            "expected_output",
            "submitted_at",
            "completed_at",
        }
        assert CodeSubmission.objects.filter(user=student_user).count() == 1

    def test_code_list_filter_by_challenge_public_id(
        self, client, student_user, coding_challenge
    ):
        CodeSubmission.objects.create(
            user=student_user,
            challenge=coding_challenge,
            code="x",
            status="pending",
        )
        url = (
            f"/api/progress/code/?challenge_public_id="
            f"{coding_challenge.public_id}"
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
