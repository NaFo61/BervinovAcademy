"""Сервисы записи на курсы и синхронизации прогресса."""

from __future__ import annotations

from django.utils import timezone

from content.models import Course
from progress.stats import get_course_progress_detail

from .models import Enrollment


def enroll_user(user, course: Course) -> tuple[Enrollment, bool]:
    """Записать пользователя на курс (идемпотентно)."""
    enrollment, created = Enrollment.objects.get_or_create(
        user=user,
        course=course,
    )
    sync_enrollment_status(enrollment)
    return enrollment, created


def sync_enrollment_status(enrollment: Enrollment) -> Enrollment:
    """Обновить статус записи по фактическому прогрессу."""
    detail = get_course_progress_detail(enrollment.user, enrollment.course)
    total = detail["total_steps"]
    done = detail["completed_steps"]

    if total > 0 and done >= total:
        if enrollment.status != Enrollment.Status.COMPLETED:
            enrollment.status = Enrollment.Status.COMPLETED
            enrollment.completed_at = timezone.now()
            enrollment.save(
                update_fields=["status", "completed_at", "last_activity_at"]
            )
    elif enrollment.status == Enrollment.Status.COMPLETED and done < total:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.completed_at = None
        enrollment.save(
            update_fields=["status", "completed_at", "last_activity_at"]
        )
    return enrollment


def build_enrollment_payload(enrollment: Enrollment) -> dict:
    sync_enrollment_status(enrollment)
    detail = get_course_progress_detail(enrollment.user, enrollment.course)
    course = enrollment.course
    return {
        "public_id": str(enrollment.public_id),
        "course_public_id": str(course.public_id),
        "course_title": course.title,
        "course_slug": course.slug,
        "status": enrollment.status,
        "percent": detail["percent"],
        "completed_steps": detail["completed_steps"],
        "total_steps": detail["total_steps"],
        "started_at": enrollment.started_at.isoformat(),
        "last_activity_at": enrollment.last_activity_at.isoformat(),
        "completed_at": (
            enrollment.completed_at.isoformat()
            if enrollment.completed_at
            else None
        ),
    }


def build_enrollments_payload(user) -> list[dict]:
    enrollments = (
        Enrollment.objects.filter(user=user)
        .select_related("course")
        .order_by("-last_activity_at")
    )
    return [build_enrollment_payload(e) for e in enrollments]
