from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models import F, Func, Q
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class LessonAccess(UUIDPublicIdMixin, models.Model):
    """Галочка «занятия». Подписка Pro её не заменяет."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_access",
        verbose_name=_("Ученик"),
    )
    enabled = models.BooleanField(default=False, verbose_name=_("Включён"))
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_lesson_access",
        verbose_name=_("Кто выдал"),
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Обновлён")
    )

    class Meta:
        verbose_name = _("Доступ к занятиям")
        verbose_name_plural = _("Доступы к занятиям")

    def __str__(self):
        state = "да" if self.enabled else "нет"
        return f"{self.user} ({state})"


class TutorSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="tutor_settings",
        verbose_name=_("Ментор"),
    )
    timezone = models.CharField(
        max_length=64,
        default="Europe/Moscow",
        verbose_name=_("Часовой пояс"),
    )

    class Meta:
        verbose_name = _("Настройки ментора")
        verbose_name_plural = _("Настройки менторов")

    def __str__(self):
        return f"{self.user} ({self.timezone})"


class AvailabilityWindow(UUIDPublicIdMixin, models.Model):
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="availability_windows",
        verbose_name=_("Ментор"),
    )
    weekday = models.PositiveSmallIntegerField(
        verbose_name=_("День недели"),
        help_text=_("0 — понедельник, 6 — воскресенье"),
    )
    start_time = models.TimeField(verbose_name=_("Начало"))
    end_time = models.TimeField(verbose_name=_("Конец"))

    class Meta:
        verbose_name = _("Окно записи")
        verbose_name_plural = _("Окна записи")
        ordering = ("weekday", "start_time")
        constraints = [
            models.CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="tutoring_window_end_after_start",
            ),
            models.CheckConstraint(
                check=Q(weekday__gte=0, weekday__lte=6),
                name="tutoring_window_weekday",
            ),
        ]

    def __str__(self):
        return f"{self.mentor} {self.weekday} {self.start_time}"


class LessonTariff(UUIDPublicIdMixin, models.Model):
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_tariffs",
        verbose_name=_("Ментор"),
    )
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Длительность, мин")
    )
    price_kop = models.PositiveIntegerField(verbose_name=_("Цена, копейки"))

    class Meta:
        verbose_name = _("Цена занятия")
        verbose_name_plural = _("Цены занятий")
        constraints = [
            models.UniqueConstraint(
                fields=("mentor", "duration_minutes"),
                name="tutoring_tariff_duration_unique",
            ),
            models.CheckConstraint(
                check=Q(price_kop__gt=0),
                name="tutoring_tariff_price_positive",
            ),
        ]

    def __str__(self):
        return f"{self.duration_minutes} мин / {self.price_kop}"


class TutoringLesson(UUIDPublicIdMixin, models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", _("Записан")
        DONE = "done", _("Проведён")
        MISSED = "missed", _("Не пришёл")
        CANCELLED = "cancelled", _("Отменён")

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tutoring_lessons",
        verbose_name=_("Ученик"),
    )
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentoring_lessons",
        verbose_name=_("Ментор"),
    )
    starts_at = models.DateTimeField(verbose_name=_("Начало"), db_index=True)
    ends_at = models.DateTimeField(verbose_name=_("Конец"))
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Длительность, мин")
    )
    price_kop = models.PositiveIntegerField(verbose_name=_("Цена, копейки"))
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.BOOKED,
        verbose_name=_("Статус"),
        db_index=True,
    )
    homework_status = models.CharField(
        max_length=16,
        choices=[
            ("", _("Не отмечено")),
            ("done", _("Сдал")),
            ("not_done", _("Не сдал")),
        ],
        default="",
        blank=True,
        verbose_name=_("Домашка"),
        db_index=True,
    )
    learned_note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Чему научился"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Занятие")
        verbose_name_plural = _("Занятия")
        ordering = ("starts_at",)
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=F("starts_at")),
                name="tutoring_lesson_ends_after_start",
            ),
            ExclusionConstraint(
                name="tutoring_lesson_no_overlap",
                expressions=[
                    (F("mentor"), RangeOperators.EQUAL),
                    (
                        Func(
                            "starts_at",
                            "ends_at",
                            function="tstzrange",
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(
                    status__in=[
                        "booked",
                        "done",
                        "missed",
                    ]
                ),
            ),
        ]

    def __str__(self):
        return f"{self.student} {self.starts_at}"


class LedgerEntry(UUIDPublicIdMixin, models.Model):
    class Kind(models.TextChoices):
        CHARGE = "charge", _("Начисление")
        PAYMENT = "payment", _("Оплата")
        ADJUSTMENT = "adjustment", _("Правка")

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_ledger",
        verbose_name=_("Ученик"),
    )
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_ledger",
        verbose_name=_("Ментор"),
    )
    lesson = models.ForeignKey(
        TutoringLesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
        verbose_name=_("Занятие"),
    )
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        verbose_name=_("Тип"),
    )
    amount_kop = models.IntegerField(
        verbose_name=_("Сумма, копейки"),
        help_text=_("Оплата плюс, долг за занятие минус"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Проводка")
        verbose_name_plural = _("Проводки")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.kind} {self.amount_kop}"


class PaymentClaim(UUIDPublicIdMixin, models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Ждёт решения")
        CONFIRMED = "confirmed", _("Подтверждена")
        REJECTED = "rejected", _("Отклонена")

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payment_claims",
        verbose_name=_("Ученик"),
    )
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_payment_claims",
        verbose_name=_("Ментор"),
    )
    amount_kop = models.PositiveIntegerField(verbose_name=_("Сумма, копейки"))
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Статус"),
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Решение")
    )

    class Meta:
        verbose_name = _("Заявка «Я оплатил»")
        verbose_name_plural = _("Заявки «Я оплатил»")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.student} {self.amount_kop} {self.status}"


class LessonReminder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Ждёт")
        SENT = "sent", _("Отправлено")
        CANCELLED = "cancelled", _("Снято")
        SKIPPED = "skipped", _("Без Telegram")

    lesson = models.ForeignKey(
        TutoringLesson,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name=_("Занятие"),
    )
    offset_minutes = models.PositiveIntegerField(
        verbose_name=_("За сколько минут")
    )
    send_at = models.DateTimeField(
        verbose_name=_("Когда послать"), db_index=True
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Статус"),
    )

    class Meta:
        verbose_name = _("Напоминание")
        verbose_name_plural = _("Напоминания")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "offset_minutes"),
                name="tutoring_reminder_offset_unique",
            )
        ]

    def __str__(self):
        return f"{self.lesson_id} -{self.offset_minutes}м"
