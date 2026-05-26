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

    class Meta:
        model = LessonTheory
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "content",
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
    modules = serializers.SerializerMethodField()

    def get_modules(self, obj):
        queryset = obj.modules.filter(is_active=True).order_by("order_index")
        return ModuleShortSerializer(queryset, many=True).data

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
            "modules",
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

    class Meta:
        model = LessonRadioQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "explanation",
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

    class Meta:
        model = LessonCheckBoxQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "explanation",
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
            "description",
            "instructions",
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
