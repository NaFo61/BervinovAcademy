"""Разблокировка достижений по статистике прогресса."""

from __future__ import annotations

import logging

from django.db import transaction

from .models import Achievement, UserAchievement
from .stats import get_user_progress_stats

logger = logging.getLogger(__name__)

_KIND_TO_STAT = {
    Achievement.Kind.TASKS_SOLVED: "tasks_solved",
    Achievement.Kind.THEORIES_READ: "theories_read",
    Achievement.Kind.COURSES_COMPLETED: "courses_completed",
    Achievement.Kind.QUIZZES_SOLVED: "quizzes_solved",
    Achievement.Kind.STREAK_DAYS: "streak_days",
}


def check_and_unlock_achievements(user) -> list[UserAchievement]:
    """Проверяет пороги и создаёт недостающие UserAchievement."""
    stats = get_user_progress_stats(user)
    unlocked: list[UserAchievement] = []

    existing_ids = set(
        UserAchievement.objects.filter(user=user).values_list(
            "achievement_id", flat=True
        )
    )

    for achievement in Achievement.objects.filter(is_active=True).order_by(
        "order_index", "threshold"
    ):
        if achievement.pk in existing_ids:
            continue
        stat_key = _KIND_TO_STAT.get(achievement.kind)
        if not stat_key:
            continue
        if stats.get(stat_key, 0) >= achievement.threshold:
            obj = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
            )
            unlocked.append(obj)
            existing_ids.add(achievement.pk)
            logger.info(
                "Достижение разблокировано: user=%s achievement=%s",
                user.pk,
                achievement.code,
            )

    return unlocked


def sync_achievements_for_user(user) -> list[UserAchievement]:
    with transaction.atomic():
        return check_and_unlock_achievements(user)
