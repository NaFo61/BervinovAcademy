from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import LessonAttachment, LessonTheory
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
        title="№1 графы",
        content="<p>Старый HTML</p>",
        is_active=True,
    )


@pytest.fixture
def enrolled_student(student_user, course):
    Enrollment.objects.get_or_create(user=student_user, course=course)
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


def _png(name="schema.png"):
    return SimpleUploadedFile(name, b"fake-png", content_type="image/png")


def _upload(mentor_client, theory_lesson, name="schema.png"):
    resp = mentor_client.post(
        f"/api/mentoring/editor/lessons/theory/"
        f"{theory_lesson.public_id}/attachments/",
        {"file": _png(name)},
        format="multipart",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.data


@pytest.mark.django_db
class TestTheoryBlocks:
    def test_student_sees_legacy_html_without_blocks(
        self, enrolled_student, theory_lesson
    ):
        resp = enrolled_student.get(
            f"/api/content/lessons-theory/{theory_lesson.public_id}/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["blocks"] == []
        assert "Старый HTML" in resp.data["content"]

    def test_patch_blocks_and_student_reads(
        self, mentor_client, enrolled_student, theory_lesson
    ):
        att = _upload(mentor_client, theory_lesson)
        payload = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "type": "heading",
                "text": "Что дают в №1",
            },
            {
                "type": "text",
                "html": (
                    "<p>Буквы <mark>не равны</mark> номерам."
                    "<script>alert(1)</script></p>"
                ),
            },
            {
                "type": "image",
                "attachment_id": att["public_id"],
                "caption": "Исходная схема",
            },
            {
                "type": "callout",
                "html": "<p>Схему рисовали независимо.</p>",
            },
        ]
        patch = mentor_client.patch(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/",
            {"blocks": payload},
            format="json",
        )
        assert patch.status_code == status.HTTP_200_OK
        types = [row["type"] for row in patch.data["blocks"]]
        assert types == ["heading", "text", "image", "callout"]
        text_html = patch.data["blocks"][1]["html"]
        assert "<mark>" in text_html
        assert "<script>" not in text_html
        assert patch.data["blocks"][2]["url"]
        assert patch.data["blocks"][2]["caption"] == "Исходная схема"
        assert "Что дают" in patch.data["content"]

        student = enrolled_student.get(
            f"/api/content/lessons-theory/{theory_lesson.public_id}/"
        )
        assert student.status_code == status.HTTP_200_OK
        assert [row["type"] for row in student.data["blocks"]] == types
        assert student.data["blocks"][2]["url"]
        assert "<mark>" in student.data["blocks"][1]["html"]

        theory_lesson.refresh_from_db()
        assert theory_lesson.blocks[0]["type"] == "heading"

    def test_foreign_attachment_rejected(
        self, mentor_client, theory_lesson, module
    ):
        other = LessonTheory.objects.create(
            module=module,
            title="Другой урок",
            content="<p>x</p>",
            is_active=True,
        )
        att = _upload(mentor_client, other, "other.png")
        resp = mentor_client.patch(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/",
            {
                "blocks": [
                    {
                        "type": "image",
                        "attachment_id": att["public_id"],
                        "caption": "чужая",
                    }
                ]
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_attachment_drops_image_block(
        self, mentor_client, theory_lesson
    ):
        att = _upload(mentor_client, theory_lesson)
        mentor_client.patch(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/",
            {
                "blocks": [
                    {"type": "text", "html": "<p>До</p>"},
                    {
                        "type": "image",
                        "attachment_id": att["public_id"],
                        "caption": "кадр",
                    },
                    {"type": "text", "html": "<p>После</p>"},
                ]
            },
            format="json",
        )
        delete = mentor_client.delete(
            f"/api/mentoring/editor/lessons/theory/"
            f"{theory_lesson.public_id}/attachments/{att['public_id']}/"
        )
        assert delete.status_code == status.HTTP_204_NO_CONTENT
        theory_lesson.refresh_from_db()
        assert [row["type"] for row in theory_lesson.blocks] == [
            "text",
            "text",
        ]
        assert LessonAttachment.objects.count() == 0

    def test_no_file_count_cap(self, mentor_client, theory_lesson):
        for i in range(11):
            resp = mentor_client.post(
                f"/api/mentoring/editor/lessons/theory/"
                f"{theory_lesson.public_id}/attachments/",
                {"file": _png(f"frame-{i}.png")},
                format="multipart",
            )
            assert resp.status_code == status.HTTP_201_CREATED
        assert (
            LessonAttachment.objects.filter(theory=theory_lesson).count() == 11
        )


@pytest.mark.django_db
def test_sanitize_keeps_mark():
    from common.html_sanitize import sanitize_html

    out = sanitize_html("<p>Буквы <mark>не равны</mark> номерам</p>")
    assert "<mark>" in out
    assert "не равны" in out
