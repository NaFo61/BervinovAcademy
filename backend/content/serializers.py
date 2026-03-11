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
    module_id = serializers.IntegerField(source="module_id", read_only=True)

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
    course_id = serializers.IntegerField(source="course_id", read_only=True)

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
    course_id = serializers.IntegerField(source="course_id", read_only=True)
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
