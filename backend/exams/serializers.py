from exams.models import ExamAccessGrant
from exams.services import get_exam_access, serialize_attempt
from rest_framework import serializers

from content.models import Exam


class ExamShortSerializer(serializers.ModelSerializer):
    course_public_id = serializers.UUIDField(
        source="course.public_id", read_only=True
    )
    lessons_theories = serializers.SerializerMethodField()
    lessons_radio = serializers.SerializerMethodField()
    lessons_checkbox = serializers.SerializerMethodField()
    lessons_coding = serializers.SerializerMethodField()

    def get_lessons_theories(self, obj):
        from content.serializers import LessonTheoryShortSerializer

        queryset = obj.lessons_theories.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonTheoryShortSerializer(queryset, many=True).data

    def get_lessons_radio(self, obj):
        from content.serializers import LessonRadioShortSerializer

        queryset = obj.lessons_radio_questions.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonRadioShortSerializer(queryset, many=True).data

    def get_lessons_checkbox(self, obj):
        from content.serializers import LessonCheckBoxShortSerializer

        queryset = obj.lessons_checkbox_questions.filter(
            is_active=True
        ).order_by("order_index")
        return LessonCheckBoxShortSerializer(queryset, many=True).data

    def get_lessons_coding(self, obj):
        from content.serializers import CodingChallengeShortSerializer

        queryset = obj.challenges.filter(is_active=True).order_by(
            "order_index"
        )
        return CodingChallengeShortSerializer(queryset, many=True).data

    class Meta:
        model = Exam
        fields = (
            "public_id",
            "course_public_id",
            "title",
            "description",
            "order_index",
            "duration_minutes",
            "navigation_mode",
            "tab_policy",
            "tab_warn_limit",
            "mentor_unlock_required",
            "pass_score_percent",
            "is_active",
            "lessons_theories",
            "lessons_radio",
            "lessons_checkbox",
            "lessons_coding",
        )
        read_only_fields = fields


class ExamDetailSerializer(ExamShortSerializer):
    prerequisite_module_public_ids = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    access = serializers.SerializerMethodField()

    class Meta(ExamShortSerializer.Meta):
        fields = ExamShortSerializer.Meta.fields + (
            "prerequisite_module_public_ids",
            "lessons",
            "access",
        )

    def get_prerequisite_module_public_ids(self, obj):
        return [str(m.public_id) for m in obj.prerequisite_modules.all()]

    def get_lessons(self, obj):
        from content.container_lessons import iter_container_lessons

        items = []
        for kind, lesson in iter_container_lessons(obj, active_only=True):
            items.append(
                {
                    "kind": kind,
                    "public_id": str(lesson.public_id),
                    "title": lesson.title,
                    "order_index": lesson.order_index,
                    "points": (
                        getattr(lesson, "points", 0) if kind != "theory" else 0
                    ),
                }
            )
        return items

    def get_access(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return get_exam_access(request.user, obj)


class ExamAttemptSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return serialize_attempt(instance)


class ExamAccessGrantSerializer(serializers.ModelSerializer):
    exam_public_id = serializers.UUIDField(
        source="exam.public_id", read_only=True
    )
    user_public_id = serializers.UUIDField(
        source="user.public_id", read_only=True
    )

    class Meta:
        model = ExamAccessGrant
        fields = (
            "public_id",
            "exam_public_id",
            "user_public_id",
            "grant_type",
            "note",
            "is_active",
            "created_at",
            "consumed_at",
        )
        read_only_fields = fields
