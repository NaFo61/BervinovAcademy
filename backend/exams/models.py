from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from content.models import Exam

User = settings.AUTH_USER_MODEL


class ExamAttempt(UUIDPublicIdMixin, models.Model):
    """Попытка прохождения контрольной."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", _("В процессе")
        SUBMITTED = "submitted", _("Сдана")
        EXPIRED = "expired", _("Время вышло")
        CANCELLED = "cancelled", _("Отменена")

    class SubmitReason(models.TextChoices):
        MANUAL = "manual", _("Сдал сам")
        TIMEOUT = "timeout", _("Истекло время")
        WARN_LIMIT = "warn_limit", _("Лимит предупреждений")
        MENTOR = "mentor", _("Завершил ментор")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exam_attempts",
        verbose_name=_("Пользователь"),
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("Контрольная"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    submit_reason = models.CharField(
        max_length=20,
        choices=SubmitReason.choices,
        blank=True,
    )
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    focus_warn_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Попытка КР")
        verbose_name_plural = _("Попытки КР")
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["user", "exam", "-started_at"]),
            models.Index(fields=["exam", "status", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.exam.title} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.IN_PROGRESS


class ExamAccessGrant(UUIDPublicIdMixin, models.Model):
    """Разрешение ментора: доступ к КР или переписывание."""

    class GrantType(models.TextChoices):
        UNLOCK = "unlock", _("Открыть доступ")
        RETAKE = "retake", _("Разрешить переписать")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exam_access_grants",
        verbose_name=_("Ученик"),
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="access_grants",
        verbose_name=_("Контрольная"),
    )
    grant_type = models.CharField(
        max_length=10,
        choices=GrantType.choices,
        default=GrantType.RETAKE,
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_exam_access",
        verbose_name=_("Выдал"),
    )
    note = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Разрешение на КР")
        verbose_name_plural = _("Разрешения на КР")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} — {self.exam.title} ({self.grant_type})"


class ExamFocusEvent(UUIDPublicIdMixin, models.Model):
    """Лог ухода с вкладки / потери фокуса."""

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name="focus_events",
        verbose_name=_("Попытка"),
    )
    event_type = models.CharField(max_length=32, default="visibility_hidden")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Событие фокуса")
        verbose_name_plural = _("События фокуса")
        ordering = ("created_at",)


class ExamAttemptStep(UUIDPublicIdMixin, models.Model):
    """Ответ ученика на шаг КР в рамках попытки."""

    class StepKind(models.TextChoices):
        THEORY = "theory", _("Теория")
        RADIO = "radio", _("Radio")
        CHECKBOX = "checkbox", _("Checkbox")
        CODING = "coding", _("Код")

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=_("Попытка"),
    )
    step_kind = models.CharField(max_length=10, choices=StepKind.choices)
    content_public_id = models.UUIDField(db_index=True)
    order_index = models.PositiveIntegerField(default=1)
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)
    max_points = models.PositiveIntegerField(default=0)
    payload = models.JSONField(default=dict, blank=True)
    code_submission = models.ForeignKey(
        "progress.CodeSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_attempt_steps",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Шаг попытки КР")
        verbose_name_plural = _("Шаги попытки КР")
        ordering = ("order_index", "updated_at")
        unique_together = ("attempt", "step_kind", "content_public_id")

    def __str__(self):
        return f"{self.attempt_id} — {self.step_kind} {self.content_public_id}"
