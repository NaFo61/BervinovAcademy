import os
import uuid

from common.models import UUIDPublicIdMixin
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from content.models import Technology
from translations.mixins import AutoTranslateMixin


class CustomUserManager(BaseUserManager):

    def normalize_email(self, email):
        email = super().normalize_email(email)
        return email.lower()

    def create_user(
        self, email=None, phone=None, password=None, **extra_fields
    ):
        # Для обычных пользователей: email ИЛИ phone
        if not email and not phone:
            raise ValueError(_("Необходимо указать email или телефон"))

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, phone=None, password=None, **extra_fields
    ):
        # Для суперпользователя: email И телефон ОБЯЗАТЕЛЬНЫ
        if not email:
            raise ValueError(_("Суперпользователь должен иметь email"))
        if not phone:
            raise ValueError(_("Суперпользователь должен иметь телефон"))

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            email=email, phone=phone, password=password, **extra_fields
        )

    def get_by_natural_key(self, login):
        user = self.filter(email=login).first()
        if user:
            return user

        user = self.filter(phone=login).first()
        if user:
            return user

        return self.get(email=login)


class User(UUIDPublicIdMixin, AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("student", _("Студент")),
        ("mentor", _("Ментор")),
        ("admin", _("Администратор")),
    ]

    def upload_to(self, filename):
        user_identifier = self.email or self.phone or "unknown"
        file_name, file_extension = os.path.splitext(filename)
        filename = f"{uuid.uuid4().hex}{file_extension}"
        return f"avatars/{user_identifier}/{filename}"

    def clean(self):
        # Базовая проверка: email ИЛИ телефон для всех пользователей
        if not self.email and not self.phone:
            raise ValidationError(_("Необходимо указать email или телефон"))

        if self.role == "admin" or self.is_superuser:
            if not self.email:
                raise ValidationError(
                    {"email": _("Для администратора требуется email")}
                )
            if not self.phone:
                raise ValidationError(
                    {"phone": _("Для администратора требуется телефон")}
                )

        # Проверка уникальности email
        if self.email:
            qs = User.objects.filter(email=self.email)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"email": _("Пользователь с таким email уже существует")}
                )

        # Проверка уникальности телефона
        if self.phone:
            qs = User.objects.filter(phone=self.phone)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {
                        "phone": _(
                            "Пользователь с таким телефоном уже существует"
                        )
                    }
                )

    first_name = models.CharField(
        verbose_name=_("Имя"),
        max_length=255,
        help_text=_("Имя пользователя"),
    )
    last_name = models.CharField(
        verbose_name=_("Фамилия"),
        max_length=255,
        help_text=_("Фамилия пользователя"),
    )
    phone = models.CharField(
        verbose_name=_("Телефон"),
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text=_("Номер телефона пользователя"),
    )
    email = models.EmailField(
        verbose_name=_("Email"),
        blank=True,
        null=True,
        unique=True,
        help_text=_("Email пользователя"),
    )
    role = models.CharField(
        verbose_name=_("Роль"),
        max_length=50,
        choices=ROLE_CHOICES,
        default="student",
        help_text=_("Роль пользователя в системе"),
    )
    avatar = models.ImageField(
        verbose_name=_("Аватар"),
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text=_("Аватар пользователя"),
    )
    bio = models.TextField(
        verbose_name=_("Биография"),
        default="",
        help_text=_("Биография пользователя"),
        blank=True,
    )
    date_joined = models.DateTimeField(
        verbose_name=_("Дата регистрации"),
        default=timezone.now,
        help_text=_("Дата регистрации пользователя"),
    )
    last_login = models.DateTimeField(
        verbose_name=_("Последний вход"),
        auto_now=True,
        help_text=_("Время последнего входа"),
    )
    is_active = models.BooleanField(
        verbose_name=_("Активен"),
        default=True,
        help_text=_("Активен ли пользователь"),
    )
    is_staff = models.BooleanField(
        verbose_name=_("Персонал"),
        default=False,
        help_text=_("Является ли пользователь сотрудником"),
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]

    def __str__(self):
        identifier = self.email or self.phone or "Нет контактов"
        return f"{self.get_full_name()} ({identifier})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def get_username(self):
        return self.email or self.phone

    @property
    def has_email(self):
        return bool(self.email)

    @property
    def has_phone(self):
        return bool(self.phone)

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_mentor(self):
        return self.role == "mentor"

    @property
    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def save(self, *args, **kwargs):
        if self.role == "admin":
            self.is_staff = True
            self.is_superuser = True
        elif self.role == "mentor":
            self.is_staff = True
            self.is_superuser = False
        else:  # student
            self.is_staff = False
            self.is_superuser = False

        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "users"
        ordering = ["-date_joined", "email"]
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")


class Student(UUIDPublicIdMixin, models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("Пользователь"),
    )

    class Meta:
        db_table = "students"
        verbose_name = _("Студент")
        verbose_name_plural = _("Студенты")

    def __str__(self):
        return self.user.get_full_name() or str(self.user)


class Specialization(UUIDPublicIdMixin, AutoTranslateMixin, models.Model):
    TYPE_CHOICES = [
        ("web", _("WEB-разработка")),
        ("mobile", _("Мобильная разработка")),
        ("data", _("Data Science")),
        ("design", _("UI/UX дизайн")),
        ("marketing", _("Цифровой маркетинг")),
        ("business", _("Бизнес")),
        ("other", _("Другое")),
    ]
    STATUS_CHOICES = [
        ("pending", _("В ожидании")),
        ("completed", _("Завершено")),
        ("failed", _("Не удалось")),
    ]

    type = models.CharField(
        verbose_name=_("Тип специализации"),
        max_length=50,
        choices=TYPE_CHOICES,
        default="web",
        help_text=_("Тип специализации"),
    )
    title = models.CharField(
        verbose_name=_("Название специализации"),
        max_length=255,
        help_text=_("Название специализации"),
    )
    description = models.TextField(
        verbose_name=_("Описание"),
        blank=True,
        help_text=_("Подробное описание специализации"),
    )
    is_active = models.BooleanField(
        verbose_name=_("Активна"),
        default=True,
        help_text=_("Активна ли эта специализация"),
    )
    translatable_fields = ["title", "description"]

    class Meta:
        db_table = "specializations"
        ordering = ["type", "title"]
        verbose_name = _("Специализация")
        verbose_name_plural = _("Специализации")

    def __str__(self):
        return self.title


class Mentor(UUIDPublicIdMixin, models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_profile",
        verbose_name=_("Пользователь"),
    )
    specialization = models.ForeignKey(
        to=Specialization,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Специализация"),
        blank=True,
        help_text=_("Основная специализация"),
    )
    experience_years = models.PositiveSmallIntegerField(
        verbose_name=_("Опыт (в годах)"),
        null=True,
        blank=True,
        help_text=_("Количество лет опыта"),
    )
    technology = models.ManyToManyField(
        Technology,
        blank=True,
        verbose_name=_("Технологии"),
        related_name="mentors",
    )

    class Meta:
        db_table = "mentors"
        verbose_name = _("Ментор")
        verbose_name_plural = _("Менторы")

    def __str__(self):
        return (
            f"{self.user.get_full_name() or str(self.user)} "
            f"({self.specialization or '—'})"
        )
