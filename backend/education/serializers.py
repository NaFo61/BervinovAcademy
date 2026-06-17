from rest_framework import serializers

from content.models import Course

from .models import Enrollment


class EnrollmentCreateSerializer(serializers.Serializer):
    course = serializers.UUIDField(
        help_text="public_id курса из каталога",
    )

    def validate_course(self, value):
        try:
            course = Course.objects.get(public_id=value, is_active=True)
        except Course.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Курс не найден или неактивен."
            ) from exc
        self.context["course_obj"] = course
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    course_public_id = serializers.UUIDField(
        source="course.public_id", read_only=True
    )
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    percent = serializers.SerializerMethodField()
    completed_steps = serializers.SerializerMethodField()
    total_steps = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = (
            "public_id",
            "course_public_id",
            "course_title",
            "course_slug",
            "status",
            "percent",
            "completed_steps",
            "total_steps",
            "started_at",
            "last_activity_at",
            "completed_at",
        )
        read_only_fields = fields

    def _detail(self, obj):
        cached = getattr(obj, "_progress_detail", None)
        if cached is None:
            from progress.stats import get_course_progress_detail

            cached = get_course_progress_detail(obj.user, obj.course)
            obj._progress_detail = cached
        return cached

    def get_percent(self, obj) -> int:
        return self._detail(obj)["percent"]

    def get_completed_steps(self, obj) -> int:
        return self._detail(obj)["completed_steps"]

    def get_total_steps(self, obj) -> int:
        return self._detail(obj)["total_steps"]
