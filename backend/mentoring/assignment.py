"""Назначение ментора студенту и разрешение «своего» ментора."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from education.models import Enrollment
from users.models import Student

User = get_user_model()


def mentor_brief(user) -> dict | None:
    if user is None:
        return None
    avatar_url = None
    try:
        if user.avatar:
            avatar_url = user.avatar.url
    except (ValueError, AttributeError):
        avatar_url = None
    return {
        "public_id": str(user.public_id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "avatar": avatar_url,
        "role": user.role,
    }


def ensure_student_profile(user) -> Student:
    if getattr(user, "role", None) != "student":
        raise ValidationError(
            {"detail": "Назначать ментора можно только студенту."}
        )
    profile, _ = Student.objects.get_or_create(user=user)
    return profile


def default_admin_mentor():
    return (
        User.objects.filter(role="admin", is_active=True)
        .order_by("date_joined", "id")
        .first()
        or User.objects.filter(is_superuser=True, is_active=True)
        .order_by("date_joined", "id")
        .first()
    )


def course_mentor_for_student(student):
    enrollment = (
        Enrollment.objects.filter(
            user=student,
            course__is_active=True,
            course__mentor__isnull=False,
            course__mentor__is_active=True,
        )
        .select_related("course__mentor")
        .order_by("-last_activity_at")
        .first()
    )
    if enrollment and enrollment.course.mentor_id:
        return enrollment.course.mentor
    return None


def resolve_student_mentor(student) -> tuple[User | None, str]:
    """
    Порядок: assigned → ментор курса → первый admin.

    Returns (mentor_user_or_none, source).
    """
    if getattr(student, "role", None) != "student":
        return None, "none"

    profile = getattr(student, "student_profile", None)
    if profile is None:
        try:
            profile = Student.objects.select_related("assigned_mentor").get(
                user=student
            )
        except Student.DoesNotExist:
            profile = None

    if profile and profile.assigned_mentor_id:
        mentor = profile.assigned_mentor
        if mentor and mentor.is_active and mentor.role in ("mentor", "admin"):
            return mentor, "assigned"

    course_mentor = course_mentor_for_student(student)
    if course_mentor:
        return course_mentor, "course"

    admin = default_admin_mentor()
    if admin:
        return admin, "default_admin"

    return None, "none"


def list_assignable_mentors():
    return User.objects.filter(
        role__in=("mentor", "admin"), is_active=True
    ).order_by("role", "first_name", "last_name", "email")


@transaction.atomic
def assign_mentor_to_student(*, student, mentor, actor) -> Student:
    if getattr(actor, "role", None) not in ("mentor", "admin"):
        raise PermissionDenied("Назначать ментора могут ментор или админ.")
    if getattr(student, "role", None) != "student":
        raise ValidationError({"detail": "Пользователь не студент."})

    if mentor is not None:
        if mentor.role not in ("mentor", "admin") or not mentor.is_active:
            raise ValidationError(
                {"mentor_public_id": "Нужен активный ментор или админ."}
            )

    profile = ensure_student_profile(student)
    profile.assigned_mentor = mentor
    profile.save(update_fields=["assigned_mentor"])
    return profile
