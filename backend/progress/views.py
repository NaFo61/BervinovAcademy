from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Course
from progress.certificates import (
    get_certificate,
    list_certificates_for_user,
    serialize_certificate,
)
from progress.models import CourseCertificate
from progress.stats import get_course_progress_detail


class CourseProgressView(APIView):
    """
    Сводка прогресса по курсу для текущего пользователя.

    ``GET /api/progress/course/?course_public_id=<uuid>``
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_pid = request.query_params.get("course_public_id")
        if not course_pid:
            return Response(
                {"detail": "Укажите course_public_id."},
                status=400,
            )
        try:
            course = Course.objects.get(public_id=course_pid, is_active=True)
        except Course.DoesNotExist:
            return Response({"detail": "Курс не найден."}, status=404)

        payload = get_course_progress_detail(request.user, course)

        from education.models import Enrollment
        from education.services import sync_enrollment_status

        enrollment = Enrollment.objects.filter(
            user=request.user, course=course
        ).first()
        if enrollment:
            sync_enrollment_status(enrollment)
            payload["enrollment"] = {
                "public_id": str(enrollment.public_id),
                "status": enrollment.status,
            }
            cert = get_certificate(request.user, course)
            payload["certificate_public_id"] = (
                str(cert.public_id) if cert else None
            )
        else:
            payload["certificate_public_id"] = None

        return Response(payload)


class CertificateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certs = list_certificates_for_user(request.user)
        return Response([serialize_certificate(c) for c in certs])


class CertificateDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        cert = (
            CourseCertificate.objects.select_related("user", "course")
            .filter(public_id=public_id)
            .first()
        )
        if cert is None:
            return Response({"detail": "Сертификат не найден."}, status=404)
        return Response(serialize_certificate(cert))
