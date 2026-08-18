"""ЕГЭ-курс: seed-инварианты, short-answer, Pro-гейт теории."""

from django.core.management import call_command
import pytest
from rest_framework.test import APIClient

from content.models import (
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonShortAnswer,
    LessonTheory,
    Module,
)
from content.short_answer import answers_match, normalize_answer
from education.models import Enrollment
from users.models import User


def _seed():
    call_command("seed_data", "--clear")


def _student_client():
    user = User.objects.create_user(
        email="ege-student@test.com",
        password="password",
        role="student",
        first_name="ЕГЭ",
        last_name="Ученик",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


@pytest.mark.django_db
def test_normalize_strip_casefold():
    assert normalize_answer("  Ab  C  ") == "ab c"
    assert answers_match("Ab C", "ab  c")
    assert not answers_match("42", "43")


@pytest.mark.django_db
def test_seed_ege_structure():
    _seed()
    courses = Course.objects.filter(is_active=True)
    assert courses.count() == 1
    course = courses.get()
    assert course.title == "ЕГЭ-информатика"
    assert course.slug == "ege-informatika"

    modules = list(
        course.modules.filter(is_active=True).order_by("order_index")
    )
    assert len(modules) == 4
    titles = [m.title for m in modules]
    assert titles == [
        "1-й урок ЕГЭ: Графы",
        "2-й урок ЕГЭ: Кодирование и поиск",
        "3-й урок ЕГЭ: Электронные таблицы",
        "Контрольная",
    ]

    graphs = modules[0]
    assert graphs.lessons_theories.filter(is_active=True).count() == 7

    for mod in modules[:3]:
        assert mod.lessons_theories.filter(is_active=True).count() >= 1
        assert mod.lessons_radio_questions.filter(is_active=True).count() >= 2
        assert (
            mod.lessons_checkbox_questions.filter(is_active=True).count() >= 2
        )
        assert mod.challenges.filter(is_active=True).count() >= 3
        assert mod.lessons_short_answers.filter(is_active=True).count() >= 3
        for theory in mod.lessons_theories.filter(is_active=True):
            assert theory.video_url
        for q in mod.lessons_radio_questions.filter(is_active=True):
            assert q.video_url
        for q in mod.lessons_checkbox_questions.filter(is_active=True):
            assert q.video_url
        for ch in mod.challenges.filter(is_active=True):
            assert ch.video_url
        for q in mod.lessons_short_answers.filter(is_active=True):
            assert q.video_url

    control = modules[3]
    assert control.lessons_theories.filter(is_active=True).count() == 0
    assert control.lessons_radio_questions.filter(is_active=True).count() >= 2
    assert (
        control.lessons_checkbox_questions.filter(is_active=True).count() >= 2
    )
    assert control.challenges.filter(is_active=True).count() >= 2
    assert control.lessons_short_answers.filter(is_active=True).count() >= 2


@pytest.mark.django_db
def test_catalog_lists_one_ege_course():
    _seed()
    user, client = _student_client()
    resp = client.get("/api/content/courses/")
    assert resp.status_code == 200
    rows = resp.data if isinstance(resp.data, list) else resp.data["results"]
    assert len(rows) == 1
    assert rows[0]["title"] == "ЕГЭ-информатика"
    assert rows[0]["slug"] == "ege-informatika"


@pytest.mark.django_db
def test_theory_video_requires_pro():
    _seed()
    user, client = _student_client()
    course = Course.objects.get(slug="ege-informatika")
    Enrollment.objects.create(user=user, course=course)
    theory = LessonTheory.objects.filter(
        module__course=course, is_active=True
    ).first()
    assert theory and theory.video_url

    resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
    assert resp.status_code == 200
    assert resp.data["has_video"] is True
    assert resp.data["video_requires_pro"] is True
    assert resp.data["video"] is None
    assert resp.data["content"]

    from subscriptions.services import grant_pro

    grant_pro(user=user)
    resp2 = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
    assert resp2.status_code == 200
    assert resp2.data["video_requires_pro"] is False
    assert resp2.data["video"] is not None
    assert resp2.data["video"]["embed_url"]


@pytest.mark.django_db
def test_short_answer_api_normalize_and_unlock():
    _seed()
    user, client = _student_client()
    course = Course.objects.get(slug="ege-informatika")
    Enrollment.objects.create(user=user, course=course)
    question = LessonShortAnswer.objects.filter(
        module__course=course, correct_answer="Граф"
    ).first()
    assert question

    detail = client.get(f"/api/content/short-answers/{question.public_id}/")
    assert detail.status_code == 200
    assert "correct_answer" not in detail.data
    assert detail.data["solution_unlocked"] is False

    wrong = client.post(
        "/api/progress/short-answer/",
        {"question": str(question.public_id), "answer": "нет"},
        format="json",
    )
    assert wrong.status_code == 201
    assert wrong.data["is_correct"] is False

    ok = client.post(
        "/api/progress/short-answer/",
        {"question": str(question.public_id), "answer": "  граф  "},
        format="json",
    )
    assert ok.status_code == 201
    assert ok.data["is_correct"] is True
    assert ok.data["solved_ever"] is True

    detail2 = client.get(f"/api/content/short-answers/{question.public_id}/")
    assert detail2.data["solution_unlocked"] is True


@pytest.mark.django_db
def test_short_answer_unlock_after_three_fails():
    _seed()
    user, client = _student_client()
    course = Course.objects.get(slug="ege-informatika")
    Enrollment.objects.create(user=user, course=course)
    question = LessonShortAnswer.objects.filter(
        module__course=course, is_active=True
    ).first()

    for i in range(3):
        resp = client.post(
            "/api/progress/short-answer/",
            {
                "question": str(question.public_id),
                "answer": f"wrong-{i}",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["is_correct"] is False

    detail = client.get(f"/api/content/short-answers/{question.public_id}/")
    assert detail.data["solution_unlocked"] is True
    assert detail.data["wrong_attempts"] >= 3


@pytest.mark.django_db
def test_editor_create_short_answer():
    _seed()
    admin = User.objects.filter(role="admin").first()
    assert admin
    client = APIClient()
    client.force_authenticate(user=admin)
    module = Module.objects.filter(course__slug="ege-informatika").first()
    created = client.post(
        f"/api/mentoring/editor/modules/{module.public_id}/lessons/",
        {"kind": "short_answer", "title": "Новый краткий"},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["title"] == "Новый краткий"
    pid = created.data["public_id"]

    patched = client.patch(
        f"/api/mentoring/editor/lessons/short_answer/{pid}/",
        {
            "question_text": "Сколько?",
            "correct_answer": "10",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
        format="json",
    )
    assert patched.status_code == 200
    assert patched.data["correct_answer"] == "10"
    assert patched.data["video_url"]


@pytest.mark.django_db
def test_seed_has_radio_and_checkbox():
    _seed()
    course = Course.objects.get(slug="ege-informatika")
    assert (
        LessonRadioQuestion.objects.filter(
            module__course=course, is_active=True
        ).count()
        >= 8
    )
    assert (
        LessonCheckBoxQuestion.objects.filter(
            module__course=course, is_active=True
        ).count()
        >= 8
    )
