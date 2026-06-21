"""Tests for chat API"""

import pytest
from rest_framework import status

from communication.models import ChatMessage, DirectThread
from content.models import Course
from education.services import enroll_user


@pytest.fixture
def course(db, mentor_user):
    return Course.objects.create(
        title="Python Start",
        slug="python-start-chat",
        description="Test course",
        mentor=mentor_user,
        is_active=True,
    )


@pytest.fixture
def enrolled_student(student_user, course):
    enroll_user(student_user, course)
    return student_user


@pytest.mark.django_db
class TestChatApi:
    def test_mentor_opens_thread_with_any_student(
        self, mentor_client, mentor_user, student_user
    ):
        resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert DirectThread.objects.count() == 1
        thread = DirectThread.objects.get()
        assert thread.mentor_id == mentor_user.pk
        assert thread.student_id == student_user.pk

    def test_student_cannot_open_thread_without_enrollment(
        self, student_client, mentor_user
    ):
        resp = student_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(mentor_user.public_id)},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_student_opens_thread_with_course_mentor(
        self, student_client, enrolled_student, course, mentor_user
    ):
        resp = student_client.get(
            "/api/communication/chat/threads/open/",
            {"course": str(course.public_id)},
        )
        assert resp.status_code == status.HTTP_200_OK
        thread = DirectThread.objects.get()
        assert thread.mentor_id == mentor_user.pk
        assert thread.student_id == enrolled_student.pk

    def test_send_and_list_messages(
        self, mentor_client, student_user, mentor_user
    ):
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]

        send_resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Привет!"},
            format="json",
        )
        assert send_resp.status_code == status.HTTP_201_CREATED
        assert send_resp.data["body"] == "Привет!"
        assert ChatMessage.objects.count() == 1

        list_resp = mentor_client.get(
            f"/api/communication/chat/threads/{thread_id}/messages/"
        )
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.data["results"]) == 1
        assert list_resp.data["results"][0]["body"] == "Привет!"

    def test_student_cannot_message_unrelated_mentor(
        self, student_client, mentor_user
    ):
        other_mentor = mentor_user.__class__.objects.create_user(
            email="other-mentor@academy.com",
            phone="+79001110099",
            password="password",
            role="mentor",
        )
        resp = student_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(other_mentor.public_id)},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_threads(self, mentor_client, student_user):
        mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        resp = mentor_client.get("/api/communication/chat/threads/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1

    def test_mentor_edits_message_without_edited_flag(
        self, mentor_client, student_user
    ):
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        send_resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Было"},
            format="json",
        )
        msg_id = send_resp.data["public_id"]
        patch_resp = mentor_client.patch(
            f"/api/communication/chat/messages/{msg_id}/",
            {"body": "Стало"},
            format="json",
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.data["body"] == "Стало"
        assert patch_resp.data["show_edited"] is False
        assert patch_resp.data["edited_at"] is not None

    def test_student_edits_message_with_edited_flag(
        self, mentor_user, student_client, student_user, course
    ):
        course.mentor = mentor_user
        course.save()
        enroll_user(student_user, course)
        open_resp = student_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(mentor_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        send_resp = student_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Привет"},
            format="json",
        )
        msg_id = send_resp.data["public_id"]
        patch_resp = student_client.patch(
            f"/api/communication/chat/messages/{msg_id}/",
            {"body": "Привет!"},
            format="json",
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.data["show_edited"] is True

    def test_delete_message(self, mentor_client, student_user):
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        send_resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Удалю"},
            format="json",
        )
        msg_id = send_resp.data["public_id"]
        del_resp = mentor_client.delete(
            f"/api/communication/chat/messages/{msg_id}/",
        )
        assert del_resp.status_code == status.HTTP_200_OK
        assert del_resp.data["is_deleted"] is True
        assert del_resp.data["body"] == ""

    def test_cannot_edit_others_message(
        self, mentor_client, student_client, student_user, course, mentor_user
    ):
        course.mentor = mentor_user
        course.save()
        enroll_user(student_user, course)
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        send_resp = mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Ментор"},
            format="json",
        )
        msg_id = send_resp.data["public_id"]
        resp = student_client.patch(
            f"/api/communication/chat/messages/{msg_id}/",
            {"body": "Хак"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_conference_posts_chat_invite(
        self, mentor_client, mentor_user, student_user
    ):
        resp = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        conf_id = resp.data["public_id"]
        msg = ChatMessage.objects.get(
            conference__public_id=conf_id,
            system_event=ChatMessage.SystemEvent.CONFERENCE_INVITED,
        )
        assert "пригласил" in msg.body.lower()
        assert DirectThread.objects.filter(
            mentor=mentor_user,
            student=student_user,
        ).exists()

    def test_open_thread_by_conference(self, mentor_client, student_user):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"conference": conf_id},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["student"]["public_id"] == str(student_user.public_id)

    def test_end_conference_posts_chat_event(
        self, mentor_client, student_user
    ):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        end = mentor_client.post(
            f"/api/communication/conferences/{conf_id}/end/",
        )
        assert end.status_code == status.HTTP_200_OK
        assert ChatMessage.objects.filter(
            system_event=ChatMessage.SystemEvent.CONFERENCE_ENDED,
        ).exists()

    def test_unread_count_and_mark_read(
        self, mentor_client, student_client, student_user, mentor_user
    ):
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        mentor_client.post(
            f"/api/communication/chat/threads/{thread_id}/messages/",
            {"body": "Привет"},
            format="json",
        )

        list_resp = student_client.get("/api/communication/chat/threads/")
        thread_row = next(
            t for t in list_resp.data if t["public_id"] == thread_id
        )
        assert thread_row["unread_count"] == 1

        total_resp = student_client.get(
            "/api/communication/chat/threads/unread_total/"
        )
        assert total_resp.status_code == status.HTTP_200_OK
        assert total_resp.data["total"] >= 1

        read_resp = student_client.get(
            f"/api/communication/chat/threads/{thread_id}/messages/"
        )
        assert read_resp.status_code == status.HTTP_200_OK

        list_after = student_client.get("/api/communication/chat/threads/")
        thread_after = next(
            t for t in list_after.data if t["public_id"] == thread_id
        )
        assert thread_after["unread_count"] == 0

    def test_decline_conference_posts_chat_event(
        self, mentor_client, student_client, student_user
    ):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        decline = student_client.post(
            f"/api/communication/conferences/{conf_id}/decline/",
        )
        assert decline.status_code == 200
        assert ChatMessage.objects.filter(
            system_event=ChatMessage.SystemEvent.CONFERENCE_DECLINED,
        ).exists()

    def test_cancel_conference_posts_chat_event(
        self, mentor_client, student_user
    ):
        create = mentor_client.post(
            "/api/communication/conferences/",
            {"guest": str(student_user.public_id)},
            format="json",
        )
        conf_id = create.data["public_id"]
        cancel = mentor_client.post(
            f"/api/communication/conferences/{conf_id}/cancel/",
        )
        assert cancel.status_code == 200
        assert ChatMessage.objects.filter(
            system_event=ChatMessage.SystemEvent.CONFERENCE_CANCELLED,
        ).exists()

    def test_message_pagination(self, mentor_client, student_user):
        open_resp = mentor_client.get(
            "/api/communication/chat/threads/open/",
            {"user": str(student_user.public_id)},
        )
        thread_id = open_resp.data["public_id"]
        for idx in range(5):
            mentor_client.post(
                f"/api/communication/chat/threads/{thread_id}/messages/",
                {"body": f"msg-{idx}"},
                format="json",
            )

        page1 = mentor_client.get(
            f"/api/communication/chat/threads/{thread_id}/messages/?limit=2"
        )
        assert page1.status_code == 200
        assert len(page1.data["results"]) == 2
        assert page1.data["has_more"] is True

        oldest = page1.data["results"][0]["created_at"]
        from urllib.parse import quote

        page2 = mentor_client.get(
            f"/api/communication/chat/threads/{thread_id}/messages/"
            f"?limit=2&before={quote(oldest, safe='')}"
        )
        assert page2.status_code == 200
        assert len(page2.data["results"]) == 2
        page1_ids = {m["public_id"] for m in page1.data["results"]}
        page2_ids = {m["public_id"] for m in page2.data["results"]}
        assert page1_ids.isdisjoint(page2_ids)
