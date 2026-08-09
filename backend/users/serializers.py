from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from education.services import build_enrollments_payload
from progress.profile_serializers import (
    UserProgressStatsSerializer,
    build_achievements_payload,
)
from progress.stats import build_activity_payload

from .models import User


def inject_access_claims(access_token, user):
    """Добавляет публичные claims в access JWT (login / register / refresh)."""
    access_token["email"] = user.email
    access_token["phone"] = user.phone
    access_token["role"] = user.role
    access_token["public_id"] = str(user.public_id)
    access_token["first_name"] = user.first_name
    access_token["last_name"] = user.last_name
    return access_token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    login = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        error_messages={
            "min_length": "Пароль должен содержать минимум 8 символов.",
        },
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "login",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if not login:
            raise serializers.ValidationError(
                "Необходимо указать login (email или телефон) для регистрации."
            )

        if "@" in login:
            if User.objects.filter(email=login).exists():
                raise serializers.ValidationError(
                    {"login": "Пользователь с таким email уже существует."}
                )
            attrs["email"] = login
        else:
            if User.objects.filter(phone=login).exists():
                raise serializers.ValidationError(
                    {"login": "Пользователь с таким телефоном уже существует."}
                )
            attrs["phone"] = login

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Пароли не совпадают."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        validated_data.pop("login")
        password = validated_data.pop("password")
        return User.objects.create_user(
            role="student", password=password, **validated_data
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    login = serializers.CharField()

    def validate_login(self, value):
        login = (value or "").strip()
        if not login:
            raise serializers.ValidationError(
                "Укажите email или номер телефона."
            )
        return login


class PasswordResetConfirmSerializer(serializers.Serializer):
    login = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        error_messages={
            "min_length": "Пароль должен содержать минимум 8 символов.",
        },
    )
    password_confirm = serializers.CharField(write_only=True)

    def validate_login(self, value):
        login = (value or "").strip()
        if not login:
            raise serializers.ValidationError(
                "Укажите email или номер телефона."
            )
        return login

    def validate_code(self, value):
        code = (value or "").strip()
        if not code.isdigit():
            raise serializers.ValidationError("Код должен состоять из цифр.")
        return code

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Пароли не совпадают."}
            )
        return attrs


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Сериализатор для получения JWT токенов по email или телефону"""

    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")

        if not login or not password:
            raise serializers.ValidationError(
                "Необходимо указать login (email или телефон) и пароль."
            )

        user = None
        try:
            user = User.objects.get(email=login)
        except User.DoesNotExist:
            try:
                user = User.objects.get(phone=login)
            except User.DoesNotExist:
                pass

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Неверные учетные данные.")

        if not user.is_active:
            raise serializers.ValidationError("Учетная запись неактивна.")

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        inject_access_claims(access, user)

        return {"refresh": str(refresh), "access": str(access)}


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Refresh с теми же claims, что и при логине (public_id, role, …)."""

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh[api_settings.USER_ID_CLAIM]
        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Пользователь не найден."
            ) from exc
        data = super().validate(attrs)
        access = refresh.access_token
        inject_access_claims(access, user)
        data["access"] = str(access)
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data display"""

    class Meta:
        model = User
        fields = (
            "public_id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "bio",
        )
        read_only_fields = ("public_id", "role")


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "public_id",
            "first_name",
            "last_name",
            "role",
            "avatar",
        )
        read_only_fields = fields


class MentorProfileSerializer(serializers.Serializer):
    specialization = serializers.SerializerMethodField()
    experience_years = serializers.IntegerField(allow_null=True)
    technologies = serializers.SerializerMethodField()

    def get_specialization(self, obj):
        if not obj.specialization:
            return None
        return {
            "public_id": obj.specialization.public_id,
            "type": obj.specialization.type,
            "title": obj.specialization.title,
        }

    def get_technologies(self, obj):
        return [
            {
                "public_id": tech.public_id,
                "title": getattr(tech, "title", str(tech)),
            }
            for tech in obj.technology.all()
        ]


class UserPublicProfileSerializer(serializers.ModelSerializer):
    mentor_profile = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    enrollments = serializers.SerializerMethodField()
    activity = serializers.SerializerMethodField()

    def get_mentor_profile(self, obj):
        mentor = getattr(obj, "mentor_profile", None)
        if not mentor:
            return None
        return MentorProfileSerializer(mentor, context=self.context).data

    def get_progress(self, obj):
        return UserProgressStatsSerializer.from_user(obj).data

    def get_achievements(self, obj):
        return build_achievements_payload(obj)

    def get_enrollments(self, obj):
        return build_enrollments_payload(obj)

    def get_activity(self, obj):
        return build_activity_payload(obj)

    class Meta:
        model = User
        fields: tuple[str, ...] = (
            "public_id",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "bio",
            "date_joined",
            "last_login",
            "mentor_profile",
            "progress",
            "achievements",
            "enrollments",
            "activity",
        )
        read_only_fields: tuple[str, ...] = (
            "public_id",
            "role",
            "date_joined",
            "last_login",
            "mentor_profile",
            "progress",
            "achievements",
            "enrollments",
            "activity",
        )


def build_recovery_payload(user) -> dict:
    has_password = user.has_usable_password()
    has_email = bool(user.email)
    has_phone = bool(user.phone)
    ready = has_password and (has_email or has_phone)
    oauth_linked = bool(user.vk_id or user.yandex_id)
    return {
        "needs_setup": oauth_linked and not ready,
        "has_usable_password": has_password,
        "has_email": has_email,
        "has_phone": has_phone,
        "ready": ready,
    }


class ContactConflict(Exception):
    """Email/phone занят другим аккаунтом."""

    def __init__(self, detail):
        self.detail = detail
        super().__init__(str(detail))


class RecoverySetupSerializer(serializers.Serializer):
    """Задать пароль и/или контакты для восстановления доступа."""

    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    password_confirm = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    current_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True
    )

    def validate_email(self, value):
        return (value or "").strip().lower()

    def validate_phone(self, value):
        return (value or "").strip()

    def validate(self, attrs):
        user = self.context["request"].user
        password = (attrs.get("password") or "").strip()
        password_confirm = (attrs.get("password_confirm") or "").strip()
        email = attrs.get("email") or ""
        phone = attrs.get("phone") or ""
        current_password = attrs.get("current_password") or ""

        # Пустая строка = поле не передали
        if not password:
            attrs.pop("password", None)
            password = ""
        if not password_confirm:
            attrs.pop("password_confirm", None)
            password_confirm = ""
        if not email:
            attrs.pop("email", None)
            email = ""
        if not phone:
            attrs.pop("phone", None)
            phone = ""

        if email:
            field = serializers.EmailField()
            try:
                email = field.run_validation(email)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"email": exc.detail})
            attrs["email"] = email

        if password or password_confirm:
            if not password or not password_confirm:
                raise serializers.ValidationError(
                    {
                        "password_confirm": (
                            "Нужны пароль и подтверждение пароля."
                        )
                    }
                )
            if password != password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": "Пароли не совпадают."}
                )
            try:
                validate_password(password, user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"password": list(exc.messages)}
                ) from exc
            if user.has_usable_password():
                if not current_password or not user.check_password(
                    current_password
                ):
                    raise serializers.ValidationError(
                        {
                            "current_password": (
                                "Укажите текущий пароль для смены."
                            )
                        }
                    )
            attrs["password"] = password

        if email and user.email and email != user.email.lower():
            raise serializers.ValidationError(
                {"email": "Email уже задан и в v1 не меняется."}
            )
        if phone and user.phone and phone != user.phone:
            raise serializers.ValidationError(
                {"phone": "Телефон уже задан и в v1 не меняется."}
            )

        will_have_password = user.has_usable_password() or bool(password)
        will_have_email = bool(user.email) or bool(email)
        will_have_phone = bool(user.phone) or bool(phone)

        if not will_have_password:
            raise serializers.ValidationError(
                {"password": "Нужно задать пароль для восстановления доступа."}
            )
        if not (will_have_email or will_have_phone):
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Укажите email или телефон — хотя бы один контакт."
                    )
                }
            )

        if not password and not email and not phone:
            raise serializers.ValidationError(
                {"detail": "Нечего сохранять: передайте пароль и/или контакт."}
            )

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        password = self.validated_data.get("password")
        email = self.validated_data.get("email")
        phone = self.validated_data.get("phone")
        update_fields: list[str] = []

        if email and not user.email:
            taken = (
                User.objects.filter(email__iexact=email)
                .exclude(pk=user.pk)
                .exists()
            )
            if taken:
                raise ContactConflict(
                    {"email": "Пользователь с таким email уже существует."}
                )
            user.email = email
            update_fields.append("email")

        if phone and not user.phone:
            taken = (
                User.objects.filter(phone=phone).exclude(pk=user.pk).exists()
            )
            if taken:
                raise ContactConflict(
                    {
                        "phone": (
                            "Пользователь с таким телефоном уже существует."
                        )
                    }
                )
            user.phone = phone
            update_fields.append("phone")

        if password:
            user.set_password(password)
            update_fields.append("password")

        if update_fields:
            user.save(update_fields=update_fields)
        return user


class UserPrivateProfileSerializer(UserPublicProfileSerializer):
    email = serializers.EmailField(allow_null=True, read_only=True)
    phone = serializers.CharField(allow_null=True, read_only=True)
    subscription = serializers.SerializerMethodField()
    oauth = serializers.SerializerMethodField()
    vk = serializers.SerializerMethodField()
    recovery = serializers.SerializerMethodField()

    def get_subscription(self, obj):
        from subscriptions.services import subscription_payload

        return subscription_payload(obj)

    def get_oauth(self, obj):
        return {
            "yandex": bool(obj.yandex_id),
            "vk": bool(obj.vk_id),
        }

    def get_vk(self, obj):
        from django.conf import settings
        from notify.vk_api import community_write_url, is_configured

        return {
            "linked": bool(obj.vk_id),
            "messages_allowed": bool(obj.vk_messages_allowed),
            "bot_configured": is_configured(),
            "group_id": (getattr(settings, "VK_GROUP_ID", "") or "").strip(),
            "write_url": community_write_url(),
        }

    def get_recovery(self, obj):
        return build_recovery_payload(obj)

    class Meta(UserPublicProfileSerializer.Meta):
        fields: tuple[str, ...] = UserPublicProfileSerializer.Meta.fields + (
            "email",
            "phone",
            "subscription",
            "oauth",
            "vk",
            "recovery",
        )
        read_only_fields: tuple[str, ...] = (
            "public_id",
            "role",
            "date_joined",
            "last_login",
            "mentor_profile",
            "progress",
            "achievements",
            "email",
            "phone",
            "subscription",
            "oauth",
            "vk",
            "recovery",
        )
