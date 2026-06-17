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


@pytest.mark.django_db
class TestExamLessonContentApi:
    def test_retrieve_exam_theory(self, exam_with_lessons):
        theory = exam_with_lessons["theory"]
        client = APIClient()
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 200
        assert resp.data["title"] == "Теория КР"

    def test_retrieve_exam_radio(self, exam_with_lessons):
        radio = exam_with_lessons["radio"]
        client = APIClient()
        resp = client.get(f"/api/content/lessons-radio/{radio.public_id}/")
        assert resp.status_code == 200
        assert resp.data["question_text"] == "1+1?"
        assert len(resp.data["answer_options"]) == 1

    def test_retrieve_exam_checkbox(self, exam_with_lessons):
        checkbox = exam_with_lessons["checkbox"]
        client = APIClient()
        resp = client.get(
            f"/api/content/lessons-checkbox/{checkbox.public_id}/"
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Checkbox КР"

    def test_filter_by_exam_public_id(self, exam_with_lessons):
        exam = exam_with_lessons["exam"]
        client = APIClient()
        resp = client.get(
            "/api/content/lessons-theory/",
            {"exam_public_id": str(exam.public_id)},
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1
