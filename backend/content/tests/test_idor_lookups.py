"""Security: content endpoints reject internal PK and enforce enrollment."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from content.models import CodingChallenge, Course, LessonTheory, Module
from education.models import Enrollment
from users.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="idor-student@academy.com",
        phone="+79003330001",
        password="password",
        role="student",
        first_name="Idor",
        last_name="Student",
    )


@pytest.fixture
def stranger(db):
    return User.objects.create_user(
        email="idor-stranger@academy.com",
        phone="+79003330002",
        password="password",
        role="student",
        first_name="Idor",
        last_name="Stranger",
    )


@pytest.fixture
def catalog(db):
    course = Course.objects.create(
        title="IDOR Course",
        slug="idor-course",
        description="d",
        is_active=True,
    )
    module = Module.objects.create(
        course=course, title="M1", description="", is_active=True
    )
    theory = LessonTheory.objects.create(
        module=module,
        title="Theory",
        content="<p>secret lesson</p>",
        is_active=True,
    )
    challenge = CodingChallenge.objects.create(
        module=module,
        course=course,
        title="Ch",
        description="d",
        instructions="i",
        initial_code="pass",
        solution_template="pass",
        is_active=True,
    )
    return {
        "course": course,
        "module": module,
        "theory": theory,
        "challenge": challenge,
    }


@pytest.mark.django_db
class TestContentIdor:
    def test_theory_by_internal_pk_404(self, student, catalog):
        Enrollment.objects.create(user=student, course=catalog["course"])
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get(
            f"/api/content/lessons-theory/{catalog['theory'].pk}/"
        )
        assert resp.status_code == 404

    def test_challenge_by_internal_pk_404(self, student, catalog):
        Enrollment.objects.create(user=student, course=catalog["course"])
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get(
            f"/api/content/challenges/{catalog['challenge'].pk}/"
        )
        assert resp.status_code == 404

    def test_unenrolled_cannot_read_challenge(self, stranger, catalog):
        client = APIClient()
        client.force_authenticate(user=stranger)
        resp = client.get(
            f"/api/content/challenges/{catalog['challenge'].public_id}/"
        )
        assert resp.status_code in (403, 404)

    def test_enrolled_can_read_by_public_id(self, student, catalog):
        Enrollment.objects.create(user=student, course=catalog["course"])
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get(
            f"/api/content/lessons-theory/{catalog['theory'].public_id}/"
        )
        assert resp.status_code == 200
        assert resp.data["public_id"] == str(catalog["theory"].public_id)
