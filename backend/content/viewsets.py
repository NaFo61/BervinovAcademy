from django.utils.translation import gettext_lazy as _
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
    """
    ViewSet для управления курсами.

    Доступные действия:
    - list — получение списка всех активных курсов
    - retrieve — получение детальной информации о конкретном курсе по slug

    Особенности:
    - Доступен без авторизации (AllowAny)
    - В списке возвращаются только базовые поля курса
    - При детальном просмотре добавляются модули и уроки
    - Автоматическая генерация slug из названия
    - Сортировка по дате создания (новые сверху)
    - Используется prefetch_related для оптимизации запросов

    Поля курса:
    - title — название курса
    - slug — уникальный URL-идентификатор
    - description — полное описание
    - image — обложка курса
    - is_active — статус активности
    - created_at — дата создания
    - technology — связанные технологии (многие ко многим)
    - modules — модули курса (только в детальном просмотре)
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"

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
    - course_id — идентификатор родительского курса
    - lessons_theories — теоретические уроки модуля
    """

    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Возвращает queryset активных модулей активных курсов.
        Оптимизирует запросы к связанным моделям.
        """
        return (
            Module.objects.filter(is_active=True, course__is_active=True)
            .select_related("course")
            .prefetch_related("lessons_theories")
            .order_by("course_id", "order_index")
        )

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
    - module_id — идентификатор родительского модуля
    """

    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Возвращает queryset активных уроков из активных модулей и курсов.
        Оптимизирует загрузку связанных модулей и курсов.
        """
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
        """Возвращает единый сериализатор для всех действий."""
        return LessonTheorySerializer


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
    - submit — отправка решения задачи (POST)
    - my_submissions — получение истории отправок пользователя (GET)

    Особенности:
    - Просмотр задач доступен без авторизации
    - Отправка решений требует авторизации (IsAuthenticated)
    - Поддерживается фильтрация по курсу, модулю и сложности
    - Сортировка по порядковому номеру и сложности
    - В детальном просмотре показываются только не скрытые тесты
    - Автоматическая проверка решений (заглушка, требует доработки)

    Поля задачи:
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
    - course_id — ID курса
    - module_id — ID модуля
    - difficulty — уровень сложности (beginner, easy, medium, hard, expert)
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        """
        Возвращает queryset активных задач с поддержкой фильтрации.
        Фильтры: course_id, module_id, difficulty.
        Сортировка: сначала по order_index, затем по difficulty.
        """
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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="submit",
    )
    def submit(self, request, slug=None):
        """
        Отправка решения задачи пользователем.

        Процесс:
        1. Получение кода из запроса
        2. Создание записи о попытке (статус pending)
        3. Выполнение кода на тестах
        4. Обновление статуса и результатов
        5. Возврат результата проверки

        Требования:
        - Пользователь должен быть авторизован
        - Код не может быть пустым
        - Задача должна быть активной

        Возвращаемые данные:
        - submission_id — уникальный идентификатор попытки
        - status — статус проверки
        - tests_passed — количество пройденных тестов
        - total_tests — общее количество тестов
        - error_message — сообщение об ошибке (если есть)
        - test_results — детальные результаты тестов
        """
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
        """
        Выполнение кода на тестовых случаях.

        ВНИМАНИЕ: Это временная заглушка!
        В реальной реализации необходимо:
        1. Использовать Celery для асинхронного выполнения
        2. Запускать код в изолированном Docker-контейнере
        3. Ограничивать ресурсы (время, память)
        4. Безопасно обрабатывать пользовательский код
        5. Поддерживать разные языки программирования

        Текущая заглушка:
        - Считает все тесты пройденными
        - Не выполняет реальный код
        - Не проверяет корректность решения
        """
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
        """
        Получение истории отправок текущего пользователя по задаче.

        Особенности:
        - Требуется авторизация пользователя
        - Возвращает последние 20 отправок
        - Сортировка от новых к старым
        - Не включает код решения (только мета-информацию)

        Возвращаемые данные для каждой отправки:
        - submission_id — уникальный идентификатор
        - status — статус проверки
        - tests_passed — количество пройденных тестов
        - total_tests — общее количество тестов
        - submitted_at — дата и время отправки
        """
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
