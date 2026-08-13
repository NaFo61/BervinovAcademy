"""Сертификат выдаётся при 100% курса."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from education.services import enroll_user, sync_enrollment_status
from progress.models import CourseCertificate, UserLessonTheoryRead


@pytest.mark.django_db
class TestCourseCertificate:
    @pytest.fixture
    def client(self, student_user):
        c = APIClient()
        c.force_authenticate(user=student_user)
        return c

    def test_not_issued_before_complete(
        self, client, student_user, course, theory_lesson
    ):
        enroll_user(student_user, course)
        resp = client.get("/api/progress/certificates/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []

    def test_issued_at_100_percent(
        self, client, student_user, course, theory_lesson
    ):
        enroll_user(student_user, course)
        UserLessonTheoryRead.objects.create(
            user=student_user, lesson=theory_lesson
        )
        enrollment = student_user.enrollments.get(course=course)
        sync_enrollment_status(enrollment)

        cert = CourseCertificate.objects.get(user=student_user, course=course)
        assert cert.serial.startswith("BA-")

        listed = client.get("/api/progress/certificates/")
        assert listed.status_code == status.HTTP_200_OK
        assert len(listed.data) == 1
        assert listed.data[0]["course_title"] == course.title
        assert listed.data[0]["public_id"] == str(cert.public_id)

        detail = client.get(f"/api/progress/certificates/{cert.public_id}/")
        assert detail.status_code == status.HTTP_200_OK
        assert "Иван" in detail.data["student_name"]

        progress = client.get(
            f"/api/progress/course/?course_public_id={course.public_id}"
        )
        assert progress.data["certificate_public_id"] == str(cert.public_id)

        me = client.get("/api/users/me/")
        assert "achievements" not in me.data
        assert len(me.data["certificates"]) == 1

    def test_public_can_open_certificate(
        self, student_user, course, theory_lesson
    ):
        enroll_user(student_user, course)
        UserLessonTheoryRead.objects.create(
            user=student_user, lesson=theory_lesson
        )
        sync_enrollment_status(student_user.enrollments.get(course=course))
        cert = CourseCertificate.objects.get(user=student_user, course=course)
        anon = APIClient()
        resp = anon.get(f"/api/progress/certificates/{cert.public_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["serial"] == cert.serial

    def test_unknown_certificate_404(self, client):
        resp = client.get(
            "/api/progress/certificates/"
            "00000000-0000-0000-0000-000000000001/"
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
