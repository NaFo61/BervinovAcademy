from common.drf import UUID_LOOKUP_REGEX
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import chat_services
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    DirectThreadSerializer,
)


class ChatThreadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX
    serializer_class = DirectThreadSerializer

    def get_queryset(self):
        return chat_services.threads_for_user(self.request.user)

    @action(detail=False, methods=["get"])
    def open(self, request):
        user_public_id = (request.query_params.get("user") or "").strip()
        course_public_id = (request.query_params.get("course") or "").strip()
        conference_public_id = (
            request.query_params.get("conference") or ""
        ).strip()
        thread = chat_services.open_thread(
            actor=request.user,
            user_public_id=user_public_id or None,
            course_public_id=course_public_id or None,
            conference_public_id=conference_public_id or None,
        )
        serializer = DirectThreadSerializer(
            thread, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unread_total(self, request):
        total = chat_services.total_unread_count(user=request.user)
        return Response({"total": total})

    @action(detail=True, methods=["post"])
    def read(self, request, public_id=None):
        thread = chat_services.thread_for_user(
            user=request.user,
            thread_public_id=public_id,
        )
        thread = chat_services.mark_thread_read(
            thread=thread, user=request.user
        )
        serializer = DirectThreadSerializer(
            thread, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, public_id=None):
        thread = chat_services.thread_for_user(
            user=request.user,
            thread_public_id=public_id,
        )

        if request.method == "GET":
            before_raw = request.query_params.get("before")
            before = None
            if before_raw:
                before = parse_datetime(before_raw)
                if before is None:
                    raise ValidationError(
                        {"before": "Некорректная дата ISO 8601."}
                    )
            try:
                limit = int(request.query_params.get("limit", 50))
            except (TypeError, ValueError):
                limit = 50

            rows, has_more = chat_services.list_thread_messages(
                thread=thread,
                before=before,
                limit=limit,
            )
            mark_read = request.query_params.get("mark_read", "1") != "0"
            if before is None and mark_read:
                chat_services.mark_thread_read(
                    thread=thread, user=request.user
                )
            return Response(
                {
                    "results": ChatMessageSerializer(rows, many=True).data,
                    "has_more": has_more,
                }
            )

        ser = ChatMessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        message = chat_services.create_text_message(
            thread=thread,
            sender=request.user,
            body=ser.validated_data["body"],
        )
        return Response(
            ChatMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class ChatMessageViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX
    serializer_class = ChatMessageSerializer
    http_method_names = ["patch", "delete", "head", "options"]

    def partial_update(self, request, public_id=None):
        message = chat_services.message_for_user(
            user=request.user,
            message_public_id=public_id,
        )
        ser = ChatMessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        message = chat_services.update_text_message(
            message=message,
            editor=request.user,
            body=ser.validated_data["body"],
        )
        return Response(ChatMessageSerializer(message).data)

    def destroy(self, request, public_id=None):
        message = chat_services.message_for_user(
            user=request.user,
            message_public_id=public_id,
        )
        message = chat_services.delete_text_message(
            message=message,
            deleter=request.user,
        )
        return Response(ChatMessageSerializer(message).data)
