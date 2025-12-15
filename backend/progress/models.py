from django.db import models
from django.contrib.auth import get_user_model


class Tecnology(models.Model):
    id = models.ForeignKey(User, on_delete=models.CASCADE)


from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Technology(models.Model):
    """Технологии"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название технологии")

    class Meta:
        verbose_name = "Технология"
        verbose_name_plural = "Технологии"
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """Курсы"""
    title = models.CharField(max_length=200, verbose_name="Название курса")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(verbose_name="Описание")
    cover_image = models.ImageField(
        upload_to='courses/covers/',
        verbose_name="Обложка курса",
        null=True,
        blank=True
    )
    is_public = models.BooleanField(default=False, verbose_name="Опубликован")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Module(models.Model):
    """Модули курса"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Название модуля")
    description = models.TextField(verbose_name="Описание модуля", blank=True)
    order_index = models.PositiveIntegerField(default=0, verbose_name="Порядковый номер")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        ordering = ['order_index']
        unique_together = ['course', 'order_index']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Уроки модуля"""
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="Модуль"
    )
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = models.TextField(verbose_name="Содержание урока")
    video_url = models.URLField(max_length=500, verbose_name="URL видео", blank=True)
    order_index = models.PositiveIntegerField(default=0, verbose_name="Порядковый номер")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['order_index']
        unique_together = ['module', 'order_index']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class MentorTechnology(models.Model):
    """Технологии, которыми владеет ментор"""
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_technologies',
        verbose_name="Ментор"
    )
    technology = models.ForeignKey(
        Technology,
        on_delete=models.CASCADE,
        related_name='mentors',
        verbose_name="Технология"
    )

    class Meta:
        verbose_name = "Технология ментора"
        verbose_name_plural = "Технологии менторов"
        unique_together = ['mentor', 'technology']  # Один ментор - одна запись по технологии

    def __str__(self):
        return f"{self.mentor.username} - {self.technology.name}"


class CourseTechnology(models.Model):
    """Технологии, используемые в курсе"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='course_technologies',
        verbose_name="Курс"
    )
    technology = models.ForeignKey(
        Technology,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Технология"
    )

    class Meta:
        verbose_name = "Технология курса"
        verbose_name_plural = "Технологии курсов"
        unique_together = ['course', 'technology']  # Один курс - одна запись по технологии

    def __str__(self):
        return f"{self.course.title} - {self.technology.name}"
