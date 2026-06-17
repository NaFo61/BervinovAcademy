"""Сериализаторы достижений и статистики прогресса."""

from rest_framework import serializers

from .achievements import sync_achievements_for_user
from .models import Achievement, UserAchievement
from .stats import get_user_progress_stats


class UserProgressStatsSerializer(serializers.Serializer):
    tasks_solved = serializers.IntegerField()
    coding_solved = serializers.IntegerField()
    quizzes_solved = serializers.IntegerField()
    radio_solved = serializers.IntegerField()
    checkbox_solved = serializers.IntegerField()
    theories_read = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    streak_days = serializers.IntegerField()

    @classmethod
    def from_user(cls, user):
        return cls(get_user_progress_stats(user))


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = (
            "public_id",
            "code",
            "kind",
            "threshold",
            "title",
            "description",
            "emoji",
            "order_index",
        )
        read_only_fields = fields


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    unlocked = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = ("public_id", "achievement", "unlocked_at", "unlocked")
        read_only_fields = fields

    def get_unlocked(self, obj) -> bool:
        return True


class AchievementWithStatusSerializer(serializers.ModelSerializer):
    """Все достижения + флаг unlocked для конкретного пользователя."""

    unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = (
            "public_id",
            "code",
            "kind",
            "threshold",
            "title",
            "description",
            "emoji",
            "order_index",
            "unlocked",
            "unlocked_at",
        )
        read_only_fields = fields

    def get_unlocked(self, obj) -> bool:
        unlocks = self.context.get("user_unlocks") or {}
        return obj.pk in unlocks

    def get_unlocked_at(self, obj):
        unlocks = self.context.get("user_unlocks") or {}
        ts = unlocks.get(obj.pk)
        if ts is None:
            return None
        return ts.isoformat()


def build_achievements_payload(user):
    sync_achievements_for_user(user)

    unlocks = {
        row.achievement_id: row.unlocked_at
        for row in UserAchievement.objects.filter(user=user).select_related(
            "achievement"
        )
    }
    achievements = Achievement.objects.filter(is_active=True).order_by(
        "order_index", "threshold"
    )
    items = AchievementWithStatusSerializer(
        achievements,
        many=True,
        context={"user_unlocks": unlocks},
    ).data
    unlocked_count = sum(1 for item in items if item["unlocked"])
    return {
        "items": items,
        "unlocked_count": unlocked_count,
        "total_count": len(items),
    }
