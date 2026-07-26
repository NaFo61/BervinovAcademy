"""Tests for Pro tariff entitlements and feature gates."""

from datetime import timedelta

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from communication import services as conf_services
from content.models import Course, LessonRadioQuestion, Module
from content.solution_access import build_reference_solution
from education.services import enroll_user
from subscriptions.models import Entitlement, Plan
from subscriptions.services import (
    FEATURE_MENTOR_CHAT,
    FEATURE_SOLUTION_VIDEO,
    PLAN_CODE_PRO,
    ensure_pro_plan,
    grant_pro,
    subscription_payload,
    user_has_feature,
    user_is_pro,
)
from users.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="sub-student@example.com",
        phone="+79002220001",
        password="password",
        role="student",
        first_name="Ученик",
    )


@pytest.fixture
def mentor(db):
    return User.objects.create_user(
        email="sub-mentor@example.com",
        phone="+79002220002",
        password="password",
        role="mentor",
        first_name="Ментор",
    )


@pytest.fixture
def pro_plan(db):
    return ensure_pro_plan()


@pytest.mark.django_db
class TestGrantPro:
    def test_seed_plan_exists_after_ensure(self, pro_plan):
        assert pro_plan.code == PLAN_CODE_PRO
        assert FEATURE_MENTOR_CHAT in pro_plan.feature_set()

    def test_grant_makes_user_pro_for_month(self, student, pro_plan):
        assert user_is_pro(student) is False
        ent = grant_pro(user=student)
        assert user_is_pro(student) is True
        assert user_has_feature(student, FEATURE_SOLUTION_VIDEO) is True
        assert ent.ends_at > timezone.now() + timedelta(days=29)

    def test_grant_extends_active_period(self, student, pro_plan):
        first = grant_pro(user=student)
        second = grant_pro(user=student)
        assert second.ends_at >= first.ends_at + timedelta(days=29)

    def test_revoked_not_active(self, student, pro_plan):
        ent = grant_pro(user=student)
        ent.revoked_at = timezone.now()
        ent.save(update_fields=["revoked_at"])
        assert user_is_pro(student) is False

    def test_expired_not_active(self, student, pro_plan):
        Entitlement.objects.create(
            user=student,
            plan=pro_plan,
            starts_at=timezone.now() - timedelta(days=40),
            ends_at=timezone.now() - timedelta(days=10),
        )
        assert user_is_pro(student) is False

    def test_mentor_bypasses_entitlement(self, mentor):
        assert user_is_pro(mentor) is True
        assert user_has_feature(mentor, FEATURE_MENTOR_CHAT) is True


@pytest.mark.django_db
class TestMeSubscription:
    def test_me_includes_subscription(self, student):
        client = APIClient()
        client.force_authenticate(user=student)
        before = client.get("/api/users/me/")
        assert before.status_code == status.HTTP_200_OK
        assert before.data["subscription"]["is_pro"] is False

        grant_pro(user=student)
        after = client.get("/api/users/me/")
        assert after.data["subscription"]["is_pro"] is True
        assert after.data["subscription"]["plan"] == "pro"
        assert "solution_video" in after.data["subscription"]["features"]


@pytest.mark.django_db
class TestSolutionVideoGate:
    def test_text_for_all_video_for_pro(self, student, rf):
        course = Course.objects.create(
            title="C", slug="sub-c", description="d", is_active=True
        )
        module = Module.objects.create(course=course, title="M", order_index=1)
        q = LessonRadioQuestion.objects.create(
            module=module,
            title="Q",
            question_text="?",
            solution_text="<p>Текст эталона</p>",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            order_index=1,
        )
        request = rf.get("/")
        request.user = student

        free = build_reference_solution(q, request, unlocked=True)
        assert free["text"]
        assert free["video"] is None
        assert free["has_video"] is True
        assert free["video_requires_pro"] is True

        grant_pro(user=student)
        pro = build_reference_solution(q, request, unlocked=True)
        assert pro["video"] is not None
        assert pro["video_requires_pro"] is False


@pytest.mark.django_db
class TestMentorChatGate:
    def test_student_without_pro_blocked(self, student, mentor):
        course = Course.objects.create(
            title="Chat course",
            slug="sub-chat",
            description="d",
            mentor=mentor,
            is_active=True,
        )
        enroll_user(student, course)
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get(
            "/api/communication/chat/threads/open/",
            {"course": str(course.public_id)},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert "Про" in str(resp.data)

    def test_student_with_pro_can_open(self, student, mentor):
        course = Course.objects.create(
            title="Chat course 2",
            slug="sub-chat-2",
            description="d",
            mentor=mentor,
            is_active=True,
        )
        enroll_user(student, course)
        grant_pro(user=student)
        client = APIClient()
        client.force_authenticate(user=student)
        resp = client.get(
            "/api/communication/chat/threads/open/",
            {"course": str(course.public_id)},
        )
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestConferenceGate:
    @pytest.fixture(autouse=True)
    def _channels(self, settings):
        settings.CHANNEL_LAYERS = {
            "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
        }

    def test_cannot_invite_student_without_pro(self, student, mentor):
        with pytest.raises(ValueError, match="Про"):
            conf_services.create_conference(mentor=mentor, guest=student)

    def test_can_invite_pro_student(self, student, mentor):
        grant_pro(user=student)
        conf = conf_services.create_conference(mentor=mentor, guest=student)
        assert conf.guest_id == student.pk
        assert conf_services.user_may_access_conference(student, conf) is True

    def test_payload_helper(self, student):
        assert subscription_payload(student)["is_pro"] is False
        grant_pro(user=student)
        payload = subscription_payload(student)
        assert payload["is_pro"] is True
        assert Plan.objects.filter(code="pro").exists()
