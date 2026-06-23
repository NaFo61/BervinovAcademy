from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    RadioAnswerOption,
    Technology,
    TestCase,
)
from .solution_access import (
    build_reference_solution,
    checkbox_solution_unlocked,
    checkbox_wrong_attempts,
    coding_solution_unlocked,
    coding_wrong_attempts,
    has_reference_solution_content,
    radio_solution_unlocked,
    radio_wrong_attempts,
)
from .video_utils import build_video_payload

User = get_user_model()


class CourseMentorBriefSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ("public_id", "first_name", "last_name", "avatar", "role")
        read_only_fields = fields


def _serialize_video(serializer, obj):
    return build_video_payload(obj, serializer.context.get("request"))


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = (
            "public_id",
            "name",
        )
        read_only_fields = fields


class LessonTheoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonTheory
        fields = (
            "public_id",
            "title",
            "order_index",
        )
        read_only_fields = fields


class LessonTheorySerializer(serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )
    video = serializers.SerializerMethodField()

    def get_video(self, obj):
        return _serialize_video(self, obj)

    class Meta:
        model = LessonTheory
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "content",
            "comment",
            "video",
            "order_index",
            "is_active",
        )
        read_only_fields = fields


class LessonRadioShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonRadioQuestion
        fields = ("public_id", "title", "order_index")
        read_only_fields = fields


class LessonCheckBoxShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCheckBoxQuestion
        fields = ("public_id", "title", "order_index")
        read_only_fields = fields


class CodingChallengeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingChallenge
        fields = ("public_id", "title", "order_index", "difficulty", "points")
        read_only_fields = fields


class ModuleShortSerializer(serializers.ModelSerializer):
    lessons_theories = serializers.SerializerMethodField()
    lessons_radio = serializers.SerializerMethodField()
    lessons_checkbox = serializers.SerializerMethodField()
    lessons_coding = serializers.SerializerMethodField()

    def get_lessons_theories(self, obj):
        queryset = obj.lessons_theories.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonTheoryShortSerializer(queryset, many=True).data

    def get_lessons_radio(self, obj):
        queryset = obj.lessons_radio_questions.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonRadioShortSerializer(queryset, many=True).data

    def get_lessons_checkbox(self, obj):
        queryset = obj.lessons_checkbox_questions.filter(
            is_active=True
        ).order_by("order_index")
        return LessonCheckBoxShortSerializer(queryset, many=True).data

    def get_lessons_coding(self, obj):
        queryset = obj.challenges.filter(is_active=True).order_by(
            "order_index"
        )
        return CodingChallengeShortSerializer(queryset, many=True).data

    class Meta:
        model = Module
        fields = (
            "public_id",
            "title",
            "description",
            "order_index",
            "lessons_theories",
            "lessons_radio",
            "lessons_checkbox",
            "lessons_coding",
        )
        read_only_fields = fields


class ModuleListSerializer(serializers.ModelSerializer):
    course_public_id = serializers.UUIDField(
        source="course.public_id", read_only=True
    )

    class Meta:
        model = Module
        fields = (
            "public_id",
            "course_public_id",
            "title",
            "description",
            "order_index",
            "is_active",
        )
        read_only_fields = fields


class ModuleDetailSerializer(serializers.ModelSerializer):
    course_public_id = serializers.UUIDField(
        source="course.public_id", read_only=True
    )
    lessons_theories = serializers.SerializerMethodField()
    lessons_radio = serializers.SerializerMethodField()
    lessons_checkbox = serializers.SerializerMethodField()
    lessons_coding = serializers.SerializerMethodField()

    def get_lessons_theories(self, obj):
        queryset = obj.lessons_theories.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonTheoryShortSerializer(queryset, many=True).data

    def get_lessons_radio(self, obj):
        queryset = obj.lessons_radio_questions.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonRadioShortSerializer(queryset, many=True).data

    def get_lessons_checkbox(self, obj):
        queryset = obj.lessons_checkbox_questions.filter(
            is_active=True
        ).order_by("order_index")
        return LessonCheckBoxShortSerializer(queryset, many=True).data

    def get_lessons_coding(self, obj):
        queryset = obj.challenges.filter(is_active=True).order_by(
            "order_index"
        )
        return CodingChallengeShortSerializer(queryset, many=True).data

    class Meta:
        model = Module
        fields = (
            "public_id",
            "course_public_id",
            "title",
            "description",
            "order_index",
            "is_active",
            "lessons_theories",
            "lessons_radio",
            "lessons_checkbox",
            "lessons_coding",
        )
        read_only_fields = fields


