"""
Прогресс пользователя: ответы на задания и отправки кода.

Общая схема (все под ``/api/progress/…``, нужен JWT):

- **Radio** — несколько ``POST /progress/radio/`` на один вопрос (новая
  попытка каждый раз; правки через API нет). Поле ``solved_ever`` — был ли
  хотя бы один верный ответ по этому вопросу у пользователя (для зачёта).

- **Checkbox** — ``POST /progress/checkbox/`` с телом ``question``,
  ``selected_answers`` (массив public_id; допускается пустой массив). Ответ —
  полный объект.

- **Код (coding challenge)** — ``POST /progress/code/`` с телом::

      {"challenge": "<uuid задачи>", "code": "<исходник>"}

  где ``challenge`` — это ``public_id`` из ``GET /api/content/challenges/…``
  (не числовой pk). Ответ — полная отправка (как при ``GET``).

- **Список своих отправок кода** — ``GET /progress/code/``;
  по одной задаче: ``GET /progress/code/?challenge_public_id=<uuid>``.
"""

import logging

from common.drf import UUID_LOOKUP_REGEX
from django.db.models import Exists, OuterRef
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    CodeSubmission,
    UserAnswerCheckBox,
    UserAnswerRadio,
    UserLessonTheoryRead,
)
from .serializers import (
    CodeSubmissionCreateSerializer,
    CodeSubmissionSerializer,
    UserAnswerCheckBoxSerializer,
    UserAnswerRadioSerializer,
    UserLessonTheoryReadSerializer,
)

logger = logging.getLogger(__name__)


class UserAnswerRadioViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Ответы на вопросы с одним вариантом (radio).

    - ``GET /progress/radio/`` — все попытки текущего пользователя
    - ``GET /progress/radio/{public_id}/`` — одна попытка
    - ``POST /progress/radio/`` — новая попытка (изменить старую нельзя)

    Тело POST: ``question`` и ``selected_answer`` — публичные UUID (строки),
    как в списках контента. В ответе ``solved_ever``: есть ли у пользователя
    хотя бы одна верная попытка по этому вопросу (включая текущую строку).

    При суммировании баллов по курсу не суммируйте ``points_earned`` по всем
    попыткам слепо — для «зачёта за вопрос» используйте ``solved_ever`` / max.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerRadioSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        solved_ever_sq = UserAnswerRadio.objects.filter(
            user=OuterRef("user"),
            question=OuterRef("question"),
            is_correct=True,
        )
        return (
            UserAnswerRadio.objects.filter(user=self.request.user)
            .select_related("question", "selected_answer")
            .annotate(solved_ever=Exists(solved_ever_sq))
            .order_by("-created_at")
        )


class UserAnswerCheckBoxViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Ответы на вопросы с несколькими вариантами (checkbox).

    - ``GET /progress/checkbox/`` — ответы текущего пользователя
    - ``GET /progress/checkbox/{public_id}/`` — детали
    - ``POST /progress/checkbox/`` — создать ответ (полный объект)

    Тело POST: ``question`` (UUID), ``selected_answers`` (массив UUID; может
    быть пустым — «ничего не выбрано»).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerCheckBoxSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        return (
            UserAnswerCheckBox.objects.filter(user=self.request.user)
            .select_related("question")
            .prefetch_related("selected_answers")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance, payload = serializer.submit(serializer.validated_data)
        if instance is None:
            return Response(payload, status=status.HTTP_200_OK)
        return Response(payload, status=status.HTTP_201_CREATED)


class UserCodeSubmissionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Отправки решений задач по программированию (код).

    **Как отправить код**

    1. Взять ``public_id`` задачи из ``GET /api/content/challenges/`` или
       ``GET /api/content/challenges/{public_id}/``.
    2. Авторизованным запросом::

           POST /api/progress/code/
           Content-Type: application/json

           {"challenge": "<public_id задачи>", "code": "def solve(): ..."}

       Ответ — полная модель отправки (как при ``GET``).

    3. Создаётся запись со статусом ``pending``; при настроенном Kafka сообщение
       уходит в воркер, а ответ из топика результатов подхватывает
       ``consume_code_submission_results`` (вердикт ``accepted`` → ``completed``).

    **Чтение**

    - ``GET /api/progress/code/`` — все свои отправки;
      фильтр по задаче: ``?challenge_public_id=<uuid>``.
    - ``GET /api/progress/code/{public_id}/`` — одна отправка.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CodeSubmissionSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        qs = (
            CodeSubmission.objects.filter(user=self.request.user)
            .select_related("challenge")
            .order_by("-submitted_at")
        )
        ch = self.request.query_params.get("challenge_public_id")
        if ch:
            qs = qs.filter(challenge__public_id=ch)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return CodeSubmissionCreateSerializer
        return CodeSubmissionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        logger.info(
            "Создана отправка кода: public_id=%s, пользователь=%s, "
            "задача=%s, длина кода=%s символов.",
            instance.public_id,
            getattr(request.user, "public_id", request.user.pk),
            instance.challenge.public_id,
            len(instance.code or ""),
        )
        out = CodeSubmissionSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(out.data, status=status.HTTP_201_CREATED)


class UserLessonTheoryReadViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Фиксация «прочитано» для теории.

    - ``GET /api/progress/theory/`` — все прочитанные уроки теории текущего пользователя
      (фильтр: ``?course_public_id=<uuid>``)
    - ``POST /api/progress/theory/`` — отметить теорию прочитанной

    POST body: ``{"lesson": "<public_id теории>"}``
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserLessonTheoryReadSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        qs = (
            UserLessonTheoryRead.objects.filter(user=self.request.user)
            .select_related(
                "lesson", "lesson__module", "lesson__module__course"
            )
            .order_by("-read_at")
        )
        course_pid = self.request.query_params.get("course_public_id")
        if course_pid:
            qs = qs.filter(lesson__module__course__public_id=course_pid)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.validated_data["lesson"]
        obj, created = UserLessonTheoryRead.objects.get_or_create(
            user=request.user,
            lesson=lesson,
        )
        out = UserLessonTheoryReadSerializer(
            obj, context=self.get_serializer_context()
        )
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
