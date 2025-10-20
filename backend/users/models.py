from os.path import splitext
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(
        self, email=None, phone=None, password=None, **extra_fields
    ):
        """
        Создает пользователя по email ИЛИ phone
        """
        if not email and not phone:
            raise ValueError("Необходимо указать email или телефон")

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, phone=None, password=None, **extra_fields
    ):
        """
        Создает суперпользователя. Для админа обязателен email
        """
        if not email:
            raise ValueError("Суперпользователь должен иметь email")

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            email=email, phone=phone, password=password, **extra_fields
        )

    def get_by_natural_key(self, login):
        """
        Поиск пользователя по email или phone
        """
        # Пытаемся найти по email
        user = self.filter(email=login).first()
        if user:
            return user

        # Если не нашли по email, ищем по phone
        user = self.filter(phone=login).first()
        if user:
            return user

        # Если не нашли вообще
        return self.get(email=login)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("mentor", "Mentor"),
        ("admin", "Admin"),
    ]

    def upload_to(self, filename):
        user_identifier = self.email or self.phone or "unknown"
        file_name, file_extension = splitext(filename)
        filename = f"{uuid.uuid4().hex}{file_extension}"
        return f"avatars/{user_identifier}/{filename}"

    def clean(self):
        """
        Валидация: должен быть указан email или phone
        Для админа обязательны оба поля
        """
        if not self.email and not self.phone:
            raise ValidationError("Должен быть указан email или телефон")

        # Для админа обязательны и email и phone
        if self.role == "admin" or self.is_superuser:
            if not self.email:
                raise ValidationError(
                    {"email": "Для администратора обязателен email"}
                )
            if not self.phone:
                raise ValidationError(
                    {"phone": "Для администратора обязателен телефон"}
                )

        # Проверяем уникальность
        if self.email:
            qs = User.objects.filter(email=self.email)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"email": "Пользователь с таким email уже существует"}
                )

        if self.phone:
            qs = User.objects.filter(phone=self.phone)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"phone": "Пользователь с таким телефоном уже существует"}
                )

    # Основные поля
    first_name = models.CharField(
        verbose_name="имя",
        max_length=255,
        help_text="Имя пользователя",
    )
    last_name = models.CharField(
        verbose_name="фамилия",
        max_length=255,
        help_text="Фамилия пользователя",
    )
    phone = models.CharField(
        verbose_name="телефон",
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Номер телефона пользователя",
    )
    email = models.EmailField(
        verbose_name="почта",
        blank=True,
        null=True,
        unique=True,
        help_text="Почта пользователя",
    )

    # Поля ролей и статусов
    role = models.CharField(
        verbose_name="роль",
        max_length=50,
        choices=ROLE_CHOICES,
        default="student",
        help_text="Роль пользователя в системе",
    )
    avatar = models.ImageField(
        verbose_name="аватар",
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Аватар пользователя",
    )
    bio = models.TextField(
        verbose_name="биография",
        default="",
        help_text="Биография пользователя",
    )

    # Даты и временные метки
    date_joined = models.DateTimeField(
        verbose_name="дата регистрации",
        default=timezone.now,
        help_text="Дата регистрации пользователя",
    )
    last_login = models.DateTimeField(
        verbose_name="последний вход",
        auto_now=True,
        help_text="Время последнего входа",
    )

    # Флаги статусов
    is_active = models.BooleanField(
        verbose_name="активен",
        default=True,
        help_text="Активен ли пользователь",
    )
    is_staff = models.BooleanField(
        verbose_name="сотрудник",
        default=False,
        help_text="Является ли пользователь сотрудником",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"  # Для createsuperuser команды
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        identifier = self.email or self.phone or "No contact"
        return f"{self.get_full_name()} ({identifier})"

    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Возвращает короткое имя пользователя"""
        return self.first_name

    def get_username(self):
        """
        Возвращает идентификатор для аутентификации (email или phone)
        """
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
        # При создании суперпользователя автоматически ставим роль admin
        if self.is_superuser and self.role != "admin":
            self.role = "admin"

        self.clean()  # Вызываем валидацию
        super().save(*args, **kwargs)

    class Meta:
        db_table = "users"
        ordering = ["-date_joined", "email"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