class CourseListSerializer(serializers.ModelSerializer):
    technology = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "public_id",
            "title",
            "slug",
            "image",
            "is_active",
            "created_at",
            "technology",
        )
        read_only_fields = fields


class CourseDetailSerializer(serializers.ModelSerializer):
    technology = TechnologySerializer(many=True, read_only=True)
    mentor = CourseMentorBriefSerializer(read_only=True)
    modules = serializers.SerializerMethodField()
    exams = serializers.SerializerMethodField()
    course_lessons = serializers.SerializerMethodField()

    def get_modules(self, obj):
        queryset = obj.modules.filter(is_active=True).order_by("order_index")
        return ModuleShortSerializer(queryset, many=True).data

    def get_exams(self, obj):
        from exams.serializers import ExamShortSerializer

        queryset = obj.exams.filter(is_active=True).order_by("order_index")
        return ExamShortSerializer(queryset, many=True).data

    def get_course_lessons(self, obj):
        from content.container_lessons import iter_container_lessons

        items = []
        for kind, lesson in iter_container_lessons(obj, active_only=True):
            items.append(
                {
                    "kind": kind,
                    "public_id": str(lesson.public_id),
                    "title": lesson.title,
                    "order_index": lesson.order_index,
                }
            )
        return items

    class Meta:
        model = Course
        fields = (
            "public_id",
            "title",
            "slug",
            "description",
            "image",
            "is_active",
            "created_at",
            "technology",
            "mentor",
            "modules",
            "exams",
            "course_lessons",
        )
        read_only_fields = fields


class RadioAnswerOptionPublicSerializer(serializers.ModelSerializer):
    """Варианты ответа для клиента (без признака правильности)."""

    class Meta:
        model = RadioAnswerOption
        fields = ("public_id", "text", "order_index")
        read_only_fields = fields


class CheckBoxAnswerOptionPublicSerializer(serializers.ModelSerializer):
    """Варианты ответа для клиента (без признака правильности)."""

    class Meta:
        model = CheckBoxAnswerOption
        fields = ("public_id", "text", "order_index")
        read_only_fields = fields


class LessonRadioListSerializer(serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )

    class Meta:
        model = LessonRadioQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "order_index",
            "points",
            "is_active",
        )
        read_only_fields = fields


class LessonRadioDetailSerializer(serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )
    answer_options = serializers.SerializerMethodField()
    solution_unlocked = serializers.SerializerMethodField()
    wrong_attempts = serializers.SerializerMethodField()
    has_reference_solution = serializers.SerializerMethodField()
    reference_solution = serializers.SerializerMethodField()

    def _user(self):
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return None
        return request.user

    def get_has_reference_solution(self, obj):
        return has_reference_solution_content(obj)

    def get_solution_unlocked(self, obj):
        return radio_solution_unlocked(self._user(), obj)

    def get_wrong_attempts(self, obj):
        return radio_wrong_attempts(self._user(), obj)

    def get_reference_solution(self, obj):
        return build_reference_solution(
            obj,
            self.context.get("request"),
            unlocked=radio_solution_unlocked(self._user(), obj),
        )

    class Meta:
        model = LessonRadioQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "comment",
            "explanation",
            "solution_unlocked",
            "wrong_attempts",
            "has_reference_solution",
            "reference_solution",
            "order_index",
            "points",
            "is_active",
            "answer_options",
        )
        read_only_fields = fields

    def get_answer_options(self, obj):
        opts = obj.answers.all().order_by("order_index")
        return RadioAnswerOptionPublicSerializer(opts, many=True).data


class LessonCheckBoxListSerializer(serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )

    class Meta:
        model = LessonCheckBoxQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "order_index",
            "points",
            "is_active",
        )
        read_only_fields = fields


