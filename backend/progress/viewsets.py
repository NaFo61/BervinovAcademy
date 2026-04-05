# progress/viewsets.py (новый файл)

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
    """API для ответов на radio-вопросы"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerRadioSerializer

    def get_queryset(self):
        return UserAnswerRadio.objects.filter(user=self.request.user)


class UserAnswerCheckBoxViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """API для ответов на checkbox-вопросы"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerCheckBoxSerializer

    def get_queryset(self):
        return UserAnswerCheckBox.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="submit")
    def submit_answer(self, request):
        """Отправка ответа на checkbox-вопрос"""
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
    """API для отправок решений задач"""

    permission_classes = [IsAuthenticated]
    serializer_class = CodeSubmissionSerializer

    def get_queryset(self):
        return CodeSubmission.objects.filter(user=self.request.user)
