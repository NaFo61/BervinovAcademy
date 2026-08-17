from datetime import timedelta

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import Course
from education.models import Enrollment
from users.models import User


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin-panel@academy.com",
        phone="+79000000001",
        password="password",
        first_name="Админ",
        last_name="Школы",
    )


@pytest.fixture
def other_mentor(db):
    return User.objects.create_user(
        email="other-mentor-panel@academy.com",
        phone="+79001112234",
        password="password",
        first_name="Другой",
        last_name="Ментор",
        role="mentor",
    )


@pytest.fixture
def other_course(db, technology, other_mentor):
    course = Course.objects.create(
        title="Other Mentor Course",
        description="Not yours",
        slug="other-mentor-course",
        is_active=True,
        mentor=other_mentor,
    )
    course.technology.add(technology)
    return course


@pytest.fixture
def other_student(db):
    return User.objects.create_user(
        email="other-student-panel@academy.com",
        phone="+79004445567",
        password="password",
        first_name="Новый",
        last_name="Ученик",
        role="student",
    )


@pytest.mark.django_db
class TestMentorNewStudentsApi:
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

    @pytest.fixture
    def admin_client(self, admin_user):
        c = APIClient()
        c.force_authenticate(user=admin_user)
        return c

    def test_student_forbidden(self, student_client):
        resp = student_client.get("/api/mentoring/new-students/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_empty_list(self, mentor_client):
        resp = mentor_client.get("/api/mentoring/new-students/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 0
        assert resp.data["results"] == []
        assert resp.data["days"] == 7

    def test_mentor_sees_only_own_courses(
        self,
        mentor_client,
        course,
        student_user,
        other_course,
        other_student,
    ):
        mine = Enrollment.objects.create(user=student_user, course=course)
        Enrollment.objects.filter(pk=mine.pk).update(
            started_at=timezone.now() - timedelta(days=1)
        )
        foreign = Enrollment.objects.create(
            user=other_student, course=other_course
        )
        Enrollment.objects.filter(pk=foreign.pk).update(
            started_at=timezone.now() - timedelta(days=1)
        )

        resp = mentor_client.get("/api/mentoring/new-students/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        row = resp.data["results"][0]
        assert row["user_public_id"] == str(student_user.public_id)
        assert row["course_public_id"] == str(course.public_id)
        assert row["course_title"] == course.title
        assert row["first_name"] == student_user.first_name

    def test_old_enrollment_excluded(
        self, mentor_client, course, student_user
    ):
        old = Enrollment.objects.create(user=student_user, course=course)
        Enrollment.objects.filter(pk=old.pk).update(
            started_at=timezone.now() - timedelta(days=20)
        )
        resp = mentor_client.get("/api/mentoring/new-students/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 0

        resp30 = mentor_client.get("/api/mentoring/new-students/?days=30")
        assert resp30.status_code == status.HTTP_200_OK
        assert resp30.data["count"] == 1
        assert resp30.data["days"] == 30

    def test_admin_sees_all_courses(
        self,
        admin_client,
        course,
        student_user,
        other_course,
        other_student,
    ):
        Enrollment.objects.create(user=student_user, course=course)
        Enrollment.objects.create(user=other_student, course=other_course)
        resp = admin_client.get("/api/mentoring/new-students/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2
