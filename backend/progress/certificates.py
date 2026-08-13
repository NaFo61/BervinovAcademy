"""Выдача сертификата при полном прохождении курса."""

from __future__ import annotations

from progress.models import CourseCertificate
from progress.stats import get_course_progress_detail


def serialize_certificate(cert: CourseCertificate) -> dict:
    user = cert.user
    full_name = " ".join(
        part for part in (user.first_name, user.last_name) if part
    ).strip()
    return {
        "public_id": str(cert.public_id),
        "serial": cert.serial,
        "issued_at": cert.issued_at.isoformat() if cert.issued_at else None,
        "student_name": full_name or (user.email or "Ученик"),
        "course_public_id": str(cert.course.public_id),
        "course_title": cert.course.title,
    }


def get_certificate(user, course) -> CourseCertificate | None:
    if not user or not course:
        return None
    return (
        CourseCertificate.objects.filter(user=user, course=course)
        .select_related("user", "course")
        .first()
    )


def issue_certificate(user, course) -> CourseCertificate:
    cert, _created = CourseCertificate.objects.get_or_create(
        user=user, course=course
    )
    return cert


def issue_certificate_if_complete(user, course) -> CourseCertificate | None:
    detail = get_course_progress_detail(user, course)
    total = detail["total_steps"]
    done = detail["completed_steps"]
    if total <= 0 or done < total:
        return None
    return issue_certificate(user, course)


def list_certificates_for_user(user) -> list[CourseCertificate]:
    from education.models import Enrollment

    enrollments = Enrollment.objects.filter(user=user).select_related("course")
    for enrollment in enrollments:
        issue_certificate_if_complete(enrollment.user, enrollment.course)
    return list(
        CourseCertificate.objects.filter(user=user)
        .select_related("user", "course")
        .order_by("-issued_at")
    )
