from common.models import UUIDPublicIdMixin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

User = settings.AUTH_USER_MODEL


def _next_order_index(model_cls, **filters):
    """
    Следующий порядковый номер в рамках queryset
    """
    max_val = model_cls.objects.filter(**filters).aggregate(
        m=models.Max("order_index")
    )["m"]
    return (max_val or 0) + 1


MODULE_ORDER_HELP = _(
    "Порядок среди всех уроков контейнера (теория, тесты, задачи с кодом)"
)

VIDEO_URL_HELP = _("Ссылка на YouTube, Rutube или VK Видео (необязательно)")


def _lesson_video_upload_to(instance, filename):
    return f"lesson_videos/{instance.__class__.__name__.lower()}/{filename}"


def _validate_module_order_index(instance):
    from content.lesson_parent import validate_lesson_order_index

    validate_lesson_order_index(instance)


def _save_module_lesson_order(instance):
    from content.lesson_parent import save_lesson_order

    save_lesson_order(instance)


def _delete_module_lesson(instance):
    from content.lesson_parent import delete_lesson_with_order_shift

    delete_lesson_with_order_shift(instance)


def _clean_lesson_parent(instance):
    from content.lesson_parent import validate_lesson_parent

    validate_lesson_parent(instance)


class Technology(UUIDPublicIdMixin, models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Название технологии")
    )

    class Meta:
        verbose_name = _("Технология")
        verbose_name_plural = _("Технологии")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Course(UUIDPublicIdMixin, models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Название курса"))
    slug = models.SlugField(
        max_length=200, unique=True, verbose_name=_("URL адрес")
    )
    description = models.TextField(verbose_name=_("Описание"))
    image = models.ImageField(
        upload_to="courses/images/",
        verbose_name=_("Обложка курса"),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата создания")
    )
    technology = models.ManyToManyField(
        Technology,
        blank=True,
        verbose_name=_("Технологии"),
        related_name="courses",
    )
    mentor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentored_courses",
        verbose_name=_("Ментор курса"),
        limit_choices_to={"role__in": ("mentor", "admin")},
    )

    class Meta:
        verbose_name = _("Курс")
        verbose_name_plural = _("Курсы")
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.title))
        super().save(*args, **kwargs)


