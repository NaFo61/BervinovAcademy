from common.drf import UUID_LOOKUP_REGEX
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mentoring.permissions import IsMentorOrAdmin

from . import services
from .livekit_tokens import LiveKitNotConfiguredError, issue_room_token
from .models import Conference, UserNotification
from .serializers import (
    ConferenceCreateSerializer,
    ConferenceSerializer,
    JoinConferenceSerializer,
    UserBriefSerializer,
    UserNotificationSerializer,
)

User = get_user_model()


def _display_name(user) -> str:
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email or str(user.public_id)


class MentorUserSearchView(APIView):
    """Поиск пользователей для приглашения на созвон (только ментор)."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < 2:
            return Response([])
        qs = (
            User.objects.filter(
                Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
            .exclude(pk=request.user.pk)
            .order_by("first_name", "last_name")[:20]
        )
        return Response(UserBriefSerializer(qs, many=True).data)


class ConferenceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX
    serializer_class = ConferenceSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Conference.objects.select_related("mentor", "guest").filter(
            Q(mentor=user) | Q(guest=user)
        )
        role = self.request.query_params.get("role")
        if role == "mentor":
            qs = qs.filter(mentor=user)
        elif role == "guest":
            qs = qs.filter(guest=user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return ConferenceCreateSerializer
        if self.action == "join":
            return JoinConferenceSerializer
        return ConferenceSerializer

    def create(self, request, *args, **kwargs):
        ser = ConferenceCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        guest = ser.context["guest_user"]
        try:
            conference = services.create_conference(
                mentor=request.user,
                guest=guest,
            )
        except ValueError as exc:
            raise ValidationError({"guest": str(exc)}) from exc

        out = ConferenceSerializer(conference)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def _issue_join_payload(self, request, conference):
        if not services.user_may_access_conference(request.user, conference):
            return None, Response(
                {"detail": "Нет доступа к этой конференции."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if conference.status in services.TERMINAL_STATUSES:
            return None, Response(
                {"detail": "Конференция уже завершена."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = issue_room_token(
                room_name=conference.room_name,
                identity=str(request.user.public_id),
                name=_display_name(request.user),
            )
        except LiveKitNotConfiguredError as exc:
            return None, Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        services.mark_conference_joined(
            conference=conference,
            user=request.user,
        )
        conference.refresh_from_db()
        payload = {
            "token": token,
            "livekit_url": settings.LIVEKIT_URL,
            "room_name": conference.room_name,
            "conference": ConferenceSerializer(conference).data,
        }
        return payload, None

    @action(detail=True, methods=["post"])
    def join(self, request, public_id=None):
        conference = self.get_object()
        payload, error = self._issue_join_payload(request, conference)
        if error:
            return error
        return Response(payload)

    @action(detail=True, methods=["post"])
    def end(self, request, public_id=None):
        conference = self.get_object()
        if request.user.pk != conference.mentor_id:
            return Response(
                {"detail": "Завершить конференцию может только ментор."},
                status=status.HTTP_403_FORBIDDEN,
            )
        conference = services.end_conference(
            conference=conference,
            user=request.user,
        )
        return Response(ConferenceSerializer(conference).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, public_id=None):
        conference = self.get_object()
        if not services.user_may_access_conference(request.user, conference):
            return Response(
                {"detail": "Нет доступа."},
                status=status.HTTP_403_FORBIDDEN,
            )
        conference = services.mark_conference_left(
            conference=conference,
            user=request.user,
        )
        return Response(ConferenceSerializer(conference).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, public_id=None):
        conference = self.get_object()
        try:
            conference = services.decline_conference(
                conference=conference,
                user=request.user,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(ConferenceSerializer(conference).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, public_id=None):
        conference = self.get_object()
        try:
            conference = services.cancel_conference(
                conference=conference,
                user=request.user,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(ConferenceSerializer(conference).data)


class UserNotificationViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = UserNotificationSerializer
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_queryset(self):
        qs = (
            UserNotification.objects.filter(user=self.request.user)
            .select_related(
                "conference",
                "conference__mentor",
                "conference__guest",
            )
            .order_by("-created_at")
        )
        if self.request.query_params.get("unread") == "1":
            qs = qs.filter(read_at__isnull=True, dismissed_at__isnull=True)
        return qs[:50]

    @action(detail=True, methods=["post"])
    def read(self, request, public_id=None):
        from django.utils import timezone

        note = self.get_object()
        if not note.read_at:
            note.read_at = timezone.now()
            note.save(update_fields=["read_at"])
        return Response(UserNotificationSerializer(note).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, public_id=None):
        from django.utils import timezone

        note = self.get_object()
        if not note.dismissed_at:
            note.dismissed_at = timezone.now()
            note.save(update_fields=["dismissed_at"])
        if (
            note.kind == UserNotification.Kind.CONFERENCE_INVITE
            and note.conference_id
            and note.conference.status == Conference.Status.WAITING
            and request.user.pk == note.conference.guest_id
        ):
            services.decline_conference(
                conference=note.conference,
                user=request.user,
            )
        return Response(UserNotificationSerializer(note).data)


class LiveKitWebhookView(APIView):
    """Webhook endpoint для синхронизации статуса LiveKit room."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not (settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET):
            return Response(
                {"detail": "LiveKit не настроен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return Response(
                {"detail": "Нет подписи webhook."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from livekit.api import TokenVerifier, WebhookReceiver

        body = request.body.decode("utf-8")
        receiver = WebhookReceiver(
            TokenVerifier(
                settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET
            )
        )
        try:
            event = receiver.receive(body, token)
        except Exception:
            return Response(
                {"detail": "Некорректный webhook."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conference = services.apply_livekit_webhook_event(event)
        return Response(
            {
                "ok": True,
                "event": getattr(event, "event", None),
                "conference": (
                    str(conference.public_id) if conference else None
                ),
            }
        )
