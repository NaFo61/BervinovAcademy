from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode


class Technology(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Technology name")
    )

    class Meta:
        verbose_name = _("Technology")
        verbose_name_plural = _("Technologies")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Course title"))
    slug = models.SlugField(
        max_length=200, unique=True, verbose_name=_("URL address")
    )
    description = models.TextField(verbose_name=_("Description"))
    image = models.ImageField(
        upload_to="courses/images/",
        verbose_name=_("Course cover"),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created at")
    )
    technology = models.ManyToManyField(
        Technology,
        blank=True,
        verbose_name=_("Technologies"),
        related_name="courses",
    )

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
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
        verbose_name=_("Course"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Module title"))
    description = models.TextField(
        verbose_name=_("Module description"), blank=True
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    indexes = [
        models.Index(fields=['course', 'order_index']),
    ]

    class Meta:
        verbose_name = _("Module")
        verbose_name_plural = _("Modules")
        ordering = ("order_index",)
        unique_together = ("course", "order_index")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def delete(self, *args, **kwargs):
        course = self.course
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        affected_modules = Module.objects.filter(
            course=course,
            order_index__gt=deleted_index
        )
        for module in affected_modules:
            module.order_index -= 1
            module.save()


class LessonTheory(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_theories",
        verbose_name=_("Module"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Lesson title"))
    content = models.TextField(verbose_name=_("Lesson content"))
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    indexes = [
        models.Index(fields=['module', 'order_index']),
    ]

    class Meta:
        verbose_name = _("Theory lesson")
        verbose_name_plural = _("Theory lessons")
        ordering = ("order_index",)
        unique_together = ("module", "order_index")

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def delete(self, *args, **kwargs):
        module = self.module
        deleted_index = self.order_index
        super().delete(*args, **kwargs)
        LessonTheory.objects.filter(
            module=module,
            order_index__gt=deleted_index
        ).update(order_index=models.F("order_index") - 1)

    def clean(self):
        if not self.pk:
            max_order = LessonTheory.objects.filter(
                module=self.module
            ).aggregate(models.Max('order_index'))['order_index__max']

            if max_order and self.order_index > max_order + 1:
                raise ValidationError({
                    'order_index': _(
                        'Order index cannot be more than '
                        '%(max)d (next available position)'
                    ) % {'max': max_order + 1}
                })



class LessonRadioQuestion(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_radio_questions",
        verbose_name=_("Module"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Question title"))
    question_text = models.TextField(verbose_name=_("Question text"))
    explanation = models.TextField(
        verbose_name=_("Explanation"),
        blank=True,
        help_text=_("Explanation of the correct answer shown after answering"),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Points"),
        help_text=_("Number of points for correct answer"),
    )

    class Meta:
        verbose_name = _("Radio question lesson")
        verbose_name_plural = _("Radio question lessons")
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
        verbose_name=_("Question"),
    )
    text = models.CharField(max_length=500, verbose_name=_("Answer text"))
    is_correct = models.BooleanField(
        default=False, verbose_name=_("Is correct answer")
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )

    class Meta:
        verbose_name = _("Answer option")
        verbose_name_plural = _("Answer options")
        ordering = ("order_index",)
        unique_together = ("question", "order_index")
        constraints = (
            models.UniqueConstraint(
                fields=("question",),
                condition=models.Q(is_correct=True),
                name="unique_correct_answer_per_radio_question",
            ),
        )

    def __str__(self):
        return f"{self.question.title[:50]} - {self.text[:50]}"

    def save(self, *args, **kwargs):
        if self.is_correct:
            AnswerOption.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk).update(is_correct=False)
        super().save(*args, **kwargs)


class LessonCheckBoxQuestion(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons_checkbox_questions",
        verbose_name=_("Module"),
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Question title")
    )
    question_text = models.TextField(
        verbose_name=_("Question text")
    )
    explanation = models.TextField(
        verbose_name=_("Explanation"),
        blank=True,
        help_text=_(
            "Explanation of the correct answers shown "
            "after answering"
        ),
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Points"),
        help_text=_(
            "Number of points for fully correct answer"
        ),
    )

    indexes = [
        models.Index(fields=['module', 'order_index']),
    ]

    class Meta:
        verbose_name = _("Checkbox question lesson")
        verbose_name_plural = _(
            "Checkbox question lessons"
        )
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
            module=module,
            order_index__gt=deleted_index
        ).update(order_index=models.F("order_index") - 1)


class CheckBoxAnswerOption(models.Model):
    question = models.ForeignKey(
        LessonCheckBoxQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Question"),
    )
    text = models.CharField(
        max_length=500,
        verbose_name=_("Answer text")
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name=_("Is correct answer")
    )
    order_index = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Order number"),
    )

    class Meta:
        verbose_name = _("Checkbox answer option")
        verbose_name_plural = _(
            "Checkbox answer options"
        )
        ordering = ("order_index",)
        unique_together = ("question", "order_index")

    def __str__(self):
        return (
            f"{self.question.title[:50]} - "
            f"{self.text[:50]}"
        )