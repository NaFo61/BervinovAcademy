from rest_framework import serializers

from users.models import User

from .models import (
    ChatMessage,
    Conference,
    ConferenceWhiteboard,
    DirectThread,
    UserNotification,
)


class UserBriefSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = (
            "public_id",
            "first_name",
            "last_name",
            "email",
            "role",
            "avatar",
        )


class ConferenceParticipantSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ("public_id", "first_name", "last_name", "avatar")


class ConferenceSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    mentor = ConferenceParticipantSerializer(read_only=True)
    guest = ConferenceParticipantSerializer(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    has_whiteboard = serializers.SerializerMethodField()
    whiteboard_exported_at = serializers.SerializerMethodField()

    class Meta:
        model = Conference
        fields = (
            "public_id",
            "mentor",
            "guest",
            "room_name",
            "status",
            "mentor_in_room",
            "guest_in_room",
            "created_at",
            "started_at",
            "ended_at",
            "duration_seconds",
            "has_whiteboard",
            "whiteboard_exported_at",
        )

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        if obj.started_at and obj.status == Conference.Status.ACTIVE:
            from django.utils import timezone

            return int((timezone.now() - obj.started_at).total_seconds())
        return None

    def get_has_whiteboard(self, obj):
        board = getattr(obj, "whiteboard", None)
        return bool(board and board.image)

    def get_whiteboard_exported_at(self, obj):
        board = getattr(obj, "whiteboard", None)
        if not board or not board.image:
            return None
        return board.exported_at


class ConferenceCreateSerializer(serializers.Serializer):
    guest = serializers.UUIDField(
        help_text="public_id приглашённого пользователя"
    )

    def validate_guest(self, value):
        try:
            guest = User.objects.get(public_id=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Пользователь не найден."
            ) from exc
        self.context["guest_user"] = guest
        return value


class JoinConferenceSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    livekit_url = serializers.CharField(read_only=True)
    room_name = serializers.CharField(read_only=True)
    conference = ConferenceSerializer(read_only=True)


class WhiteboardTokenSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    room_id = serializers.UUIDField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    license_key = serializers.CharField(
        read_only=True, required=False, allow_blank=True
    )


class ConferenceWhiteboardSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    exported_by = serializers.SerializerMethodField()
    has_snapshot = serializers.SerializerMethodField()
    license_key = serializers.SerializerMethodField()

    class Meta:
        model = ConferenceWhiteboard
        fields = (
            "image_url",
            "snapshot_json",
            "has_snapshot",
            "license_key",
            "exported_at",
            "exported_by",
            "created_at",
        )

    def get_has_snapshot(self, obj):
        return bool(obj.snapshot_json)

    def get_license_key(self, obj):
        from django.conf import settings

        return getattr(settings, "TLDRAW_LICENSE_KEY", "") or ""

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_exported_by(self, obj):
        if not obj.exported_by_id:
            return None
        return str(obj.exported_by.public_id)


class UserNotificationSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    conference = ConferenceSerializer(read_only=True)

    class Meta:
        model = UserNotification
        fields = (
            "public_id",
            "kind",
            "title",
            "body",
            "conference",
            "read_at",
            "dismissed_at",
            "created_at",
        )


class ChatParticipantSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ("public_id", "first_name", "last_name", "avatar", "role")


class ChatConferenceBriefSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    has_whiteboard = serializers.SerializerMethodField()

    class Meta:
        model = Conference
        fields = (
            "public_id",
            "status",
            "duration_seconds",
            "has_whiteboard",
        )

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        if obj.started_at and obj.status == Conference.Status.ACTIVE:
            from django.utils import timezone

            return int((timezone.now() - obj.started_at).total_seconds())
        return None

    def get_has_whiteboard(self, obj):
        board = getattr(obj, "whiteboard", None)
        return bool(board and board.image)


class ChatMessageSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    sender = ChatParticipantSerializer(read_only=True)
    conference = ChatConferenceBriefSerializer(read_only=True)
    system_payload = serializers.JSONField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "public_id",
            "kind",
            "sender",
            "body",
            "is_deleted",
            "edited_at",
            "show_edited",
            "conference",
            "system_event",
            "system_payload",
            "created_at",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["body"] = ""
        return data


class DirectThreadSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    mentor = ChatParticipantSerializer(read_only=True)
    student = ChatParticipantSerializer(read_only=True)
    other_participant = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = DirectThread
        fields = (
            "public_id",
            "mentor",
            "student",
            "other_participant",
            "last_message_at",
            "last_message_preview",
            "unread_count",
            "created_at",
        )

    def _request_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_other_participant(self, obj):
        user = self._request_user()
        if not user or not user.is_authenticated:
            return None
        other = obj.student if user.pk == obj.mentor_id else obj.mentor
        return ChatParticipantSerializer(other).data

    def get_last_message_preview(self, obj):
        msg = (
            obj.messages.select_related("sender")
            .order_by("-created_at")
            .first()
        )
        if not msg:
            return None
        if msg.is_deleted:
            return "Сообщение удалено"
        if msg.kind == ChatMessage.Kind.SYSTEM:
            return (msg.body or "")[:120]
        return (msg.body or "")[:120]

    def get_unread_count(self, obj):
        user = self._request_user()
        if not user or not user.is_authenticated:
            return 0
        from . import chat_services

        return chat_services.thread_unread_count(thread=obj, user=user)


class ChatMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=4000, trim_whitespace=True)
