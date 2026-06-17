import pytest
from rest_framework import status
from rest_framework.test import APIClient

from education.models import Enrollment
from progress.models import CodeSubmission, UserAnswerRadio
from users.models import User

pytest_plugins = (
    "content.tests.conftest",
    "progress.tests.conftest",
)


@pytest.fixture
def mentor_user(db):
    return User.objects.create_user(
        email="mentor-panel@academy.com",
        phone="+79001112233",
        password="password",
        first_name="Ментор",
        last_name="Тестов",
        role="mentor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student-panel@academy.com",
        phone="+79004445566",
        password="password",
        first_name="Студент",
        last_name="Тестов",
        role="student",
    )


@pytest.mark.django_db
class TestMentorApiAccess:
    @pytest.fixture
    def mentor_client(self, mentor_user):
        c = APIClient()
        c.force_authenticate(user=mentor_user)
        return c

    @pytest.fixture
    def student_client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_student_forbidden(self, student_client):
        resp = student_client.get("/api/mentoring/courses/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_mentor_courses_overview(
        self, mentor_client, course, student_user
    ):
        Enrollment.objects.create(user=student_user, course=course)
        resp = mentor_client.get("/api/mentoring/courses/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 1
        row = next(
            r
            for r in resp.data
            if r["course_public_id"] == str(course.public_id)
        )
        assert row["students_count"] == 1

    def test_mentor_sees_code_submission(
        self, mentor_client, student_user, coding_challenge
    ):
        CodeSubmission.objects.create(
            user=student_user,
            challenge=coding_challenge,
            code="print(42)",
            status="completed",
            tests_passed=1,
            total_tests=1,
        )
        resp = mentor_client.get("/api/mentoring/code-submissions/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data[0]["code"] == "print(42)"
        assert resp.data[0]["student"]["public_id"] == str(
            student_user.public_id
        )

    def test_mentor_sees_quiz_answer(
        self, mentor_client, student_user, radio_question, radio_answers
    ):
        correct = next(a for a in radio_answers if a.is_correct)
        UserAnswerRadio.objects.create(
            user=student_user,
            question=radio_question,
            selected_answer=correct,
            is_correct=True,
            points_earned=1,
        )
        resp = mentor_client.get("/api/mentoring/quiz-answers/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data[0]["kind"] == "radio"
        assert resp.data[0]["is_correct"] is True
