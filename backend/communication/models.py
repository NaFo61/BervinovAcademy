from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class Conference(UUIDPublicIdMixin, models.Model):
    """Видеоконференция ментор ↔ участник (1-на-1)."""

    class Status(models.TextChoices):
        WAITING = "waiting", _("Ожидание")
        ACTIVE = "active", _("Идёт")
        COMPLETED = "completed", _("Завершена")
        DECLINED = "declined", _("Отклонена")
        CANCELLED = "cancelled", _("Отменена")
        EXPIRED = "expired", _("Истекла")

    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_conferences",
        verbose_name=_("Ментор"),
    )
    guest = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="guest_conferences",
        verbose_name=_("Участник"),
    )
    room_name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_("Комната LiveKit"),
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
        verbose_name=_("Статус"),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    mentor_in_room = models.BooleanField(default=False, db_index=True)
    guest_in_room = models.BooleanField(default=False, db_index=True)
    mentor_joined_at = models.DateTimeField(null=True, blank=True)
    guest_joined_at = models.DateTimeField(null=True, blank=True)
    last_mentor_left_at = models.DateTimeField(null=True, blank=True)
    last_guest_left_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ended_conferences",
        verbose_name=_("Завершил"),
    )

    class Meta:
        verbose_name = _("Конференция")
        verbose_name_plural = _("Конференции")
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["mentor", "-created_at"],
                name="communicati_mentor__a8e4c2_idx",
            ),
            models.Index(
                fields=["guest", "-created_at"],
                name="communicati_guest_i_91f0ab_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="communicati_status_4b2f11_idx",
            ),
            models.Index(
                fields=["mentor_in_room", "last_mentor_left_at"],
                name="communicati_mentor__0bc8c3_idx",
            ),
        ]

    def __str__(self):
        return f"{self.mentor} → {self.guest} ({self.status})"


class UserNotification(UUIDPublicIdMixin, models.Model):
    """In-app уведомление пользователя."""

    class Kind(models.TextChoices):
        CONFERENCE_INVITE = "conference_invite", _("Приглашение на созвон")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Пользователь"),
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        verbose_name=_("Тип"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Заголовок"))
    body = models.TextField(blank=True, verbose_name=_("Текст"))
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Конференция"),
    )
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="communicati_user_id_6d8e21_idx",
            ),
            models.Index(
                fields=["user", "dismissed_at", "-created_at"],
                name="communicati_user_id_2c7a55_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user}: {self.title}"
