import os
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(
        self, email=None, phone=None, password=None, **extra_fields
    ):
        # Для обычных пользователей: email ИЛИ phone
        if not email and not phone:
            raise ValueError(_("Email or phone is required"))

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, phone=None, password=None, **extra_fields
    ):
        # Для суперпользователя: email И phone ОБЯЗАТЕЛЬНЫ
        if not email:
            raise ValueError(_("Superuser must have an email"))
        if not phone:
            raise ValueError(_("Superuser must have a phone"))

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


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("student", _("Student")),
        ("mentor", _("Mentor")),
        ("admin", _("Admin")),
    ]

    def upload_to(self, filename):
        user_identifier = self.email or self.phone or "unknown"
        file_name, file_extension = os.path.splitext(filename)
        filename = f"{uuid.uuid4().hex}{file_extension}"
        return f"avatars/{user_identifier}/{filename}"

    def clean(self):
        # Базовая проверка: email ИЛИ phone для всех пользователей
        if not self.email and not self.phone:
            raise ValidationError(_("Email or phone must be specified"))

        if self.role == "admin" or self.is_superuser:
            if not self.email:
                raise ValidationError(
                    {"email": _("Email is required for admin")}
                )
            if not self.phone:
                raise ValidationError(
                    {"phone": _("Phone is required for admin")}
                )

        # Проверка уникальности email
        if self.email:
            qs = User.objects.filter(email=self.email)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"email": _("A user with this email already exists")}
                )

        # Проверка уникальности phone
        if self.phone:
            qs = User.objects.filter(phone=self.phone)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"phone": _("A user with this phone already exists")}
                )

    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=255,
        help_text=_("User's first name"),
    )
    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=255,
        help_text=_("User's last name"),
    )
    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text=_("User phone number"),
    )
    email = models.EmailField(
        verbose_name=_("Email"),
        blank=True,
        null=True,
        unique=True,
        help_text=_("User email"),
    )
    role = models.CharField(
        verbose_name=_("Role"),
        max_length=50,
        choices=ROLE_CHOICES,
        default="student",
        help_text=_("User role in the system"),
    )
    avatar = models.ImageField(
        verbose_name=_("Avatar"),
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text=_("User avatar"),
    )
    bio = models.TextField(
        verbose_name=_("Biography"),
        default="",
        help_text=_("User biography"),
        blank=True,
    )
    date_joined = models.DateTimeField(
        verbose_name=_("Registration date"),
        default=timezone.now,
        help_text=_("User registration date"),
    )
    last_login = models.DateTimeField(
        verbose_name=_("Last login"),
        auto_now=True,
        help_text=_("Last login time"),
    )
    is_active = models.BooleanField(
        verbose_name=_("Active"),
        default=True,
        help_text=_("Is the user active"),
    )
    is_staff = models.BooleanField(
        verbose_name=_("Staff"),
        default=False,
        help_text=_("Is the user a staff member"),
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]

    def __str__(self):
        identifier = self.email or self.phone or "No contact"
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
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("User"),
    )

    class Meta:
        db_table = "students"
        verbose_name = _("Student")
        verbose_name_plural = _("Students")

    def __str__(self):
        return self.user.get_full_name() or str(self.user)



class Specialization(models.Model):
    TYPE_CHOICES = [
        ("web", _("WEB Development")),
        ("mobile", _("Mobile Development")),
        ("data", _("Data Science")),
        ("design", _("UI/UX Design")),
        ("marketing", _("Digital Marketing")),
        ("business", _("Business")),
        ("other", _("Other")),
    ]
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    ]

    type = models.CharField(
        verbose_name=_("Specialization type"),
        max_length=50,
        choices=TYPE_CHOICES,
        default="web",
        help_text=_("Type of specialization")
    )
    title = models.CharField(
        verbose_name=_("Specialization title"),
        max_length=255,
        help_text=_("Title of the specialization")
    )
    title_ru = models.CharField(
        verbose_name=_("Russian specialization title"),
        max_length=255,
        help_text=_("Title of the specialization in russian"),
        null=True,
        blank=True,
    )
    title_en = models.CharField(
        verbose_name=_("English specialization title"),
        max_length=255,
        help_text=_("Title of the specialization in english"),
        null=True,
        blank=True,
    )
    translation_status = models.CharField(
        verbose_name=_("Translation status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text=_("Set status of translation")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        help_text=_("Detailed description of the specialization")
    )
    is_active = models.BooleanField(
        verbose_name=_("Active"),
        default=True,
        help_text=_("Is this specialization active")
    )
    updated_at = models.DateTimeField(
        verbose_name=_("Updated at"),
        auto_now=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = self.title

    def has_title_changed(self):
        return self._title != self.title

    class Meta:
        db_table = "specializations"
        ordering = ["type", "title"]
        verbose_name = _("Specialization")
        verbose_name_plural = _("Specializations")

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"


class Mentor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_profile",
        verbose_name=_("User"),
    )
    specialization = models.ForeignKey(
        to=Specialization,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Specialization"),
        blank=True,
        help_text=_("Primary specialization"),
    )
    experience_years = models.PositiveSmallIntegerField(
        verbose_name=_("Experience (in years)"),
        null=True,
        blank=True,
        help_text=_("How many years experience"),
    )

    class Meta:
        db_table = "mentors"
        verbose_name = _("Mentor")
        verbose_name_plural = _("Mentors")

    def __str__(self):
        return (
            f"{self.user.get_full_name() or str(self.user)} "
            f"({self.specialization or '—'})"
        )
