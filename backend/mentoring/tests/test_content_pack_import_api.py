"""API импорта content-pack ZIP в курс."""

from io import BytesIO
import json
import zipfile

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import Course, LessonRadioQuestion, Module
from users.models import User


def _sample_questions():
    return {
        "meta": {"images_dir": "images/"},
        "lessons": [
            {
                "type": "radio",
                "title": "API radio",
                "question_text": "Pick one",
                "points": 3,
                "answers": [["wrong", False], ["right", True]],
            },
        ],
    }


def _zip_bytes(*, manifest: dict, questions: dict) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
        )
        zf.writestr(
            "questions.json",
            json.dumps(questions, ensure_ascii=False).encode("utf-8"),
        )
    return buf.getvalue()


@pytest.fixture
def mentor_client(mentor_user):
    client = APIClient()
    client.force_authenticate(user=mentor_user)
    return client


@pytest.fixture
def owned_course(mentor_user):
    course = Course.objects.create(
        title="Тестовый курс",
        slug="test-import-course",
        description="desc",
        is_active=True,
        mentor=mentor_user,
    )
    module = Module.objects.create(
        course=course,
        title="Модуль для импорта",
        description="",
        order_index=1,
        is_active=True,
    )
    return course, module


@pytest.mark.django_db
class TestContentPackImportApi:
    def test_preview_import_pack(self, mentor_client, owned_course):
        course, module = owned_course
        manifest = {
            "pack_id": "api-pack",
            "course_slug": course.slug,
            "module_title": module.title,
        }
        data = _zip_bytes(manifest=manifest, questions=_sample_questions())
        url = f"/api/mentoring/editor/courses/{course.public_id}/import-pack/"
        response = mentor_client.post(
            url,
            {"archive": ("pack.zip", data, "application/zip"), "dry_run": "1"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["dry_run"] is True
        assert response.data["created"] == 1
        assert response.data["lesson_count"] == 1
        assert LessonRadioQuestion.objects.filter(module=module).count() == 0

    def test_import_pack(self, mentor_client, owned_course):
        course, module = owned_course
        manifest = {
            "pack_id": "api-pack",
            "course_slug": course.slug,
            "module_title": module.title,
        }
        data = _zip_bytes(manifest=manifest, questions=_sample_questions())
        url = f"/api/mentoring/editor/courses/{course.public_id}/import-pack/"
        response = mentor_client.post(
            url,
            {"archive": ("pack.zip", data, "application/zip")},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["dry_run"] is False
        assert response.data["created"] == 1
        assert LessonRadioQuestion.objects.filter(module=module).count() == 1

    def test_wrong_course_slug(self, mentor_client, owned_course):
        course, module = owned_course
        manifest = {
            "pack_id": "api-pack",
            "course_slug": "other-slug",
            "module_title": module.title,
        }
        data = _zip_bytes(manifest=manifest, questions=_sample_questions())
        url = f"/api/mentoring/editor/courses/{course.public_id}/import-pack/"
        response = mentor_client.post(
            url,
            {"archive": ("pack.zip", data, "application/zip")},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "course_slug" in response.data["detail"]

    def test_student_forbidden(self, student_user, owned_course):
        course, _module = owned_course
        client = APIClient()
        client.force_authenticate(user=student_user)
        manifest = {
            "pack_id": "api-pack",
            "course_slug": course.slug,
            "module_title": "x",
        }
        data = _zip_bytes(manifest=manifest, questions=_sample_questions())
        url = f"/api/mentoring/editor/courses/{course.public_id}/import-pack/"
        response = client.post(
            url,
            {"archive": ("pack.zip", data, "application/zip")},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_other_mentor_forbidden(self, owned_course):
        course, module = owned_course
        other = User.objects.create_user(
            email="other2@academy.com",
            phone="+79001112299",
            password="password",
            role="mentor",
        )
        client = APIClient()
        client.force_authenticate(user=other)
        manifest = {
            "pack_id": "api-pack",
            "course_slug": course.slug,
            "module_title": module.title,
        }
        data = _zip_bytes(manifest=manifest, questions=_sample_questions())
        url = f"/api/mentoring/editor/courses/{course.public_id}/import-pack/"
        response = client.post(
            url,
            {"archive": ("pack.zip", data, "application/zip")},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