class Module(UUIDPublicIdMixin, models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name=_("Курс"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Название модуля"))
    description = models.TextField(
        verbose_name=_("Описание модуля"), blank=True
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    indexes = [
        models.Index(fields=["course", "order_index"]),
    ]

    class Meta:
        verbose_name = _("Модуль")
        verbose_name_plural = _("Модули")
        ordering = ("order_index",)
        unique_together = ("course", "order_index")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order_index = _next_order_index(
                Module, course_id=self.course_id
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        course = self.course
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        affected_modules = Module.objects.filter(
            course=course, order_index__gt=deleted_index
        )
        for module in affected_modules:
            module.order_index -= 1
            module.save()


class Exam(UUIDPublicIdMixin, models.Model):
    """Контрольная работа (КР) — контейнер заданий с таймером и правилами."""

    class NavigationMode(models.TextChoices):
        FREE = "free", _("Свободная навигация")
        LINEAR = "linear", _("Строго по порядку")

    class TabPolicy(models.TextChoices):
        LOG_ONLY = "log_only", _("Только логирование")
        WARN = "warn", _("Предупреждения")

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Курс"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(verbose_name=_("Описание"), blank=True)
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер в курсе"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    duration_minutes = models.PositiveIntegerField(
        default=45,
        verbose_name=_("Длительность (мин)"),
        help_text=_("Таймер с момента «Начать»"),
    )
    navigation_mode = models.CharField(
        max_length=10,
        choices=NavigationMode.choices,
        default=NavigationMode.FREE,
        verbose_name=_("Навигация между заданиями"),
    )
    tab_policy = models.CharField(
        max_length=10,
        choices=TabPolicy.choices,
        default=TabPolicy.LOG_ONLY,
        verbose_name=_("Политика переключения вкладок"),
    )
    tab_warn_limit = models.PositiveSmallIntegerField(
        default=2,
        verbose_name=_("Лимит предупреждений"),
        help_text=_("После лимита — автосдача с текущими ответами"),
    )
    mentor_unlock_required = models.BooleanField(
        default=False,
        verbose_name=_("Нужно разрешение ментора"),
        help_text=_("Доступ к старту только после одобрения ментора"),
    )
    pass_score_percent = models.PositiveSmallIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name=_("Порог зачёта (%)"),
    )
    prerequisite_modules = models.ManyToManyField(
        Module,
        blank=True,
        related_name="required_for_exams",
        verbose_name=_("Обязательные модули"),
        help_text=_("Нужно пройти эти модули перед стартом КР"),
    )

    class Meta:
        verbose_name = _("Контрольная работа")
        verbose_name_plural = _("Контрольные работы")
        ordering = ("order_index",)
        unique_together = ("course", "order_index")

    def __str__(self):
        return f"{self.course.title} — {self.title}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order_index = _next_order_index(
                Exam, course_id=self.course_id
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        course = self.course
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        for exam in Exam.objects.filter(
            course=course, order_index__gt=deleted_index
        ):
            exam.order_index -= 1
            exam.save(update_fields=["order_index"])


class LessonTheory(UUIDPublicIdMixin, models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_theories",
        verbose_name=_("Модуль"),
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="lessons_theories",
        verbose_name=_("Контрольная"),
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_lessons_theories",
        verbose_name=_("Курс"),
        null=True,
        blank=True,
        help_text=_("Урок на уровне курса (без модуля и КР)"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Название урока"))
    content = models.TextField(verbose_name=_("Содержание урока"))
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Ссылка на видео"),
        help_text=VIDEO_URL_HELP,
    )
    video_file = models.FileField(
        upload_to=_lesson_video_upload_to,
        blank=True,
        null=True,
        verbose_name=_("Видеофайл"),
        help_text=_("Или загрузите MP4/WebM как объяснение"),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
        help_text=MODULE_ORDER_HELP,
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    indexes = [
        models.Index(fields=["module", "order_index"]),
    ]

    class Meta:
        verbose_name = _("Теоретический урок")
        verbose_name_plural = _("Теоретические уроки")
        ordering = ("order_index",)

    def __str__(self):
        parent = self.module or self.exam or self.course
        return f"{parent} - {self.title}"

    def save(self, *args, **kwargs):
        _save_module_lesson_order(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        _delete_module_lesson(self)

    def clean(self):
        super().clean()
        _clean_lesson_parent(self)
        _validate_module_order_index(self)


class LessonRadioQuestion(UUIDPublicIdMixin, models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_radio_questions",
        verbose_name=_("Модуль"),
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="lessons_radio_questions",
        verbose_name=_("Контрольная"),
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_lessons_radio_questions",
        verbose_name=_("Курс"),
        null=True,
        blank=True,
    )
    title = models.CharField(
        max_length=200, verbose_name=_("Название вопроса")
    )
    question_text = models.TextField(verbose_name=_("Текст вопроса"))
    explanation = models.TextField(
        verbose_name=_("Пояснение"),
        blank=True,
        help_text=_("Пояснение правильного ответа, показываемое после ответа"),
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Ссылка на видео"),
        help_text=VIDEO_URL_HELP,
    )
    video_file = models.FileField(
        upload_to=_lesson_video_upload_to,
        blank=True,
        null=True,
        verbose_name=_("Видеофайл"),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
        help_text=MODULE_ORDER_HELP,
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Баллы"),
        help_text=_("Количество баллов за правильный ответ"),
    )

    class Meta:
        verbose_name = _("Урок с радио-кнопками")
        verbose_name_plural = _("Уроки с радио-кнопками")
        ordering = ("order_index",)

    def __str__(self):
        parent = self.module or self.exam or self.course
        return f"{parent} - {self.title}"

    def save(self, *args, **kwargs):
        _save_module_lesson_order(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        _delete_module_lesson(self)

    def clean(self):
        super().clean()
        _clean_lesson_parent(self)
        _validate_module_order_index(self)

    def get_correct_answer(self):
        return self.answers.filter(is_correct=True).first()


class RadioAnswerOption(UUIDPublicIdMixin, models.Model):
    question = models.ForeignKey(
        LessonRadioQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Вопрос"),
    )
    text = models.CharField(max_length=500, verbose_name=_("Текст ответа"))
    is_correct = models.BooleanField(
        default=False, verbose_name=_("Правильный ответ")
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
    )

    class Meta:
        verbose_name = _("Вариант ответа")
        verbose_name_plural = _("Варианты ответов")
        ordering = ("order_index",)
        unique_together = ("question", "order_index")

    def __str__(self):
        return f"{self.question.title[:50]} - {self.text[:50]}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order_index = _next_order_index(
                RadioAnswerOption, question_id=self.question_id
            )
        super().save(*args, **kwargs)


class LessonCheckBoxQuestion(UUIDPublicIdMixin, models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_checkbox_questions",
        verbose_name=_("Модуль"),
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="lessons_checkbox_questions",
        verbose_name=_("Контрольная"),
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_lessons_checkbox_questions",
        verbose_name=_("Курс"),
        null=True,
        blank=True,
    )
    title = models.CharField(
        max_length=200, verbose_name=_("Название вопроса")
    )
    question_text = models.TextField(verbose_name=_("Текст вопроса"))
    explanation = models.TextField(
        verbose_name=_("Пояснение"),
        blank=True,
        help_text=_("Пояснение правильных ответов, показываемое после ответа"),
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Ссылка на видео"),
        help_text=VIDEO_URL_HELP,
    )
    video_file = models.FileField(
        upload_to=_lesson_video_upload_to,
        blank=True,
        null=True,
        verbose_name=_("Видеофайл"),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
        help_text=MODULE_ORDER_HELP,
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Баллы"),
        help_text=_("Количество баллов за полностью правильный ответ"),
    )

    indexes = [
        models.Index(fields=["module", "order_index"]),
    ]

    class Meta:
        verbose_name = _("Урок с чекбоксами")
        verbose_name_plural = _("Уроки с чекбоксами")
        ordering = ("order_index",)

    def __str__(self):
        parent = self.module or self.exam or self.course
        return f"{parent} - {self.title}"

    def save(self, *args, **kwargs):
        _save_module_lesson_order(self)
        super().save(*args, **kwargs)

    def get_correct_answers(self):
        return self.answers.filter(is_correct=True)

    def delete(self, *args, **kwargs):
        _delete_module_lesson(self)

    def clean(self):
        super().clean()
        _clean_lesson_parent(self)
        _validate_module_order_index(self)


class CheckBoxAnswerOption(UUIDPublicIdMixin, models.Model):
    question = models.ForeignKey(
        LessonCheckBoxQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Вопрос"),
    )
    text = models.CharField(max_length=500, verbose_name=_("Текст ответа"))
    is_correct = models.BooleanField(
        default=False, verbose_name=_("Правильный ответ")
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
    )

    class Meta:
        verbose_name = _("Вариант ответа для чекбокса")
        verbose_name_plural = _("Варианты ответов для чекбоксов")
        ordering = ("order_index",)
        unique_together = ("question", "order_index")

    def __str__(self):
        return f"{self.question.title[:50]} - {self.text[:50]}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order_index = _next_order_index(
                CheckBoxAnswerOption, question_id=self.question_id
            )
        super().save(*args, **kwargs)


class CodingChallenge(UUIDPublicIdMixin, models.Model):
    """Задача по программированию"""

    DIFFICULTY_CHOICES = [
        ("beginner", _("Начинающий")),
        ("easy", _("Легкий")),
        ("medium", _("Средний")),
        ("hard", _("Сложный")),
        ("expert", _("Эксперт")),
    ]

    title = models.CharField(max_length=200, verbose_name=_("Название задачи"))
    description = models.TextField(verbose_name=_("Описание задачи"))
    instructions = models.TextField(
        verbose_name=_("Инструкция по выполнению"),
        help_text=_("Подробная инструкция для пользователя"),
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Ссылка на видео"),
        help_text=VIDEO_URL_HELP,
    )
    video_file = models.FileField(
        upload_to=_lesson_video_upload_to,
        blank=True,
        null=True,
        verbose_name=_("Видеофайл"),
    )
    initial_code = models.TextField(
        verbose_name=_("Начальный код"),
        blank=True,
        help_text=_("Код, который будет показан пользователю как стартовый"),
    )
    solution_template = models.TextField(
        verbose_name=_("Шаблон решения"),
        help_text=_("Шаблон с местами для заполнения {{placeholder}}"),
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        verbose_name=_("Сложность"),
    )
    points = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name=_("Баллы"),
    )
    time_limit_ms = models.PositiveIntegerField(
        default=2000,
        verbose_name=_("Лимит времени (мс)"),
        help_text=_("Максимальное время выполнения решения в миллисекундах"),
    )
    memory_limit_mb = models.PositiveIntegerField(
        default=256,
        verbose_name=_("Лимит памяти (МБ)"),
        help_text=_("Максимальное использование памяти в мегабайтах"),
    )

    # Связи с существующими моделями
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenges",
        verbose_name=_("Курс"),
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="challenges",
        verbose_name=_("Модуль"),
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="challenges",
        verbose_name=_("Контрольная"),
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
        help_text=MODULE_ORDER_HELP,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата создания")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Дата обновления")
    )

    class Meta:
        verbose_name = _("Задача")
        verbose_name_plural = _("Задачи")
        ordering = ("order_index", "difficulty", "title")
        indexes = [
            models.Index(fields=["course", "order_index"]),
            models.Index(fields=["module", "order_index"]),
            models.Index(fields=["difficulty", "is_active"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from content.lesson_parent import sync_coding_challenge_course

        sync_coding_challenge_course(self)
        _save_module_lesson_order(self)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        _clean_lesson_parent(self)
        _validate_module_order_index(self)

    def get_max_score(self):
        """Максимальный возможный балл за задачу"""
        return self.points

    @property
    def success_rate(self):
        """Процент успешных решений"""
        total = self.submissions.filter(status="completed").count()
        if total == 0:
            return 0
        successful = self.submissions.filter(
            status="completed",
            tests_passed=F("total_tests"),
            total_tests__gt=0,
        ).count()
        return round((successful / total) * 100, 1)

    def delete(self, *args, **kwargs):
        _delete_module_lesson(self)


class TestCase(UUIDPublicIdMixin, models.Model):

    challenge = models.ForeignKey(
        CodingChallenge,
        on_delete=models.CASCADE,
        related_name="test_cases",
        verbose_name=_("Задача"),
    )
    input_data = models.TextField(
        verbose_name=_("Входные данные"),
        help_text=_("Входные данные для теста"),
    )
    expected_output = models.TextField(
        verbose_name=_("Ожидаемый вывод"),
        help_text=_("Ожидаемый вывод программы"),
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_("Скрытый тест"),
        help_text=_("Скрытые тесты не показываются пользователю"),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
    )

    class Meta:
        verbose_name = _("Тестовый случай")
        verbose_name_plural = _("Тестовые случаи")
        ordering = ("order_index",)
        unique_together = ("challenge", "order_index")

    def __str__(self):
        return f"{self.challenge.title} - Тест {self.order_index}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order_index = _next_order_index(
                TestCase, challenge_id=self.challenge_id
            )
        super().save(*args, **kwargs)

    def clean(self):
        if self.pk:
            return

        max_order = TestCase.objects.filter(
            challenge=self.challenge
        ).aggregate(models.Max("order_index"))["order_index__max"]

        if max_order and self.order_index > max_order + 1:
            raise ValidationError(
                {
                    "order_index": _(
                        "Порядковый номер не может быть больше %(max)d "
                        "(следующая доступная позиция)"
                    )
                    % {"max": max_order + 1}
                }
            )
