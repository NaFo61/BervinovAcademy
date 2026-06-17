from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from education.services import build_enrollments_payload
from progress.profile_serializers import (
    UserProgressStatsSerializer,
    build_achievements_payload,
)
from progress.stats import build_activity_payload

from .models import User


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

        # Проверка формата login (email или телефон)
        if "@" in login:
            # Это email
            if User.objects.filter(email=login).exists():
                raise serializers.ValidationError(
                    {"login": "Пользователь с таким email уже существует."}
                )
            attrs["email"] = login
        else:
            # Это телефон
            if User.objects.filter(phone=login).exists():
                raise serializers.ValidationError(
                    {"login": "Пользователь с таким телефоном уже существует."}
                )
            attrs["phone"] = login

        # Проверка совпадения паролей
        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Пароли не совпадают."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        validated_data.pop("login")  # Удаляем login, используем email/phone
        password = validated_data.pop("password")

        # Создание пользователя с ролью student
        user = User.objects.create_user(
            role="student", password=password, **validated_data
        )

        return user


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

        # Поиск пользователя по email или телефону
        user = None
        try:
            user = User.objects.get(email=login)
        except User.DoesNotExist:
            try:
                user = User.objects.get(phone=login)
            except User.DoesNotExist:
                pass

        # Проверка пароля и статуса
        if not user or not user.check_password(password):
            raise serializers.ValidationError("Неверные учетные данные.")

        if not user.is_active:
            raise serializers.ValidationError("Учетная запись неактивна.")

        # Генерация токенов
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Добавление пользовательских claims в access токен
        access["email"] = user.email
        access["phone"] = user.phone
        access["role"] = user.role
        access["public_id"] = str(user.public_id)

        return {"refresh": str(refresh), "access": str(access)}


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


class UserPrivateProfileSerializer(UserPublicProfileSerializer):
    email = serializers.EmailField(allow_null=True, read_only=True)
    phone = serializers.CharField(allow_null=True, read_only=True)

    class Meta(UserPublicProfileSerializer.Meta):
        fields: tuple[str, ...] = UserPublicProfileSerializer.Meta.fields + (
            "email",
            "phone",
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
        )


#         return attrs
