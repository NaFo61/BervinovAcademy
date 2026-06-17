from common.drf import UUID_LOOKUP_REGEX
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Enrollment
from .serializers import EnrollmentCreateSerializer, EnrollmentSerializer
from .services import enroll_user, sync_enrollment_status


class EnrollmentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Запись на курсы.

    - ``GET /education/enrollments/`` — мои курсы
    - ``GET /education/enrollments/{public_id}/`` — одна запись
    - ``POST /education/enrollments/`` — начать курс (тело: ``{"course": "<uuid>"}``)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        return (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course")
            .order_by("-last_activity_at")
        )

    def create(self, request, *args, **kwargs):
        ser = EnrollmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        course = ser.context["course_obj"]
        enrollment, created = enroll_user(request.user, course)
        sync_enrollment_status(enrollment)
        out = EnrollmentSerializer(enrollment)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
