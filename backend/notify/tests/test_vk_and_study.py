"""VK Callback, chat-bridge, outbound deliver."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.utils import timezone
from model_bakery import baker
from notify.study_reminders import send_abandoned_and_streak_reminders
from notify.tasks import deliver_outbound
from notify.vk_handlers import handle_callback_event
import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from communication.chat_services import create_message
from communication.models import ChatMessage, DirectThread, UserNotification
from education.models import Enrollment
from users.oauth import resolve_or_create_user, unlink_provider


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_study_reminder_for_stale_enrollment(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    user = baker.make("users.User", role="student", email="b@ex.com")
    course = baker.make("content.Course", title="Python")
    en = baker.make(
        Enrollment,
        user=user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )
    Enrollment.objects.filter(pk=en.pk).update(
        last_activity_at=timezone.now() - timedelta(days=5),
        last_study_reminder_at=None,
    )
    result = send_abandoned_and_streak_reminders()
    assert result["study"] >= 1
    assert UserNotification.objects.filter(
        user=user, kind=UserNotification.Kind.STUDY_REMINDER
    ).exists()


@pytest.mark.django_db
def test_vk_webhook_forbidden_bad_secret(settings):
    settings.VK_CALLBACK_SECRET = "super-secret-token"
    client = APIClient()
    resp = client.post(
        "/api/vk/webhook/wrong/",
        data={"type": "message_new", "secret": "super-secret-token"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_vk_webhook_forbidden_bad_body_secret(settings):
    settings.VK_CALLBACK_SECRET = "super-secret-token"
    client = APIClient()
    resp = client.post(
        "/api/vk/webhook/super-secret-token/",
        data={"type": "message_new", "secret": "nope"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_vk_webhook_confirmation(settings):
    settings.VK_CALLBACK_SECRET = "super-secret-token"
    settings.VK_CALLBACK_CONFIRMATION = "confirm_string_abc"
    client = APIClient()
    # Как в UI VK: confirmation часто без secret в теле
    resp = client.post(
        "/api/vk/webhook/super-secret-token/",
        data={"type": "confirmation", "group_id": 238124028},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.content.decode() == "confirm_string_abc"


@pytest.mark.django_db
def test_vk_webhook_confirmation_with_secret(settings):
    settings.VK_CALLBACK_SECRET = "super-secret-token"
    settings.VK_CALLBACK_CONFIRMATION = "confirm_string_abc"
    client = APIClient()
    resp = client.post(
        "/api/vk/webhook/super-secret-token/",
        data={
            "type": "confirmation",
            "group_id": 1,
            "secret": "super-secret-token",
        },
        format="json",
    )
    assert resp.status_code == 200
    assert resp.content.decode() == "confirm_string_abc"


@pytest.mark.django_db
def test_vk_webhook_message_new_ok(settings):
    settings.VK_CALLBACK_SECRET = "sec"
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="s2@ex.com",
        vk_id=2002,
        vk_messages_allowed=True,
    )
    mentor = baker.make("users.User", role="mentor", email="m2@ex.com")
    DirectThread.objects.create(mentor=mentor, student=student)
    client = APIClient()
    with patch("notify.vk_handlers.send_message", return_value=True):
        resp = client.post(
            "/api/vk/webhook/sec/",
            data={
                "type": "message_new",
                "secret": "sec",
                "object": {
                    "message": {
                        "from_id": 2002,
                        "peer_id": 2002,
                        "text": "через webhook",
                    }
                },
            },
            format="json",
        )
    assert resp.status_code == 200
    assert resp.content.decode() == "ok"
    assert ChatMessage.objects.filter(body="через webhook").exists()


@pytest.mark.django_db
def test_vk_inbound_creates_chat_message(settings):
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="s@ex.com",
        vk_id=1001,
        vk_messages_allowed=True,
    )
    mentor = baker.make("users.User", role="mentor", email="m@ex.com")
    DirectThread.objects.create(mentor=mentor, student=student)

    with patch("notify.vk_handlers.send_message", return_value=True):
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 1001,
                        "peer_id": 1001,
                        "text": "Привет с VK",
                    }
                },
            }
        )

    msg = ChatMessage.objects.get(sender=student, body="Привет с VK")
    assert msg.source == ChatMessage.Source.VK


@pytest.mark.django_db
def test_vk_message_allow_sets_flag():
    user = baker.make(
        "users.User",
        role="student",
        email="allow@ex.com",
        vk_id=3003,
        vk_messages_allowed=False,
    )
    handle_callback_event(
        {"type": "message_allow", "object": {"user_id": 3003}}
    )
    user.refresh_from_db()
    assert user.vk_messages_allowed is True


@pytest.mark.django_db
def test_vk_message_deny_clears_flag():
    user = baker.make(
        "users.User",
        role="student",
        email="deny@ex.com",
        vk_id=3004,
        vk_messages_allowed=True,
    )
    handle_callback_event(
        {"type": "message_deny", "object": {"user_id": 3004}}
    )
    user.refresh_from_db()
    assert user.vk_messages_allowed is False


@pytest.mark.django_db
def test_vk_inbound_unknown_user_gets_hint(settings):
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "42"
    with patch("notify.vk_handlers.send_message") as send:
        send.return_value = True
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 99999,
                        "peer_id": 99999,
                        "text": "hello",
                    }
                },
            }
        )
        assert send.called
        text = send.call_args[0][1]
        assert "привяз" in text.lower() or "войди" in text.lower()


@pytest.mark.django_db
def test_vk_multi_thread_asks_to_choose(settings):
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="multi@ex.com",
        vk_id=4004,
        vk_messages_allowed=True,
    )
    m1 = baker.make("users.User", role="mentor", email="m1@ex.com")
    m2 = baker.make("users.User", role="mentor", email="m2@ex.com")
    DirectThread.objects.create(mentor=m1, student=student)
    DirectThread.objects.create(mentor=m2, student=student)

    with patch("notify.vk_handlers.send_message") as send:
        send.return_value = True
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 4004,
                        "peer_id": 4004,
                        "text": "всем привет",
                    }
                },
            }
        )
        assert send.called
        kwargs = send.call_args.kwargs
        assert kwargs.get("keyboard") is not None
    assert ChatMessage.objects.filter(sender=student).count() == 0


@pytest.mark.django_db
def test_vk_thread_payload_then_message(settings):
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="pick@ex.com",
        vk_id=5005,
        vk_messages_allowed=True,
    )
    m1 = baker.make("users.User", role="mentor", email="pm1@ex.com")
    m2 = baker.make("users.User", role="mentor", email="pm2@ex.com")
    t1 = DirectThread.objects.create(mentor=m1, student=student)
    DirectThread.objects.create(mentor=m2, student=student)

    with patch("notify.vk_handlers.send_message", return_value=True):
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 5005,
                        "peer_id": 5005,
                        "text": "выбрать",
                        "payload": f"thread:{t1.public_id}",
                    }
                },
            }
        )
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 5005,
                        "peer_id": 5005,
                        "text": "после выбора",
                    }
                },
            }
        )

    msg = ChatMessage.objects.get(body="после выбора")
    assert msg.thread_id == t1.pk
    assert msg.source == ChatMessage.Source.VK


@pytest.mark.django_db
def test_vk_help_command(settings):
    settings.VK_GROUP_TOKEN = "tok"
    baker.make(
        "users.User",
        role="student",
        email="help@ex.com",
        vk_id=6006,
        vk_messages_allowed=True,
    )
    with patch("notify.vk_handlers.send_message") as send:
        send.return_value = True
        handle_callback_event(
            {
                "type": "message_new",
                "object": {
                    "message": {
                        "from_id": 6006,
                        "peer_id": 6006,
                        "text": "/help",
                    }
                },
            }
        )
        assert "Команды" in send.call_args[0][1]


@pytest.mark.django_db
def test_deliver_outbound_sends_vk_when_allowed(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    user = baker.make(
        "users.User",
        role="student",
        email="out@ex.com",
        vk_id=7007,
        vk_messages_allowed=True,
    )
    with patch("notify.vk_api.send_message", return_value=True) as send:
        result = deliver_outbound(
            user_id=user.pk,
            title="Тест",
            body="тело",
            url="https://academy.test/messages",
            kind="mentor_message",
        )
        assert result["vk"] is True
        assert send.called
        assert send.call_args[0][0] == 7007


@pytest.mark.django_db
def test_deliver_outbound_skip_vk(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    user = baker.make(
        "users.User",
        role="student",
        email="skip@ex.com",
        vk_id=7008,
        vk_messages_allowed=True,
    )
    with patch("notify.vk_api.send_message") as send:
        result = deliver_outbound(
            user_id=user.pk,
            title="Эхо",
            body="не надо в VK",
            skip_vk=True,
        )
        assert result["vk"] is False
        assert not send.called


@pytest.mark.django_db
def test_create_message_from_vk_skips_vk_notify(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="bridge@ex.com",
        vk_id=8008,
        vk_messages_allowed=True,
    )
    mentor = baker.make(
        "users.User",
        role="mentor",
        email="ment@ex.com",
        vk_id=8009,
        vk_messages_allowed=True,
    )
    thread = DirectThread.objects.create(mentor=mentor, student=student)

    with patch("notify.vk_api.send_message") as send:
        send.return_value = True
        create_message(
            thread=thread,
            sender=student,
            body="из VK на сайт",
            source=ChatMessage.Source.VK,
        )
        # уведомление ментору уходит, но skip_vk=True → VK send не зовём
        assert not send.called


@pytest.mark.django_db
def test_create_message_from_site_notifies_vk(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "1"
    student = baker.make(
        "users.User",
        role="student",
        email="site2vk@ex.com",
        vk_id=8010,
        vk_messages_allowed=True,
    )
    mentor = baker.make("users.User", role="mentor", email="ment2@ex.com")
    thread = DirectThread.objects.create(mentor=mentor, student=student)

    with patch("notify.vk_api.send_message", return_value=True) as send:
        create_message(
            thread=thread,
            sender=mentor,
            body="ответ ментора",
            source=ChatMessage.Source.SITE,
        )
        assert send.called
        assert send.call_args[0][0] == 8010


@pytest.mark.django_db
def test_vk_status_endpoint(settings):
    settings.VK_GROUP_TOKEN = "tok"
    settings.VK_GROUP_ID = "12345"
    user = baker.make(
        "users.User",
        role="student",
        email="st@ex.com",
        vk_id=9010,
        vk_messages_allowed=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/vk/status/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["linked"] is True
    assert data["messages_allowed"] is True
    assert data["bot_configured"] is True
    assert "vk.me/club12345" in data["write_url"]


@pytest.mark.django_db
def test_me_payload_has_oauth_and_vk(settings):
    settings.VK_GROUP_ID = "7"
    settings.VK_GROUP_TOKEN = "t"
    user = baker.make(
        "users.User",
        role="student",
        email="me@ex.com",
        yandex_id="ya-me",
        vk_id=77,
        vk_messages_allowed=False,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/users/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["oauth"]["yandex"] is True
    assert data["oauth"]["vk"] is True
    assert data["vk"]["linked"] is True
    assert "telegram" not in data


@pytest.mark.django_db
def test_oauth_resolve_by_email_merge():
    existing = baker.make("users.User", role="student", email="merge@ex.com")
    user, created = resolve_or_create_user(
        {
            "provider": "yandex",
            "provider_user_id": "ya-99",
            "email": "merge@ex.com",
            "first_name": "A",
            "last_name": "B",
        }
    )
    assert not created
    assert user.pk == existing.pk
    existing.refresh_from_db()
    assert existing.yandex_id == "ya-99"


@pytest.mark.django_db
def test_oauth_create_vk_user():
    user, created = resolve_or_create_user(
        {
            "provider": "vk",
            "provider_user_id": "555",
            "email": None,
            "first_name": "Иван",
            "last_name": "VK",
        }
    )
    assert created
    assert user.vk_id == 555
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_oauth_unlink_last_method_forbidden():
    user = baker.make(
        "users.User",
        role="student",
        email=None,
        phone=None,
        yandex_id="only-ya",
        vk_id=None,
    )
    user.set_unusable_password()
    user.save()
    with pytest.raises(ValidationError):
        unlink_provider(user, "yandex")
