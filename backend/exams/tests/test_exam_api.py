from django.utils import timezone
from exams.models import ExamAccessGrant, ExamAttempt
import pytest
from rest_framework.test import APIClient

from content.models import (
    Course,
    Exam,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    RadioAnswerOption,
)
from progress.models import UserAnswerRadio, UserLessonTheoryRead


@pytest.fixture
def exam_course(db):
    course = Course.objects.create(
        title="ЕГЭ тест",
        slug="ege-exam-test",
        description="",
        is_active=True,
    )
    mod1 = Module.objects.create(
        course=course, title="Модуль 1", is_active=True
    )
    exam = Exam.objects.create(
        course=course,
        title="КР 1",
        duration_minutes=30,
        pass_score_percent=50,
        is_active=True,
    )
    LessonTheory.objects.create(
        exam=exam,
        title="Мини-теория",
        content="Текст",
        order_index=1,
    )
    question = LessonRadioQuestion.objects.create(
        exam=exam,
        title="Вопрос 1",
        question_text="2+2?",
        points=10,
        order_index=2,
    )
    correct = RadioAnswerOption.objects.create(
        question=question,
        text="4",
        is_correct=True,
        order_index=1,
    )
    RadioAnswerOption.objects.create(
        question=question,
        text="5",
        is_correct=False,
        order_index=2,
    )
    return {
        "course": course,
        "module1": mod1,
        "exam": exam,
        "question": question,
        "correct": correct,
    }


@pytest.fixture
def student_client(exam_course, django_user_model):
    user = django_user_model.objects.create_user(
        email="student-exam@test.com",
        password="pass",
        role="student",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def mentor_client(django_user_model):
    user = django_user_model.objects.create_user(
        email="mentor-exam@test.com",
        password="pass",
        role="mentor",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
def test_exam_list_and_detail(student_client, exam_course):
    client, _ = student_client
    course = exam_course["course"]
    exam = exam_course["exam"]

    resp = client.get(f"/api/exams/?course_public_id={course.public_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get(f"/api/exams/{exam.public_id}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "КР 1"
    assert len(body["lessons"]) == 2


@pytest.mark.django_db
def test_start_attempt_and_submit(student_client, exam_course):
    client, user = student_client
    exam = exam_course["exam"]
    question = exam_course["question"]
    correct = exam_course["correct"]

    resp = client.post(f"/api/exams/{exam.public_id}/start/")
    assert resp.status_code == 201
    attempt = resp.json()
    attempt_id = attempt["public_id"]
    assert attempt["status"] == "in_progress"
    assert attempt["remaining_seconds"] > 0

    theory = exam.lessons_theories.first()
    resp = client.post(
        f"/api/exams/attempts/{attempt_id}/theory/",
        {"lesson": str(theory.public_id)},
        format="json",
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/api/exams/attempts/{attempt_id}/radio/",
        {
            "question": str(question.public_id),
            "selected_answer": str(correct.public_id),
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == 10

    resp = client.post(f"/api/exams/attempts/{attempt_id}/submit/")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "submitted"
    assert result["passed"] is True
    assert result["score"] == 10

    assert UserLessonTheoryRead.objects.filter(
        user=user, lesson=theory
    ).exists()
    assert UserAnswerRadio.objects.filter(
        user=user, question=question, is_correct=True
    ).exists()


@pytest.mark.django_db
def test_cannot_restart_without_grant(student_client, exam_course):
    client, _ = student_client
    exam = exam_course["exam"]
    client.post(f"/api/exams/{exam.public_id}/start/")
    attempt = ExamAttempt.objects.get(exam=exam)
    attempt.status = ExamAttempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.save()

    resp = client.post(f"/api/exams/{exam.public_id}/start/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_mentor_grant_retake(mentor_client, student_client, exam_course):
    mclient, mentor = mentor_client
    client, student = student_client
    exam = exam_course["exam"]

    ExamAttempt.objects.create(
        user=student,
        exam=exam,
        status=ExamAttempt.Status.SUBMITTED,
        started_at=timezone.now(),
        expires_at=timezone.now(),
        submitted_at=timezone.now(),
        score=0,
        max_score=10,
    )

    resp = mclient.post(
        f"/api/mentoring/exams/{exam.public_id}/grant/",
        {
            "user_public_id": str(student.public_id),
            "grant_type": "retake",
        },
        format="json",
    )
    assert resp.status_code == 201

    resp = client.post(f"/api/exams/{exam.public_id}/start/")
    assert resp.status_code == 201
    assert ExamAccessGrant.objects.filter(
        user=student, exam=exam, consumed_at__isnull=False
    ).exists()


@pytest.mark.django_db
def test_focus_warn_auto_submit(student_client, exam_course):
    client, _ = student_client
    exam = exam_course["exam"]
    exam.tab_policy = Exam.TabPolicy.WARN
    exam.tab_warn_limit = 1
    exam.save()

    resp = client.post(f"/api/exams/{exam.public_id}/start/")
    attempt_id = resp.json()["public_id"]

    resp = client.post(
        f"/api/exams/attempts/{attempt_id}/focus/",
        {"event_type": "visibility_hidden"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["warn_triggered_submit"] is True
    assert resp.json()["attempt"]["status"] == "submitted"
