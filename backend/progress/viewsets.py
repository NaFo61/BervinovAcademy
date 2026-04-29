from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CodeSubmission, UserAnswerCheckBox, UserAnswerRadio
from .serializers import (
    CodeSubmissionSerializer,
    UserAnswerCheckBoxSerializer,
    UserAnswerRadioSerializer,
)


class UserAnswerRadioViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    API для работы с ответами пользователя на radio-вопросы (с единственным выбором).

    Предоставляет следующие возможности:
    - GET /progress/radio-answers/ — получить список всех ответов текущего пользователя
    - GET /progress/radio-answers/{id}/ — получить детали конкретного ответа
    - POST /progress/radio-answers/ — создать новый ответ на radio-вопрос

    Особенности:
    - Автоматически проверяет правильность ответа при сохранении
    - Рассчитывает заработанные баллы
    - Ограничивает количество попыток (можно настроить в модели)
    - Все ответы привязаны к авторизованному пользователю
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerRadioSerializer

    def get_queryset(self):
        """
        Возвращает только ответы текущего авторизованного пользователя.
        Это обеспечивает изоляцию данных между пользователями.
        """
        return UserAnswerRadio.objects.filter(user=self.request.user)


class UserAnswerCheckBoxViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    API для работы с ответами пользователя на checkbox-вопросы (с множественным выбором).

    Предоставляет следующие возможности:
    - GET /progress/checkbox-answers/ — получить список всех ответов текущего пользователя
    - GET /progress/checkbox-answers/{id}/ — получить детали конкретного ответа
    - POST /progress/checkbox-answers/submit/ — специальный эндпоинт для отправки ответов

    Особенности:
    - Поддерживает множественный выбор (несколько правильных ответов)
    - Автоматически проверяет корректность всех выбранных вариантов
    - Рассчитывает баллы (полные или частичные — настраивается)
    - Сохраняет историю всех попыток
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerCheckBoxSerializer

    def get_queryset(self):
        """
        Возвращает только ответы текущего авторизованного пользователя.
        Это обеспечивает изоляцию данных между пользователями.
        """
        return UserAnswerCheckBox.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="submit")
    def submit_answer(self, request):
        """
        Специальный эндпоинт для отправки ответа на checkbox-вопрос.

        Отличие от стандартного POST:
        - Возвращает упрощённый ответ только с результатом проверки
        - Удобен для интеграции с фронтендом
        - Проводит валидацию множественного выбора

        Возможные HTTP статусы:
        - 201 Created: ответ успешно сохранён
        - 400 Bad Request: ошибка валидации (неверные данные)

        Ошибки валидации могут возникать при:
        - Отсутствии обязательных полей
        - Выборе несуществующих вариантов ответа
        - Превышении лимита попыток
        - Попытке ответить на неактивный вопрос
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                {
                    "is_correct": instance.is_correct,
                    "points_earned": instance.points_earned,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCodeSubmissionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    API для управления отправками решений задач по программированию.

    Предоставляет следующие возможности:
    - GET /progress/code-submissions/ — получить список всех отправок текущего пользователя
    - GET /progress/code-submissions/{id}/ — получить детали конкретной отправки
    - POST /progress/code-submissions/ — создать новую отправку решения

    Особенности:
    - Хранит полный код решения пользователя
    - Фиксирует статус проверки (pending, running, completed, error)
    - Сохраняет результаты выполнения всех тестов
    - Отслеживает время выполнения и использование памяти
    - Поддерживает повторные отправки для одной задачи

    Примечания:
    - Для асинхронной проверки используйте эндпоинт /content/challenges/{slug}/submit/
    - Статус "pending" означает, что задача поставлена в очередь на проверку
    - Результаты тестов для скрытых тестов не раскрываются пользователю
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CodeSubmissionSerializer

    def get_queryset(self):
        """
        Возвращает только отправки текущего авторизованного пользователя.
        Это обеспечивает изоляцию данных между пользователями.

        Сортировка: от новых к старым (по умолчанию).
        """
        return CodeSubmission.objects.filter(user=self.request.user)
