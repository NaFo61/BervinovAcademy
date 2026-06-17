from rest_framework import serializers

from users.models import User

from .models import Conference, UserNotification


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
        )

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        if obj.started_at and obj.status == Conference.Status.ACTIVE:
            from django.utils import timezone

            return int((timezone.now() - obj.started_at).total_seconds())
        return None


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
