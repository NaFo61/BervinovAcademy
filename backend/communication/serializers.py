from rest_framework import serializers

from users.models import User

from .models import Conference, ConferenceWhiteboard, UserNotification


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


class ConferenceWhiteboardSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    exported_by = serializers.SerializerMethodField()

    class Meta:
        model = ConferenceWhiteboard
        fields = (
            "image_url",
            "exported_at",
            "exported_by",
            "created_at",
        )

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
