from rest_framework import serializers

from .models import Course, LessonTheory, Module, Technology


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = (
            "id",
            "name",
        )
        read_only_fields = fields


class LessonTheoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonTheory
        fields = (
            "id",
            "title",
            "order_index",
        )
        read_only_fields = fields


class LessonTheorySerializer(serializers.ModelSerializer):
    module_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = LessonTheory
        fields = (
            "id",
            "module_id",
            "title",
            "content",
            "order_index",
            "is_active",
        )
        read_only_fields = fields


class ModuleShortSerializer(serializers.ModelSerializer):
    lessons_theories = serializers.SerializerMethodField()

    def get_lessons_theories(self, obj):
        queryset = obj.lessons_theories.filter(is_active=True).order_by(
            "order_index"
        )
        return LessonTheoryShortSerializer(queryset, many=True).data

    class Meta:
        model = Module
        fields = (
            "id",
            "title",
            "description",
            "order_index",
            "lessons_theories",
        )
        read_only_fields = fields


class ModuleListSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "course_id",
            "title",
            "description",
            "order_index",
            "is_active",
        )
        read_only_fields = fields


class ModuleDetailSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(read_only=True)
    lessons_theories = LessonTheoryShortSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "course_id",
            "title",
            "description",
            "order_index",
            "is_active",
            "lessons_theories",
        )
        read_only_fields = fields


class CourseListSerializer(serializers.ModelSerializer):
    technology = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
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
            "id",
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


# content/serializers.py (добавить в существующий файл)

from .models import CodingChallenge, TestCase


class TestCaseSerializer(serializers.ModelSerializer):
    """Сериализатор для тестовых случаев"""

    class Meta:
        model = TestCase
        fields = (
            "id",
            "input_data",
            "expected_output",
            "is_hidden",
            "order_index",
        )
        read_only_fields = ("id",)

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

    class Meta:
        model = CodingChallenge
        fields = (
            "id",
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

    class Meta:
        model = CodingChallenge
        fields = (
            "id",
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
