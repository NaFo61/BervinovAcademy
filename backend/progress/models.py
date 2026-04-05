import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    RadioAnswerOption,
)

User = get_user_model()


class UserAnswerRadio(models.Model):
    """Модель для отслеживания ответов пользователя на radio-вопросы"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="radio_answers",
        verbose_name=_("Пользователь"),
    )
    question = models.ForeignKey(
        LessonRadioQuestion,
        on_delete=models.CASCADE,
        related_name="user_answers",
        verbose_name=_("Вопрос"),
    )
    selected_answer = models.ForeignKey(
        RadioAnswerOption,
        on_delete=models.CASCADE,
        verbose_name=_("Выбранный ответ"),
    )
    is_correct = models.BooleanField(
        verbose_name=_("Правильно"),
        help_text=_("Был ли ответ правильным"),
    )
    points_earned = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Получено баллов"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата ответа"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления"),
    )

    class Meta:
        verbose_name = _("Ответ на radio-вопрос")
        verbose_name_plural = _("Ответы на radio-вопросы")
        ordering = ["-created_at"]
        unique_together = ("user", "question")  # Один ответ на вопрос
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        return (
            f"{self.user} - {self.question.title} - "
            f"{'✅' if self.is_correct else '❌'}"
        )

    def save(self, *args, **kwargs):
        # Автоматически определяем правильность ответа
        if not self.pk:  # Только при создании
            self.is_correct = self.selected_answer.is_correct
            if self.is_correct:
                self.points_earned = self.question.points
        super().save(*args, **kwargs)


class UserAnswerCheckBox(models.Model):
    """Модель для отслеживания ответов пользователя на checkbox-вопросы"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="checkbox_answers",
        verbose_name=_("Пользователь"),
    )
    question = models.ForeignKey(
        LessonCheckBoxQuestion,
        on_delete=models.CASCADE,
        related_name="user_answers",
        verbose_name=_("Вопрос"),
    )
    selected_answers = models.ManyToManyField(
        CheckBoxAnswerOption,
        verbose_name=_("Выбранные ответы"),
        related_name="user_answers",
    )
    is_correct = models.BooleanField(
        verbose_name=_("Полностью правильно"),
        help_text=_("Были ли все выбранные ответы правильными"),
        default=False,
    )
    points_earned = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Получено баллов"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата ответа"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления"),
    )

    class Meta:
        verbose_name = _("Ответ на checkbox-вопрос")
        verbose_name_plural = _("Ответы на checkbox-вопросы")
        ordering = ["-created_at"]
        unique_together = ("user", "question")  # Один ответ на вопрос
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        return (
            f"{self.user} - {self.question.title} - "
            f"{'✅' if self.is_correct else '❌'}"
        )

    def calculate_correctness(self):
        """Вычисляет, правильный ли ответ"""
        correct_answers = set(self.question.answers.filter(is_correct=True))
        selected_answers = set(self.selected_answers.all())

        return selected_answers == correct_answers

    def calculate_points(self):
        """Вычисляет полученные баллы"""
        if self.calculate_correctness():
            return self.question.points
        return 0

    def save(self, *args, **kwargs):
        # Для новых объектов вычисляем правильность
        if not self.pk:
            super().save(
                *args, **kwargs
            )  # Сначала сохраняем, чтобы можно было добавить many-to-many
        else:
            # При обновлении пересчитываем
            self.is_correct = self.calculate_correctness()
            self.points_earned = (
                self.calculate_points() if self.is_correct else 0
            )
            super().save(*args, **kwargs)


class CodeSubmission(models.Model):
    """Отправка решения пользователя"""

    STATUS_CHOICES = [
        ("pending", _("В очереди")),
        ("running", _("Выполняется")),
        ("completed", _("Завершено")),
        ("error", _("Ошибка")),
        ("timeout", _("Превышено время")),
        ("memory_limit", _("Превышена память")),
    ]

    # Уникальный идентификатор для отслеживания
    submission_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("ID отправки"),
    )

    # Связи
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="code_submissions",
        verbose_name=_("Пользователь"),
    )
    challenge = models.ForeignKey(
        CodingChallenge,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Задача"),
    )

    # Код и результат
    code = models.TextField(verbose_name=_("Код решения"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Статус"),
        db_index=True,
    )

    # Результаты тестирования
    tests_passed = models.PositiveIntegerField(
        default=0, verbose_name=_("Пройдено тестов")
    )
    total_tests = models.PositiveIntegerField(
        default=0, verbose_name=_("Всего тестов")
    )

    # Ошибки
    error_message = models.TextField(
        blank=True, verbose_name=_("Сообщение об ошибке")
    )

    # Детали по каждому тесту (JSON)
    test_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Результаты тестов"),
        help_text=_("Детальные результаты по каждому тесту"),
    )

    # Временные метки
    submitted_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Время отправки"), db_index=True
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Время завершения")
    )

    class Meta:
        verbose_name = _("Отправка решения")
        verbose_name_plural = _("Отправки решений")
        ordering = ("-submitted_at",)
        indexes = [
            models.Index(fields=["user", "challenge", "-submitted_at"]),
            models.Index(fields=["challenge", "status", "-submitted_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.challenge} - {self.submitted_at}"

    def save(self, *args, **kwargs):
        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def is_successful(self):
        """Успешно ли решена задача"""
        return self.status == "completed"

    def get_score_earned(self):
        """Полученные баллы за решение"""
        if self.is_successful():
            return self.challenge.points
        return 0
