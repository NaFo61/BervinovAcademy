from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.attachments import MAX_FILE_BYTES, validate_upload
from content.models import CodingChallenge, LessonAttachment, LessonTheory
from education.models import Enrollment


@pytest.fixture
def mentor_client(mentor_user):
    client = APIClient()
    client.force_authenticate(user=mentor_user)
    return client


@pytest.fixture
def theory_lesson(module):
    return LessonTheory.objects.create(
        module=module,
        title="Theory with files",
        content="<p>text</p>",
        is_active=True,
    )


@pytest.fixture
def enrolled_student(student_user, course):
    Enrollment.objects.get_or_create(user=student_user, course=course)
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


def _txt(name="konspekt.txt", body=b"graf A-B-C\n  otstup\n"):
    return SimpleUploadedFile(name, body, content_type="text/plain")


@pytest.mark.django_db
class TestLessonAttachments:
    def test_mentor_uploads_and_student_sees(
        self, mentor_client, enrolled_student, theory_lesson
    ):
        url = (
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/"
        )
        resp = mentor_client.post(url, {"file": _txt()}, format="multipart")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "konspekt.txt"
        assert resp.data["url"]
        assert LessonAttachment.objects.count() == 1

        lesson = enrolled_student.get(
            f"/api/content/lessons-theory/{theory_lesson.public_id}/"
        )
        assert lesson.status_code == status.HTTP_200_OK
        assert len(lesson.data["attachments"]) == 1
        assert lesson.data["attachments"][0]["name"] == "konspekt.txt"
        assert lesson.data["attachments"][0]["url"]

    def test_mentor_can_delete(self, mentor_client, theory_lesson):
        create = mentor_client.post(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/",
            {"file": _txt()},
            format="multipart",
        )
        aid = create.data["public_id"]
        delete = mentor_client.delete(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/{aid}/"
        )
        assert delete.status_code == status.HTTP_204_NO_CONTENT
        assert LessonAttachment.objects.count() == 0

    def test_student_cannot_upload(self, enrolled_student, theory_lesson):
        resp = enrolled_student.post(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/",
            {"file": _txt()},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_rejects_exe(self, mentor_client, theory_lesson):
        bad = SimpleUploadedFile(
            "virus.exe",
            b"MZ",
            content_type="application/octet-stream",
        )
        resp = mentor_client.post(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/",
            {"file": bad},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_oversize(self):
        class Fake:
            name = "big.pdf"
            size = MAX_FILE_BYTES + 1

        with pytest.raises(ValidationError):
            validate_upload(Fake())

    def test_coding_attachment(
        self, mentor_client, enrolled_student, course, module
    ):
        ch = CodingChallenge.objects.create(
            course=course,
            module=module,
            title="Sum",
            description="sum",
            instructions="print",
            initial_code="print(1)",
            is_active=True,
        )
        resp = mentor_client.post(
            f"/api/mentoring/editor/lessons/coding/"
            f"{ch.public_id}/attachments/",
            {"file": _txt("primer.md", b"# primer\n    indented\n")},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        editor = mentor_client.get(
            f"/api/mentoring/editor/lessons/coding/{ch.public_id}/"
        )
        assert len(editor.data["attachments"]) == 1

        student = enrolled_student.get(
            f"/api/content/challenges/{ch.public_id}/"
        )
        assert student.status_code == status.HTTP_200_OK
        assert len(student.data["attachments"]) == 1
        assert student.data["attachments"][0]["name"] == "primer.md"
