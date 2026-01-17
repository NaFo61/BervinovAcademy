from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import Course, LessonTheory, Module
from .serializers import (
    CourseDetailSerializer,
    CourseListSerializer,
    LessonTheorySerializer,
    ModuleDetailSerializer,
    ModuleListSerializer,
)


class CourseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Course.objects.filter(is_active=True)
            .prefetch_related(
                "technology",
                "modules",
                "modules__lessons_theories",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer


class ModuleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Module.objects.filter(is_active=True, course__is_active=True)
            .select_related("course")
            .prefetch_related("lessons_theories")
            .order_by("course_id", "order_index")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ModuleDetailSerializer
        return ModuleListSerializer


class LessonTheoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            LessonTheory.objects.filter(
                is_active=True,
                module__is_active=True,
                module__course__is_active=True,
            )
            .select_related("module", "module__course")
            .order_by("module_id", "order_index")
        )

    def get_serializer_class(self):
        return LessonTheorySerializer
