from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from content.models import CodingChallenge, Course, LessonTheory, Module
from content.serializers import (
    CodingChallengeDetailSerializer,
    CodingChallengeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    LessonTheorySerializer,
    ModuleDetailSerializer,
    ModuleListSerializer,
)
from progress.models import CodeSubmission


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


class CodingChallengeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet для задач по программированию"""

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = CodingChallenge.objects.filter(is_active=True)

        # Фильтрация по курсу
        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Фильтрация по модулю
        module_id = self.request.query_params.get("module_id")
        if module_id:
            queryset = queryset.filter(module_id=module_id)

        # Фильтрация по сложности
        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset.order_by("order_index", "difficulty")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CodingChallengeDetailSerializer
        return CodingChallengeListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="submit",
    )
    def submit(self, request, slug=None):
        """Отправка решения задачи"""
        challenge = self.get_object()

        code = request.data.get("code", "").strip()
        if not code:
            return Response(
                {"error": _("Код не может быть пустым")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаем отправку
        submission = CodeSubmission.objects.create(
            user=request.user, challenge=challenge, code=code, status="pending"
        )

        # Здесь должна быть логика выполнения кода
        # Для минимальной версии просто помечаем как успешное
        # В реальном проекте нужно добавить очередь задач (Celery) и выполнение в Docker

        # Временная заглушка - выполняем тесты синхронно
        result = self._execute_code(submission)

        # Обновляем отправку
        for key, value in result.items():
            setattr(submission, key, value)
        submission.save()

        # Сериализуем ответ
        return Response(
            {
                "submission_id": submission.submission_id,
                "status": submission.status,
                "tests_passed": submission.tests_passed,
                "total_tests": submission.total_tests,
                "error_message": submission.error_message,
                "test_results": submission.test_results,
            }
        )

    def _execute_code(self, submission):
        """Выполнение кода (заглушка - нужно реализовать)"""
        challenge = submission.challenge
        test_cases = challenge.test_cases.all()

        result = {
            "status": "completed",
            "tests_passed": 0,
            "total_tests": test_cases.count(),
            "error_message": "",
            "test_results": {},
        }

        if result["total_tests"] == 0:
            result["status"] = "error"
            result["error_message"] = _("Нет тестов для проверки")
            return result

        # Заглушка - всегда проходит тесты
        # В реальной реализации здесь должен быть код выполнения в Docker
        result["tests_passed"] = result["total_tests"]

        for idx, test in enumerate(test_cases, 1):
            result["test_results"][f"test_{idx}"] = {
                "passed": True,
                "input": test.input_data,
                "expected": test.expected_output,
            }

        return result

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="my-submissions",
    )
    def my_submissions(self, request, slug=None):
        """История отправок пользователя по задаче"""
        challenge = self.get_object()

        submissions = challenge.submissions.filter(user=request.user).order_by(
            "-submitted_at"
        )[:20]

        return Response(
            [
                {
                    "submission_id": s.submission_id,
                    "status": s.status,
                    "tests_passed": s.tests_passed,
                    "total_tests": s.total_tests,
                    "submitted_at": s.submitted_at,
                }
                for s in submissions
            ]
        )
