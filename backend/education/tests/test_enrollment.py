import pytest
from rest_framework import status
from rest_framework.test import APIClient

from education.models import Enrollment
from progress.models import UserLessonTheoryRead


@pytest.mark.django_db
class TestEnrollmentApi:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_enroll_creates_record(self, client, course):
        resp = client.post(
            "/api/education/enrollments/",
            {"course": str(course.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["course_public_id"] == str(course.public_id)
        assert resp.data["status"] == "active"
        assert resp.data["percent"] == 0

    def test_enroll_is_idempotent(self, client, student_user, course):
        client.post(
            "/api/education/enrollments/",
            {"course": str(course.public_id)},
            format="json",
        )
        resp = client.post(
            "/api/education/enrollments/",
            {"course": str(course.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert (
            Enrollment.objects.filter(user=student_user, course=course).count()
            == 1
        )

    def test_list_enrollments(self, client, student_user, course):
        Enrollment.objects.create(user=student_user, course=course)
        resp = client.get("/api/education/enrollments/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1
        assert resp.data[0]["course_title"] == course.title


@pytest.mark.django_db
class TestCourseProgressApi:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_course_progress_empty(self, client, course):
        resp = client.get(
            f"/api/progress/course/?course_public_id={course.public_id}"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["completed_steps"] == 0
        assert resp.data["completed"] == []

    def test_course_progress_after_theory_read(
        self, client, student_user, theory_lesson, course
    ):
        UserLessonTheoryRead.objects.create(
            user=student_user, lesson=theory_lesson
        )
        resp = client.get(
            f"/api/progress/course/?course_public_id={course.public_id}"
        )
        assert resp.data["completed_steps"] == 1
        key = f"theory-{theory_lesson.public_id}"
        assert key in resp.data["completed"]


@pytest.mark.django_db
class TestProfileEnrollmentsAndActivity:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_me_includes_enrollments_and_activity(
        self, client, student_user, course
    ):
        Enrollment.objects.create(user=student_user, course=course)
        resp = client.get("/api/users/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert "enrollments" in resp.data
        assert len(resp.data["enrollments"]) == 1
        assert resp.data["enrollments"][0]["course_title"] == course.title
        assert "activity" in resp.data
        assert "last_30_days" in resp.data["activity"]
        assert len(resp.data["activity"]["last_30_days"]) == 30
