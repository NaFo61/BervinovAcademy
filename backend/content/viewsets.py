from common.drf import UUID_LOOKUP_REGEX
from common.lesson_access import filter_lessons_for_user
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from content.challenge_stats import get_course_challenge_stats
from content.lesson_querysets import public_lesson_parent_q
from content.models import (
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonShortAnswer,
    LessonTheory,
    Module,
)
from content.serializers import (
    CodingChallengeDetailSerializer,
    CodingChallengeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    LessonCheckBoxDetailSerializer,
    LessonCheckBoxListSerializer,
    LessonRadioDetailSerializer,
    LessonRadioListSerializer,
    LessonShortAnswerDetailSerializer,
    LessonShortAnswerListSerializer,
    LessonTheorySerializer,
    ModuleDetailSerializer,
    ModuleListSerializer,
)


class CourseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления курсами.

    Доступные действия:
    - list — получение списка всех активных курсов
    - retrieve — детальная информация о курсе по public_id (UUID)

    Особенности:
    - Каталог курсов доступен без авторизации (AllowAny)
    - Полный текст уроков — только авторизованным + enrollment
      (см. Lesson* / CodingChallenge ViewSets)
    - В списке возвращаются только базовые поля курса
    - При детальном просмотре — структура (заголовки), без HTML уроков
    - Автоматическая генерация slug из названия
    - Сортировка по дате создания (новые сверху)
    - Используется prefetch_related для оптимизации запросов

    Поля курса:
    - title — название курса
    - public_id — публичный UUID
    - slug — человекочитаемый URL-идентификатор
    - description — полное описание
    - image — обложка курса
    - is_active — статус активности
    - created_at — дата создания
    - technology — связанные технологии (многие ко многим)
    - modules — модули курса (только в детальном просмотре)
    """

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        """
        Возвращает queryset активных курсов с оптимизацией запросов.
        Предварительно загружаются технологии, модули и уроки модулей.

        Фильтр list: ``?technology=Python`` — по названию технологии (без учёта регистра).
        """
        qs = (
            Course.objects.filter(is_active=True)
            .prefetch_related(
                "technology",
                "modules",
                "exams",
                "modules__lessons_theories",
                "modules__lessons_radio_questions",
                "modules__lessons_radio_questions__answers",
                "modules__lessons_checkbox_questions",
                "modules__lessons_checkbox_questions__answers",
                "modules__lessons_short_answers",
                "modules__challenges",
                "exams__lessons_theories",
                "exams__lessons_radio_questions",
                "exams__lessons_checkbox_questions",
                "exams__lessons_short_answers",
                "exams__challenges",
            )
            .order_by("-created_at")
        )
        if self.action == "list":
            tech = (self.request.query_params.get("technology") or "").strip()
            if tech:
                qs = qs.filter(technology__name__iexact=tech).distinct()
        return qs

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия:
        - retrieve — детальный сериализатор с модулями
        - list — компактный сериализатор для списка
        """
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer


class ModuleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления модулями курсов.

    Доступные действия:
    - list — получение списка всех активных модулей
    - retrieve — получение детальной информации о модуле

    Особенности:
    - Доступен без авторизации (AllowAny)
    - Фильтруются только модули активных курсов
    - В списке возвращаются базовые поля
    - При детальном просмотре добавляются уроки модуля
    - Сортировка по курсу и порядковому номеру
    - Используется select_related и prefetch_related для оптимизации

    Поля модуля:
    - title — название модуля
    - description — описание модуля
    - order_index — порядковый номер в курсе
    - is_active — статус активности
    - course_public_id — UUID родительского курса
    - Фильтр списка: query-параметр course_public_id=
    - lessons_theories — теоретические уроки модуля
    """

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        """
        Возвращает queryset активных модулей активных курсов.
        Оптимизирует запросы к связанным моделям.
        """
        queryset = Module.objects.filter(
            is_active=True, course__is_active=True
        ).select_related("course")
        course_pub = self.request.query_params.get("course_public_id")
        if course_pub:
            queryset = queryset.filter(course__public_id=course_pub)
        return queryset.prefetch_related(
            "lessons_theories",
            "lessons_radio_questions",
            "lessons_radio_questions__answers",
            "lessons_checkbox_questions",
            "lessons_checkbox_questions__answers",
            "challenges",
        ).order_by("course_id", "order_index")

    def get_serializer_class(self):
        """
        Выбирает сериализатор:
        - retrieve — детальный с уроками
        - list — компактный без уроков
        """
        if self.action == "retrieve":
            return ModuleDetailSerializer
        return ModuleListSerializer


class LessonTheoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Теория: JWT + enrollment / attempt (анти-скрапинг)."""

    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = (
            LessonTheory.objects.filter(is_active=True)
            .filter(public_lesson_parent_q())
            .select_related(
                "module", "module__course", "exam", "exam__course", "course"
            )
        )
        queryset = filter_lessons_for_user(queryset, self.request.user)
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        exam_pub = self.request.query_params.get("exam_public_id")
        if exam_pub:
            queryset = queryset.filter(exam__public_id=exam_pub)
        return queryset.order_by("order_index")

    def get_serializer_class(self):
        return LessonTheorySerializer


class LessonRadioQuestionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Radio-вопросы: JWT + enrollment / attempt."""

    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = (
            LessonRadioQuestion.objects.filter(is_active=True)
            .filter(public_lesson_parent_q())
            .select_related(
                "module", "module__course", "exam", "exam__course", "course"
            )
        )
        queryset = filter_lessons_for_user(queryset, self.request.user)
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        exam_pub = self.request.query_params.get("exam_public_id")
        if exam_pub:
            queryset = queryset.filter(exam__public_id=exam_pub)
        return queryset.prefetch_related("answers").order_by("order_index")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonRadioDetailSerializer
        return LessonRadioListSerializer


class LessonCheckBoxQuestionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Checkbox-вопросы: JWT + enrollment / attempt."""

    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = (
            LessonCheckBoxQuestion.objects.filter(is_active=True)
            .filter(public_lesson_parent_q())
            .select_related(
                "module", "module__course", "exam", "exam__course", "course"
            )
        )
        queryset = filter_lessons_for_user(queryset, self.request.user)
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        exam_pub = self.request.query_params.get("exam_public_id")
        if exam_pub:
            queryset = queryset.filter(exam__public_id=exam_pub)
        return queryset.prefetch_related("answers").order_by("order_index")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonCheckBoxDetailSerializer
        return LessonCheckBoxListSerializer


class LessonShortAnswerViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Краткий ответ: JWT + enrollment / attempt."""

    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = (
            LessonShortAnswer.objects.filter(is_active=True)
            .filter(public_lesson_parent_q())
            .select_related(
                "module", "module__course", "exam", "exam__course", "course"
            )
        )
        queryset = filter_lessons_for_user(queryset, self.request.user)
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        exam_pub = self.request.query_params.get("exam_public_id")
        if exam_pub:
            queryset = queryset.filter(exam__public_id=exam_pub)
        return queryset.order_by("order_index")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonShortAnswerDetailSerializer
        return LessonShortAnswerListSerializer


class CodingChallengeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Задачи с кодом: JWT + enrollment / attempt.

    Отправка кода — ``POST /api/progress/code/``.
    ``course-stats`` остаётся публичным (агрегаты без текста заданий).
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = (
            CodingChallenge.objects.filter(is_active=True)
            .filter(public_lesson_parent_q())
            .select_related(
                "module", "module__course", "exam", "exam__course", "course"
            )
        )
        queryset = filter_lessons_for_user(queryset, self.request.user)

        course_pub = self.request.query_params.get("course_public_id")
        if course_pub:
            queryset = queryset.filter(course__public_id=course_pub)

        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)

        exam_pub = self.request.query_params.get("exam_public_id")
        if exam_pub:
            queryset = queryset.filter(exam__public_id=exam_pub)

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
        detail=False,
        methods=["get"],
        url_path="course-stats",
        permission_classes=[AllowAny],
    )
    def course_stats(self, request):
        """
        Статистика задач с кодом по курсу.

        Query: ``course_slug=python-backend`` или ``course_public_id=<uuid>``.
        """
        slug = (request.query_params.get("course_slug") or "").strip()
        course_pub = (
            request.query_params.get("course_public_id") or ""
        ).strip()
        if bool(slug) == bool(course_pub):
            raise ValidationError(
                {
                    "detail": "Укажите ровно один параметр: course_slug или course_public_id."
                }
            )

        qs = Course.objects.filter(is_active=True)
        try:
            if slug:
                course = qs.get(slug=slug)
            else:
                course = qs.get(public_id=course_pub)
        except Course.DoesNotExist as exc:
            raise NotFound("Курс не найден.") from exc

        return Response(get_course_challenge_stats(course))
