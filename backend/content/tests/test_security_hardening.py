"""Security regression: content access, HTML sanitize, webhook, throttles."""

import pytest
from rest_framework.test import APIClient

from content.models import Course, Exam, LessonTheory, Module
from education.models import Enrollment
from users.models import User


@pytest.fixture
def student():
    return User.objects.create_user(
        email="sec-student@academy.com",
        phone="+79001110001",
        password="password",
        role="student",
        first_name="Sec",
        last_name="Student",
    )


@pytest.fixture
def other_student():
    return User.objects.create_user(
        email="sec-other@academy.com",
        phone="+79001110002",
        password="password",
        role="student",
        first_name="Other",
        last_name="Student",
    )


@pytest.fixture
def course_with_theory(db):
    course = Course.objects.create(
        title="Sec Course",
        slug="sec-course",
        description="d",
        is_active=True,
    )
    module = Module.objects.create(
        course=course, title="M1", description="", is_active=True
    )
    theory = LessonTheory.objects.create(
        module=module,
        title="Theory",
        content="<p>ok</p><script>alert(1)</script>",
        is_active=True,
    )
    exam = Exam.objects.create(
        course=course, title="KR", duration_minutes=30, is_active=True
    )
    exam_theory = LessonTheory.objects.create(
        exam=exam,
        title="Exam theory",
        content="<p>exam</p>",
        is_active=True,
    )
    return {
        "course": course,
        "module": module,
        "theory": theory,
        "exam": exam,
        "exam_theory": exam_theory,
    }


@pytest.mark.django_db
class TestLessonContentAccess:
    def test_anonymous_lesson_401(self, course_with_theory):
        client = APIClient()
        theory = course_with_theory["theory"]
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 401

    def test_anonymous_exam_theory_401(self, course_with_theory):
        client = APIClient()
        theory = course_with_theory["exam_theory"]
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 401

    def test_enrolled_student_gets_sanitized_html(
        self, student, course_with_theory
    ):
        Enrollment.objects.create(
            user=student, course=course_with_theory["course"]
        )
        client = APIClient()
        client.force_authenticate(user=student)
        theory = course_with_theory["theory"]
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 200
        assert "<script>" not in (resp.data.get("content") or "")
        assert "ok" in (resp.data.get("content") or "")

    def test_unenrolled_student_cannot_read_other_course(
        self, other_student, course_with_theory
    ):
        client = APIClient()
        client.force_authenticate(user=other_student)
        theory = course_with_theory["theory"]
        resp = client.get(f"/api/content/lessons-theory/{theory.public_id}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestHtmlSanitizeUnit:
    def test_strips_script(self):
        from common.html_sanitize import sanitize_html

        out = sanitize_html(
            "<p>Hi</p><script>alert(1)</script><img src=x onerror=alert(1)>"
        )
        assert "<script>" not in out
        assert "onerror" not in out.lower()
        assert "Hi" in out


@pytest.mark.django_db
class TestVkWebhookAuth:
    def test_forbidden_without_matching_secrets(self, settings):
        settings.VK_CALLBACK_SECRET = "super-secret-token"
        client = APIClient()
        resp = client.post(
            "/api/vk/webhook/super-secret-token/",
            data={"type": "message_new", "secret": "wrong"},
            format="json",
        )
        assert resp.status_code == 403

    def test_forbidden_bad_path_secret(self, settings):
        settings.VK_CALLBACK_SECRET = "super-secret-token"
        client = APIClient()
        resp = client.post(
            "/api/vk/webhook/wrong/",
            data={"type": "message_new", "secret": "super-secret-token"},
            format="json",
        )
        assert resp.status_code == 403

    def test_ok_confirmation(self, settings):
        settings.VK_CALLBACK_SECRET = "super-secret-token"
        settings.VK_CALLBACK_CONFIRMATION = "ok-confirm"
        client = APIClient()
        resp = client.post(
            "/api/vk/webhook/super-secret-token/",
            data={"type": "confirmation", "secret": "super-secret-token"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.content.decode() == "ok-confirm"


@pytest.mark.django_db
class TestCodeSubmitLimits:
    def test_code_too_long_rejected(self, student, course_with_theory):
        from content.models import CodingChallenge

        Enrollment.objects.create(
            user=student, course=course_with_theory["course"]
        )
        ch = CodingChallenge.objects.create(
            module=course_with_theory["module"],
            course=course_with_theory["course"],
            title="C",
            description="d",
            instructions="i",
            initial_code="pass",
            solution_template="pass",
            is_active=True,
        )
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.post(
            "/api/progress/code/",
            {"challenge": str(ch.public_id), "code": "x" * 130_000},
            format="json",
        )
        assert resp.status_code == 400
