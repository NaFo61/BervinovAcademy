"""Кто может записываться на занятия."""

from __future__ import annotations

from django.contrib.auth import get_user_model

from tutoring.models import LessonAccess
from users.models import Student

User = get_user_model()


def access_row(user) -> LessonAccess | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return LessonAccess.objects.filter(user=user).first()


def lessons_enabled(user) -> bool:
    row = access_row(user)
    return bool(row and row.enabled)


def assigned_mentor(user):
    """Только явно назначенный ментор. Запасной admin из чата сюда не входит."""
    if getattr(user, "role", None) != "student":
        return None
    profile = (
        Student.objects.filter(user=user)
        .select_related("assigned_mentor")
        .first()
    )
    if profile is None or profile.assigned_mentor_id is None:
        return None
    mentor = profile.assigned_mentor
    if mentor and mentor.is_active and mentor.role in ("mentor", "admin"):
        return mentor
    return None


def can_book(user) -> bool:
    return lessons_enabled(user) and assigned_mentor(user) is not None


def booking_block_reason(user) -> str | None:
    if not lessons_enabled(user):
        return "no_access"
    if assigned_mentor(user) is None:
        return "no_mentor"
    return None