class LessonCheckBoxDetailSerializer(serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )
    answer_options = serializers.SerializerMethodField()
    solution_unlocked = serializers.SerializerMethodField()
    wrong_attempts = serializers.SerializerMethodField()
    has_reference_solution = serializers.SerializerMethodField()
    reference_solution = serializers.SerializerMethodField()

    def _user(self):
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return None
        return request.user

    def get_has_reference_solution(self, obj):
        return has_reference_solution_content(obj)

    def get_solution_unlocked(self, obj):
        return checkbox_solution_unlocked(self._user(), obj)

    def get_wrong_attempts(self, obj):
        return checkbox_wrong_attempts(self._user(), obj)

    def get_reference_solution(self, obj):
        return build_reference_solution(
            obj,
            self.context.get("request"),
            unlocked=checkbox_solution_unlocked(self._user(), obj),
        )

    class Meta:
        model = LessonCheckBoxQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "comment",
            "explanation",
            "solution_unlocked",
            "wrong_attempts",
            "has_reference_solution",
            "reference_solution",
            "order_index",
            "points",
            "is_active",
            "answer_options",
        )
        read_only_fields = fields

    def get_answer_options(self, obj):
        opts = obj.answers.all().order_by("order_index")
        return CheckBoxAnswerOptionPublicSerializer(opts, many=True).data


class TestCaseSerializer(serializers.ModelSerializer):
    """Сериализатор для тестовых случаев"""

    class Meta:
        model = TestCase
        fields = (
            "public_id",
            "input_data",
            "expected_output",
            "is_hidden",
            "order_index",
        )
        read_only_fields = ("public_id",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Скрытые тесты не показываем пользователям
        if instance.is_hidden and not self.context.get("is_admin", False):
            data["input_data"] = "[Скрытый тест]"
            data["expected_output"] = "[Скрытый тест]"
        return data


class CodingChallengeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка задач"""

    difficulty_display = serializers.CharField(
        source="get_difficulty_display", read_only=True
    )
    course_public_id = serializers.UUIDField(
        source="course.public_id",
        read_only=True,
        allow_null=True,
    )
    module_public_id = serializers.UUIDField(
        source="module.public_id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = CodingChallenge
        fields = (
            "public_id",
            "course_public_id",
            "module_public_id",
            "title",
            "difficulty",
            "difficulty_display",
            "points",
            "is_active",
            "order_index",
        )


class CodingChallengeDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор задачи"""

    difficulty_display = serializers.CharField(
        source="get_difficulty_display", read_only=True
    )
    test_cases = serializers.SerializerMethodField()
    user_solved = serializers.SerializerMethodField()
    solution_unlocked = serializers.SerializerMethodField()
    wrong_attempts = serializers.SerializerMethodField()
    has_reference_solution = serializers.SerializerMethodField()
    reference_solution = serializers.SerializerMethodField()
    course_public_id = serializers.UUIDField(
        source="course.public_id",
        read_only=True,
        allow_null=True,
    )
    module_public_id = serializers.UUIDField(
        source="module.public_id",
        read_only=True,
        allow_null=True,
    )

    def _user(self):
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return None
        return request.user

    def get_has_reference_solution(self, obj):
        return has_reference_solution_content(obj)

    def get_solution_unlocked(self, obj):
        return coding_solution_unlocked(self._user(), obj)

    def get_wrong_attempts(self, obj):
        return coding_wrong_attempts(self._user(), obj)

    def get_reference_solution(self, obj):
        return build_reference_solution(
            obj,
            self.context.get("request"),
            unlocked=coding_solution_unlocked(self._user(), obj),
        )

    class Meta:
        model = CodingChallenge
        fields = (
            "public_id",
            "course_public_id",
            "module_public_id",
            "title",
            "description",
            "instructions",
            "comment",
            "solution_unlocked",
            "wrong_attempts",
            "has_reference_solution",
            "reference_solution",
            "initial_code",
            "difficulty",
            "difficulty_display",
            "points",
            "time_limit_ms",
            "memory_limit_mb",
            "test_cases",
            "user_solved",
            "created_at",
        )

    def get_test_cases(self, obj):
        """Показываем только не скрытые тесты"""
        request = self.context.get("request")
        is_admin = request and request.user and request.user.is_staff

        test_cases = obj.test_cases.filter(is_hidden=False)
        if is_admin:
            test_cases = obj.test_cases.all()

        return TestCaseSerializer(
            test_cases, many=True, context={"is_admin": is_admin}
        ).data

    def get_user_solved(self, obj):
        """Проверяет, решил ли пользователь задачу"""
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return False

        return obj.submissions.filter(
            user=request.user, status="completed"
        ).exists()
