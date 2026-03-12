from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode


class Technology(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Название технологии")
    )

    class Meta:
        verbose_name = _("Технология")
        verbose_name_plural = _("Технологии")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Course(models.Model):
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


class Module(models.Model):
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


class LessonTheory(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_theories",
        verbose_name=_("Модуль"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Название урока"))
    content = models.TextField(verbose_name=_("Содержание урока"))
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    indexes = [
        models.Index(fields=["module", "order_index"]),
    ]

    class Meta:
        verbose_name = _("Теоретический урок")
        verbose_name_plural = _("Теоретические уроки")
        ordering = ("order_index",)
        unique_together = ("module", "order_index")

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def delete(self, *args, **kwargs):
        module = self.module
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        LessonTheory.objects.filter(
            module=module, order_index__gt=deleted_index
        ).update(order_index=models.F("order_index") - 1)

    def clean(self):
        if not self.pk:
            max_order = LessonTheory.objects.filter(
                module=self.module
            ).aggregate(models.Max("order_index"))["order_index__max"]

            if max_order and self.order_index > max_order + 1:
                raise ValidationError(
                    {
                        "order_index": _(
                            "Порядковый номер не "
                            "может быть больше %(max)d "
                            "(следующая доступная позиция)"
                        )
                        % {"max": max_order + 1}
                    }
                )


class LessonRadioQuestion(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_radio_questions",
        verbose_name=_("Модуль"),
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
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
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
        unique_together = ("module", "order_index")

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def get_correct_answer(self):
        return self.answers.filter(is_correct=True).first()


class AnswerOption(models.Model):
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


class LessonCheckBoxQuestion(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_checkbox_questions",
        verbose_name=_("Модуль"),
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
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Порядковый номер"),
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
        unique_together = ("module", "order_index")

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def get_correct_answers(self):
        return self.answers.filter(is_correct=True)

    def delete(self, *args, **kwargs):
        module = self.module
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        LessonCheckBoxQuestion.objects.filter(
            module=module, order_index__gt=deleted_index
        ).update(order_index=models.F("order_index") - 1)


class CheckBoxAnswerOption(models.Model):
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
