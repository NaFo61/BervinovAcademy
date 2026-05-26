from common.drf import UUID_LOOKUP_REGEX
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from content.models import (
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
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
    - Доступен без авторизации (AllowAny)
    - В списке возвращаются только базовые поля курса
    - При детальном просмотре добавляются модули и уроки
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
        """
        return (
            Course.objects.filter(is_active=True)
            .prefetch_related(
                "technology",
                "modules",
                "modules__lessons_theories",
                "modules__lessons_radio_questions",
                "modules__lessons_radio_questions__answers",
                "modules__lessons_checkbox_questions",
                "modules__lessons_checkbox_questions__answers",
                "modules__challenges",
            )
            .order_by("-created_at")
        )

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
    """
    ViewSet для управления теоретическими уроками.

    Доступные действия:
    - list — получение списка всех активных уроков
    - retrieve — получение полного содержания урока

    Особенности:
    - Доступен без авторизации (AllowAny)
    - Фильтруются уроки активных модулей активных курсов
    - Содержит полный HTML-контент урока
    - Сортировка по модулю и порядковому номеру
    - Используется select_related для оптимизации

    Поля урока:
    - title — название урока
    - content — HTML-содержание урока
    - order_index — порядковый номер в модуле
    - is_active — статус активности
    - module_public_id — UUID родительского модуля
    - Фильтр списка: query-параметр module_public_id=
    """

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        """
        Возвращает queryset активных уроков из активных модулей и курсов.
        Оптимизирует загрузку связанных модулей и курсов.
        """
        queryset = LessonTheory.objects.filter(
            is_active=True,
            module__is_active=True,
            module__course__is_active=True,
        ).select_related("module", "module__course")
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        return queryset.order_by("module_id", "order_index")

    def get_serializer_class(self):
        """Возвращает единый сериализатор для всех действий."""
        return LessonTheorySerializer


class LessonRadioQuestionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Публичный каталог вопросов с одним вариантом ответа (radio)."""

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = LessonRadioQuestion.objects.filter(
            is_active=True,
            module__is_active=True,
            module__course__is_active=True,
        ).select_related("module", "module__course")
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        return queryset.prefetch_related("answers").order_by(
            "module_id", "order_index"
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonRadioDetailSerializer
        return LessonRadioListSerializer


class LessonCheckBoxQuestionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Публичный каталог вопросов с несколькими вариантами (checkbox)."""

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        queryset = LessonCheckBoxQuestion.objects.filter(
            is_active=True,
            module__is_active=True,
            module__course__is_active=True,
        ).select_related("module", "module__course")
        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)
        return queryset.prefetch_related("answers").order_by(
            "module_id", "order_index"
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonCheckBoxDetailSerializer
        return LessonCheckBoxListSerializer


class CodingChallengeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления задачами по программированию.

    Доступные действия:
    - list — получение списка задач с возможностью фильтрации
    - retrieve — получение детальной информации о задаче

    Особенности:
    - Просмотр задач доступен без авторизации
    - Отправка кода и история решений — в API прогресса:
      ``POST /api/progress/code/`` (тело: ``challenge`` = этот
      ``public_id``, поле ``code``). Список своих попыток по задаче:
      ``GET /api/progress/code/?challenge_public_id=…``
    - Поддерживается фильтрация по курсу, модулю и сложности
    - Сортировка по порядковому номеру и сложности
    - В детальном просмотре показываются только не скрытые тесты

    Поля задачи:
    - public_id — публичный UUID
    - title — название задачи
    - description — описание задачи
    - instructions — инструкция по выполнению
    - initial_code — стартовый код для пользователя
    - difficulty — уровень сложности
    - points — количество баллов за решение
    - time_limit_ms — ограничение по времени (мс)
    - memory_limit_mb — ограничение по памяти (МБ)
    - test_cases — тестовые случаи (только не скрытые)
    - user_solved — флаг, решил ли пользователь задачу

    Методы фильтрации (через query-параметры):
    - course_public_id — UUID курса
    - module_public_id — UUID модуля
    - difficulty — уровень сложности (beginner, easy, medium, hard, expert)
    """

    permission_classes = [AllowAny]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        """
        Возвращает queryset активных задач с поддержкой фильтрации.
        Фильтры: course_public_id, module_public_id, difficulty.
        Сортировка: сначала по order_index, затем по difficulty.
        """
        queryset = CodingChallenge.objects.filter(is_active=True)

        course_pub = self.request.query_params.get("course_public_id")
        if course_pub:
            queryset = queryset.filter(course__public_id=course_pub)

        module_pub = self.request.query_params.get("module_public_id")
        if module_pub:
            queryset = queryset.filter(module__public_id=module_pub)

        # Фильтрация по сложности
        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset.order_by("order_index", "difficulty")

    def get_serializer_class(self):
        """
        Выбирает сериализатор:
        - retrieve — детальный с тестами и информацией о решении
        - list — компактный для списка задач
        """
        if self.action == "retrieve":
            return CodingChallengeDetailSerializer
        return CodingChallengeListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Детальный просмотр задачи.
        Передает в сериализатор объект request для определения прав доступа.
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, context={"request": request}
        )
        return Response(serializer.data)
