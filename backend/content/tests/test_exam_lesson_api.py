"""Update exam lesson API expectations: auth + enrollment required."""

import pytest
from rest_framework.test import APIClient

from content.models import (
    Course,
    Exam,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
)
from education.models import Enrollment
from users.models import User


@pytest.fixture
def exam_with_lessons(db):
    course = Course.objects.create(
        title="Курс с КР",
        slug="exam-lessons-api",
        description="",
        is_active=True,
    )
    exam = Exam.objects.create(
        course=course,
        title="КР тест",
        duration_minutes=45,
        is_active=True,
    )
    theory = LessonTheory.objects.create(
        exam=exam,
        title="Теория КР",
        content="<p>Текст</p>",
        order_index=1,
    )
    radio = LessonRadioQuestion.objects.create(
        exam=exam,
        title="Radio КР",
        question_text="1+1?",
        points=5,
        order_index=2,
    )
    RadioAnswerOption.objects.create(
        question=radio, text="2", is_correct=True, order_index=1
    )
    checkbox = LessonCheckBoxQuestion.objects.create(
        exam=exam,
        title="Checkbox КР",
        question_text="Чётные?",
        points=5,
        order_index=3,
    )
    return {
        "course": course,
        "exam": exam,
        "theory": theory,
        "radio": radio,
        "checkbox": checkbox,
    }


@pytest.fixture
def enrolled_client(exam_with_lessons):
    user = User.objects.create_user(
        email="exam-api@academy.com",
        phone="+79002223344",
        password="password",
        role="student",
    )
    Enrollment.objects.create(user=user, course=exam_with_lessons["course"])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestExamLessonContentApi:
    def test_anonymous_forbidden(self, exam_with_lessons):
        theory = exam_with_lessons["theory"]
        client = APIClient()
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 401

    def test_retrieve_exam_theory(self, enrolled_client, exam_with_lessons):
        theory = exam_with_lessons["theory"]
        resp = enrolled_client.get(
            f"/api/content/lessons-theory/{theory.public_id}/"
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Теория КР"

    def test_retrieve_exam_radio(self, enrolled_client, exam_with_lessons):
        radio = exam_with_lessons["radio"]
        resp = enrolled_client.get(
            f"/api/content/lessons-radio/{radio.public_id}/"
        )
        assert resp.status_code == 200
        assert resp.data["question_text"] == "1+1?"
        assert len(resp.data["answer_options"]) == 1
        assert "is_correct" not in resp.data["answer_options"][0]

    def test_retrieve_exam_checkbox(self, enrolled_client, exam_with_lessons):
        checkbox = exam_with_lessons["checkbox"]
        resp = enrolled_client.get(
            f"/api/content/lessons-checkbox/{checkbox.public_id}/"
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Checkbox КР"

    def test_filter_by_exam_public_id(
        self, enrolled_client, exam_with_lessons
    ):
        exam = exam_with_lessons["exam"]
        resp = enrolled_client.get(
            "/api/content/lessons-theory/",
            {"exam_public_id": str(exam.public_id)},
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1
