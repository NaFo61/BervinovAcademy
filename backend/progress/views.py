from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Course
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

        return Response(payload)
