from common.models import UUIDPublicIdMixin
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from content.models import Course

User = get_user_model()


class Enrollment(UUIDPublicIdMixin, models.Model):
    """Запись пользователя на курс."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("В процессе")
        COMPLETED = "completed", _("Завершён")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("Пользователь"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("Курс"),
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_("Статус"),
        db_index=True,
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Начало"),
        db_index=True,
    )
    last_activity_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Последняя активность"),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Завершён"),
    )

    class Meta:
        verbose_name = _("Запись на курс")
        verbose_name_plural = _("Записи на курсы")
        ordering = ("-last_activity_at",)
        unique_together = ("user", "course")
        indexes = [
            models.Index(fields=["user", "-last_activity_at"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.course.title} ({self.status})"
