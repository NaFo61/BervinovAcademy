from common.models import UUIDPublicIdMixin
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
)

User = get_user_model()


class UserAnswerRadio(UUIDPublicIdMixin, models.Model):
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
        # Несколько попыток на пару (user, question); зачёт «решено» — если
        # хотя бы одна попытка с is_correct=True (см. API solved_ever).
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


class UserAnswerCheckBox(UUIDPublicIdMixin, models.Model):
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


class CodeSubmission(UUIDPublicIdMixin, models.Model):
    """Отправка решения пользователя"""

    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        ("pending", _("В очереди")),
        ("running", _("Выполняется")),
        ("completed", _("Завершено")),
        ("error", _("Ошибка")),
        ("timeout", _("Превышено время")),
        ("memory_limit", _("Превышена память")),
    ]

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
    exam_attempt = models.ForeignKey(
        "exams.ExamAttempt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="code_submissions",
        verbose_name=_("Попытка КР"),
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
        if self.status == self.STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def is_successful(self):
        """Успешно ли решена задача"""
        return self.status == self.STATUS_COMPLETED

    def get_score_earned(self):
        """Полученные баллы за решение"""
        if self.is_successful():
            return self.challenge.points
        return 0


class UserLessonTheoryRead(UUIDPublicIdMixin, models.Model):
    """Фиксация факта, что пользователь открыл (прочитал) теорию."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="theory_reads",
        verbose_name=_("Пользователь"),
    )
    lesson = models.ForeignKey(
        LessonTheory,
        on_delete=models.CASCADE,
        related_name="user_reads",
        verbose_name=_("Теоретический урок"),
    )
    read_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Прочитано в"),
        db_index=True,
    )

    class Meta:
        verbose_name = _("Прочтение теории")
        verbose_name_plural = _("Прочтения теории")
        ordering = ("-read_at",)
        unique_together = ("user", "lesson")
        indexes = [
            models.Index(fields=["user", "lesson"]),
            models.Index(fields=["lesson", "-read_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.lesson.title}"


class Achievement(UUIDPublicIdMixin, models.Model):
    """Шаблон достижения (порог по типу активности)."""

    class Kind(models.TextChoices):
        TASKS_SOLVED = "tasks_solved", _("Решено задач")
        THEORIES_READ = "theories_read", _("Прочитано теорий")
        COURSES_COMPLETED = "courses_completed", _("Завершено курсов")
        QUIZZES_SOLVED = "quizzes_solved", _("Решено тестов")
        STREAK_DAYS = "streak_days", _("Дней подряд")

    code = models.SlugField(
        max_length=64,
        unique=True,
        verbose_name=_("Код"),
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        verbose_name=_("Тип"),
        db_index=True,
    )
    threshold = models.PositiveIntegerField(
        verbose_name=_("Порог"),
        help_text=_("Минимальное значение метрики для разблокировки"),
    )
    title = models.CharField(max_length=120, verbose_name=_("Название"))
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
    )
    emoji = models.CharField(
        max_length=16,
        default="🏆",
        verbose_name=_("Эмодзи"),
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Порядок"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
    )

    class Meta:
        verbose_name = _("Достижение")
        verbose_name_plural = _("Достижения")
        ordering = ("order_index", "threshold", "code")
        indexes = [
            models.Index(fields=["kind", "threshold"]),
        ]

    def __str__(self):
        return self.title


class UserAchievement(UUIDPublicIdMixin, models.Model):
    """Факт разблокировки достижения пользователем."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name=_("Пользователь"),
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="user_unlocks",
        verbose_name=_("Достижение"),
    )
    unlocked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Разблокировано"),
        db_index=True,
    )

    class Meta:
        verbose_name = _("Достижение пользователя")
        verbose_name_plural = _("Достижения пользователей")
        ordering = ("-unlocked_at",)
        unique_together = ("user", "achievement")
        indexes = [
            models.Index(fields=["user", "-unlocked_at"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.achievement.title}"
