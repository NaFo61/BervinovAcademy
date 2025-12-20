from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode


class Technology(models.Model):
    """Technologies"""

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Technology name")
    )

    class Meta:
        verbose_name = _("Technology")
        verbose_name_plural = _("Technologies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    """Courses"""

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
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            # Create slug from title using unidecode
            self.slug = slugify(unidecode(self.title))
        super().save(*args, **kwargs)


class Module(models.Model):
    """Course modules"""

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

    class Meta:
        verbose_name = _("Module")
        verbose_name_plural = _("Modules")
        ordering = ["order_index"]
        unique_together = ["course", "order_index"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonTheory(models.Model):
    """Module theory lessons"""

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

    class Meta:
        verbose_name = _("Theory lesson")
        verbose_name_plural = _("Theory lessons")
        ordering = ["order_index"]
        unique_together = ["module", "order_index"]

    def __str__(self):
        return f"{self.module.title} - {self.title}"
