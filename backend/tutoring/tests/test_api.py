"""Занятия: доступ, запись, деньги, напоминания."""

from __future__ import annotations

from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from subscriptions.services import grant_pro
from tutoring.models import (
    AvailabilityWindow,
    LessonAccess,
    LessonReminder,
    LessonTariff,
    TutoringLesson,
    TutorSettings,
)
from users.models import Student

User = get_user_model()


def _user(email, role="student", **extra):
    return User.objects.create_user(
        email=email,
        password="password",
        role=role,
        first_name=extra.pop("first_name", "Иван"),
        **extra,
    )


def _open_week(mentor):
    TutorSettings.objects.create(user=mentor, timezone="Europe/Moscow")
    for weekday in range(7):
        AvailabilityWindow.objects.create(
            mentor=mentor,
            weekday=weekday,
            start_time=time(0, 0),
            end_time=time(23, 59),
        )
    LessonTariff.objects.create(
        mentor=mentor, duration_minutes=60, price_kop=100_000
    )


def _enable(student, mentor):
    Student.objects.create(user=student, assigned_mentor=mentor)
    LessonAccess.objects.create(user=student, enabled=True, granted_by=mentor)


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _book_first(student):
    client = _client(student)
    day = (timezone.now() + timedelta(days=2)).date().isoformat()
    slots = client.get("/api/tutoring/slots/", {"date": day, "duration": 60})
    assert slots.status_code == 200, slots.content
    assert slots.json()["slots"]
    created = client.post(
        "/api/tutoring/lessons/",
        {"starts_at": slots.json()["slots"][0], "duration_minutes": 60},
        format="json",
    )
    assert created.status_code == 201, created.content
    return created.json()


@pytest.mark.django_db
def test_pro_without_lessons_flag_cannot_book():
    mentor = _user("mentor-pro@example.com", role="mentor")
    student = _user("student-pro@example.com")
    _open_week(mentor)
    Student.objects.create(user=student, assigned_mentor=mentor)
    grant_pro(user=student, granted_by=mentor)
    client = _client(student)
    day = (timezone.now() + timedelta(days=2)).date().isoformat()
    resp = client.get("/api/tutoring/slots/", {"date": day, "duration": 60})
    assert resp.status_code == 403
    me = client.get("/api/tutoring/me/")
    assert me.json()["lessons_enabled"] is False
    assert me.json()["can_book"] is False


