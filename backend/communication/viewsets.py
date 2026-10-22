from common.drf import UUID_LOOKUP_REGEX
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mentoring.permissions import IsAdminRole, IsMentorOrAdmin

from . import services
from .livekit_tokens import LiveKitNotConfiguredError, issue_room_token
from .models import (
    BoardAsset,
    Conference,
    ConferenceLessonSummary,
    ConferenceWhiteboard,
    UserNotification,
)
from .serializers import (
    BoardAssetSerializer,
    ConferenceCreateSerializer,
    ConferenceLessonSummarySerializer,
    ConferenceSerializer,
    ConferenceWhiteboardSerializer,
    JoinConferenceSerializer,
    UserBriefSerializer,
    UserNotificationSerializer,
    WhiteboardTokenSerializer,
)
from .stats import build_call_stats, normalize_stats_days
from .whiteboard_tokens import (
    issue_whiteboard_sync_token,
    personal_studio_room_id,
)

User = get_user_model()


def _display_name(user) -> str:
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email or str(user.public_id)


class WhiteboardStudioTokenView(APIView):
    """Токен sync для личной доски вне созвона (не общая на всех)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.WHITEBOARD_ENABLED:
            return Response(
                {"detail": "Доска отключена."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # Комнату задаёт сервер: клиент не может попасть в чужую доску.
        room_id = personal_studio_room_id(request.user.public_id)
        ttl = settings.WHITEBOARD_TOKEN_TTL_SECONDS
        token = issue_whiteboard_sync_token(
            room_id,
            request.user.public_id,
            ttl_seconds=ttl,
        )
        payload = {
            "token": token,
            "room_id": room_id,
            "expires_in": ttl,
        }
        license_key = settings.TLDRAW_LICENSE_KEY
        if license_key:
            payload["license_key"] = license_key
        return Response(WhiteboardTokenSerializer(payload).data)


_BOARD_ASSET_EXT = frozenset(
    {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".txt",
        ".md",
        ".zip",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
    }
)
_BOARD_ASSET_MAX = 20 * 1024 * 1024


class BoardAssetUploadView(APIView):
    """Крупные файлы для доски → media/S3; на доске только URL."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "Нужен файл file."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from pathlib import Path

        name = getattr(upload, "name", "") or "file"
        ext = Path(name).suffix.lower()
        if ext not in _BOARD_ASSET_EXT:
            return Response(
                {"detail": "Этот тип файла нельзя загрузить на доску."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        size = int(getattr(upload, "size", 0) or 0)
        if size <= 0 or size > _BOARD_ASSET_MAX:
            return Response(
                {"detail": "Файл пустой или больше 20 МБ."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        asset = BoardAsset.objects.create(
            uploaded_by=request.user,
            file=upload,
            original_name=name[:255],
            content_type=(upload.content_type or "")[:128],
            size=size,
        )
        return Response(
            BoardAssetSerializer(asset, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


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
        qs = Conference.objects.select_related(
            "mentor",
            "guest",
            "whiteboard",
            "lesson_summary",
        ).filter(Q(mentor=user) | Q(guest=user))
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

    @action(detail=True, methods=["post"], url_path="whiteboard/token")
    def whiteboard_token(self, request, public_id=None):
        if not settings.WHITEBOARD_ENABLED:
            return Response(
                {"detail": "Доска отключена."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        conference = self.get_object()
        if not services.user_may_access_conference(request.user, conference):
            return Response(
                {"detail": "Нет доступа."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if conference.status in services.TERMINAL_STATUSES:
            return Response(
                {"detail": "Конференция уже завершена."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Как в Miro: на уроке работаем на постоянной доске ученика.
        room_id = personal_studio_room_id(conference.guest.public_id)
        ttl = settings.WHITEBOARD_TOKEN_TTL_SECONDS
        token = issue_whiteboard_sync_token(
            room_id,
            request.user.public_id,
            ttl_seconds=ttl,
        )
        payload = {
            "token": token,
            "room_id": room_id,
            "expires_in": ttl,
        }
        license_key = settings.TLDRAW_LICENSE_KEY
        if license_key:
            payload["license_key"] = license_key
        return Response(WhiteboardTokenSerializer(payload).data)

    @action(detail=True, methods=["get"], url_path="whiteboard")
    def whiteboard(self, request, public_id=None):
        if not settings.WHITEBOARD_ENABLED:
            return Response(
                {"detail": "Доска отключена."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        conference = self.get_object()
        if not services.user_may_access_conference(request.user, conference):
            return Response(
                {"detail": "Нет доступа."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            board = conference.whiteboard
        except ConferenceWhiteboard.DoesNotExist:
            return Response(
                {"detail": "Конспект ещё не сохранён."}, status=404
            )
        return Response(
            ConferenceWhiteboardSerializer(
                board, context={"request": request}
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="whiteboard/export",
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def whiteboard_export(self, request, public_id=None):
        if not settings.WHITEBOARD_ENABLED:
            return Response(
                {"detail": "Доска отключена."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        conference = self.get_object()
        if not services.user_may_access_conference(request.user, conference):
            return Response(
                {"detail": "Нет доступа."},
                status=status.HTTP_403_FORBIDDEN,
            )

        image = request.FILES.get("image")
        if not image:
            return Response(
                {"detail": "Нужен файл image (PNG)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image.size > settings.WHITEBOARD_MAX_EXPORT_BYTES:
            return Response(
                {"detail": "Файл слишком большой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
            return Response(
                {"detail": "Допустимы PNG, JPEG или WebP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        snapshot_json = None
        raw_snapshot = request.data.get("snapshot")
        if raw_snapshot:
            if isinstance(raw_snapshot, (dict, list)):
                snapshot_json = raw_snapshot
            else:
                import json

                try:
                    snapshot_json = json.loads(raw_snapshot)
                except json.JSONDecodeError:
                    return Response(
                        {"detail": "Некорректный snapshot JSON."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        board, _created = ConferenceWhiteboard.objects.update_or_create(
            conference=conference,
            defaults={
                "image": image,
                "snapshot_json": snapshot_json,
                "exported_by": request.user,
            },
        )
        return Response(
            ConferenceWhiteboardSerializer(
                board, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="lesson-summary",
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def lesson_summary(self, request, public_id=None):
        conference = self.get_object()
        if not services.user_may_access_conference(request.user, conference):
            return Response(
                {"detail": "Нет доступа."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            try:
                summary = conference.lesson_summary
            except ConferenceLessonSummary.DoesNotExist:
                return Response(
                    {"detail": "Конспект ещё не создан."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(ConferenceLessonSummarySerializer(summary).data)

        if request.user != conference.mentor:
            return Response(
                {"detail": "Конспект может запросить только ментор."},
                status=status.HTTP_403_FORBIDDEN,
            )

        audio = request.FILES.get("audio")
        if not audio:
            return Response(
                {"detail": "Нужен файл audio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        max_bytes = int(
            getattr(
                settings,
                "LESSON_SUMMARY_MAX_AUDIO_BYTES",
                80 * 1024 * 1024,
            )
        )
        if audio.size > max_bytes:
            return Response(
                {"detail": "Аудио слишком большое."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ctype = (audio.content_type or "").lower()
        if ctype and not (
            ctype.startswith("audio/")
            or ctype.startswith("video/")
            or ctype
            in {
                "application/octet-stream",
                "application/ogg",
            }
        ):
            return Response(
                {"detail": "Ожидается аудиофайл."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary, _created = ConferenceLessonSummary.objects.update_or_create(
            conference=conference,
            defaults={
                "audio": audio,
                "transcript": "",
                "summary_md": "",
                "status": ConferenceLessonSummary.Status.PENDING,
                "error_message": "",
                "created_by": request.user,
            },
        )
        from .tasks import process_lesson_summary_task

        process_lesson_summary_task.delay(summary.pk)
        return Response(
            ConferenceLessonSummarySerializer(summary).data,
            status=status.HTTP_202_ACCEPTED,
        )

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


class AdminCallStatsView(APIView):
    """``GET /api/communication/admin/call-stats/?days=7`` — сводка звонков."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        days = normalize_stats_days(request.query_params.get("days"))
        return Response(build_call_stats(days=days))