@pytest.mark.django_db
def test_lessons_flag_books_without_pro():
    mentor = _user("mentor-avito@example.com", role="mentor")
    student = _user("student-avito@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    lesson = _book_first(student)
    assert lesson["price_kop"] == 100_000
    assert lesson["status"] == "booked"


@pytest.mark.django_db
def test_without_mentor_cannot_book():
    student = _user("student-nomentor@example.com")
    LessonAccess.objects.create(user=student, enabled=True)
    client = _client(student)
    resp = client.post(
        "/api/tutoring/lessons/",
        {"starts_at": timezone.now().isoformat(), "duration_minutes": 60},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_other_mentor_does_not_see_student():
    mentor = _user("mentor-own@example.com", role="mentor")
    other = _user("mentor-other@example.com", role="mentor")
    student = _user("student-own@example.com")
    _open_week(mentor)
    _open_week(other)
    _enable(student, mentor)
    lesson = _book_first(student)
    client = _client(student)
    claim = client.post(
        "/api/tutoring/payment-claims/",
        {"amount_kop": 50_000},
        format="json",
    )
    assert claim.status_code == 201
    foreign = _client(other)
    listed = foreign.get("/api/tutoring/lessons/")
    ids = [item["public_id"] for item in listed.json()["results"]]
    assert lesson["public_id"] not in ids
    money = foreign.get("/api/tutoring/payment-claims/")
    assert money.json()["pending"] == []
    denied = foreign.post(
        f"/api/tutoring/payment-claims/{claim.json()['public_id']}/confirm/"
    )
    assert denied.status_code == 403


@pytest.mark.django_db
def test_second_booking_of_same_slot_is_conflict():
    mentor = _user("mentor-slot@example.com", role="mentor")
    student = _user("student-slot@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    first = _book_first(student)
    again = _client(student).post(
        "/api/tutoring/lessons/",
        {"starts_at": first["starts_at"], "duration_minutes": 60},
        format="json",
    )
    assert again.status_code == 409
    assert (
        TutoringLesson.objects.filter(
            mentor=mentor, status=TutoringLesson.Status.BOOKED
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_database_rejects_overlapping_lesson():
    mentor = _user("mentor-db@example.com", role="mentor")
    student = _user("student-db@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    first = _book_first(student)
    lesson = TutoringLesson.objects.get(public_id=first["public_id"])
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TutoringLesson.objects.create(
                student=student,
                mentor=mentor,
                starts_at=lesson.starts_at,
                ends_at=lesson.ends_at,
                duration_minutes=60,
                price_kop=100_000,
                status=TutoringLesson.Status.BOOKED,
            )


@pytest.mark.django_db
def test_done_charges_confirm_pays_reject_does_not():
    mentor = _user("mentor-pay@example.com", role="mentor")
    student = _user("student-pay@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    lesson = _book_first(student)
    mentor_api = _client(mentor)
    done = mentor_api.post(
        f"/api/tutoring/lessons/{lesson['public_id']}/done/"
    )
    assert done.status_code == 200
    balance = _client(student).get("/api/tutoring/me/").json()["balance_kop"]
    assert balance == -100_000
    claim = _client(student).post(
        "/api/tutoring/payment-claims/",
        {"amount_kop": 40_000},
        format="json",
    )
    assert claim.status_code == 201
    confirmed = mentor_api.post(
        f"/api/tutoring/payment-claims/{claim.json()['public_id']}/confirm/"
    )
    assert confirmed.status_code == 200
    balance = _client(student).get("/api/tutoring/me/").json()["balance_kop"]
    assert balance == -60_000
    rejected_claim = _client(student).post(
        "/api/tutoring/payment-claims/",
        {"amount_kop": 10_000},
        format="json",
    )
    rejected = mentor_api.post(
        f"/api/tutoring/payment-claims/{rejected_claim.json()['public_id']}/reject/"
    )
    assert rejected.status_code == 200
    balance = _client(student).get("/api/tutoring/me/").json()["balance_kop"]
    assert balance == -60_000
    debtors = mentor_api.get("/api/tutoring/payment-claims/").json()["debtors"]
    assert debtors[0]["balance_kop"] == -60_000


@pytest.mark.django_db
def test_cancel_drops_pending_reminder():
    mentor = _user("mentor-rem@example.com", role="mentor")
    student = _user("student-rem@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    lesson = _book_first(student)
    row = TutoringLesson.objects.get(public_id=lesson["public_id"])
    assert LessonReminder.objects.filter(
        lesson=row, status=LessonReminder.Status.PENDING
    ).exists()
    resp = _client(student).post(
        f"/api/tutoring/lessons/{lesson['public_id']}/cancel/"
    )
    assert resp.status_code == 200
    assert not LessonReminder.objects.filter(
        lesson=row, status=LessonReminder.Status.PENDING
    ).exists()


@pytest.mark.django_db
def test_admin_grants_access_without_touching_pro(settings):
    settings.TELEGRAM_BOT_TOKEN = ""
    admin = _user(
        "admin-grant@example.com",
        role="admin",
        phone="+79005550001",
    )
    mentor = _user("mentor-grant@example.com", role="mentor")
    student = _user("student-grant@example.com")
    resp = _client(admin).post(
        "/api/tutoring/access/",
        {
            "email": student.email,
            "enabled": True,
            "mentor_public_id": str(mentor.public_id),
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["lessons_enabled"] is True
    assert body["can_book"] is True
    assert body["mentor"]["public_id"] == str(mentor.public_id)
    from subscriptions.services import user_is_pro

    assert user_is_pro(student) is False


@pytest.mark.django_db
def test_mentor_records_homework_and_note():
    mentor = _user("mentor-hw@example.com", role="mentor")
    other = _user("mentor-other@example.com", role="mentor")
    student = _user("student-hw@example.com")
    _open_week(mentor)
    _enable(student, mentor)
    lesson = _book_first(student)
    mentor_api = _client(mentor)
    saved = mentor_api.post(
        f"/api/tutoring/lessons/{lesson['public_id']}/notes/",
        {
            "homework_status": "not_done",
            "learned_note": "Разобрали циклы, домашка не сдана.",
        },
        format="json",
    )
    assert saved.status_code == 200, saved.content
    body = saved.json()
    assert body["homework_status"] == "not_done"
    assert "циклы" in body["learned_note"]
    seen = _client(student).get("/api/tutoring/lessons/").json()["results"]
    assert seen[0]["homework_status"] == "not_done"
    denied = _client(student).post(
        f"/api/tutoring/lessons/{lesson['public_id']}/notes/",
        {"homework_status": "done", "learned_note": ""},
        format="json",
    )
    assert denied.status_code == 403
    foreign = _client(other).post(
        f"/api/tutoring/lessons/{lesson['public_id']}/notes/",
        {"homework_status": "done", "learned_note": ""},
        format="json",
    )
    assert foreign.status_code == 403
