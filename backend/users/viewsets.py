from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserListSerializer,
    UserPrivateProfileSerializer,
    UserPublicProfileSerializer,
    UserRegistrationSerializer,
)


class UserRegistrationViewSet(viewsets.GenericViewSet):
    """
    ViewSet для регистрации новых пользователей.

    Доступные действия:
    - create — регистрация нового пользователя с выдачей JWT токенов

    Особенности:
    - Доступен без авторизации (AllowAny)
    - Автоматическая генерация access и refresh токенов при регистрации
    - Добавление пользовательских данных в JWT payload
    - Ограничение частоты запросов (throttle_scope="register")
    - Валидация данных через UserRegistrationSerializer

    Процесс регистрации:
    1. Проверка валидности входных данных
    2. Создание нового пользователя
    3. Генерация refresh и access токенов
    4. Добавление кастомных полей в access токен
    5. Возврат токенов клиенту

    Кастомные поля в access токене:
    - email — email пользователя
    - phone — номер телефона
    - role — роль пользователя
    - first_name — имя
    - last_name — фамилия
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        """
        Регистрация нового пользователя.

        После успешной регистрации пользователь сразу получает JWT токены
        и может использовать API без дополнительного логина.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Add custom claims to access token
        access["email"] = user.email
        access["phone"] = user.phone
        access["role"] = user.role
        access["first_name"] = user.first_name
        access["last_name"] = user.last_name

        return Response(
            {"refresh": str(refresh), "access": str(access)},
            status=status.HTTP_201_CREATED,
        )


class UserLoginViewSet(viewsets.GenericViewSet):
    """
    ViewSet для аутентификации пользователя.

    Доступные действия:
    - create — вход в систему с получением JWT токенов

    Особенности:
    - Доступен без авторизации (AllowAny)
    - Использует кастомный сериализатор CustomTokenObtainPairSerializer
    - Ограничение частоты запросов (throttle_scope="login")
    - Поддерживает вход по email/phone и паролю
    - Возвращает refresh и access токены

    Поля для входа:
    - identifier — email или номер телефона
    - password — пароль пользователя

    Возвращаемые данные:
    - refresh — refresh токен (для обновления access токена)
    - access — access токен (для авторизации API запросов)
    - user — данные пользователя (при необходимости)
    """

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "login"

    def create(self, request, *args, **kwargs):
        """
        Аутентификация пользователя.

        Проверяет учетные данные и возвращает пару JWT токенов.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {**serializer.validated_data}, status=status.HTTP_200_OK
        )


class UserLogoutViewSet(viewsets.GenericViewSet):
    """
    ViewSet для выхода пользователя из системы.

    Доступные действия:
    - create — выход из системы (blacklist refresh токена)

    Особенности:
    - Требуется авторизация (IsAuthenticated)
    - Добавляет refresh токен в черный список
    - После выхода access токен продолжает действовать до истечения
    - Для полного выхода нужно удалить access токен на клиенте

    Требования к запросу:
    - refresh — refresh токен (обязательное поле)

    Безопасность:
    - Черный список токенов предотвращает их повторное использование
    - Рекомендуется вызывать этот метод при выходе пользователя
    """

    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Выход пользователя.

        Добавляет refresh токен в черный список,
        делая его недействительным для обновления access токена.
        """
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response(
                {"message": "Выход выполнен успешно"},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"error": "Недействительный refresh токен"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TokenRefreshViewSet(viewsets.GenericViewSet):
    """
    ViewSet для обновления access токена.

    Доступные действия:
    - create — получение нового access токена по refresh токену

    Особенности:
    - Доступен без авторизации (AllowAny)
    - Ограничение частоты запросов (throttle_scope="token_refresh")
    - Refresh токен должен быть действительным (не в черном списке)
    - При ротации токенов возвращается новый refresh токен

    Требования к запросу:
    - refresh — действительный refresh токен (обязательное поле)

    Возвращаемые данные:
    - access — новый access токен
    - refresh — новый refresh токен (если включена ротация)

    Ошибки:
    - 400 Bad Request — недействительный или истекший refresh токен
    """

    permission_classes = [AllowAny]
    throttle_scope = "token_refresh"

    def create(self, request, *args, **kwargs):
        """
        Обновление access токена.

        Принимает refresh токен и возвращает новый access токен.
        """
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken:
            return Response(
                {"error": "Недействительный refresh токен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления профилями пользователей.

    Доступные действия:
    - list — получение списка всех пользователей (публичные данные)
    - retrieve — получение профиля конкретного пользователя
    - me — получение или редактирование своего профиля

    Особенности:
    - Разные уровни доступа для публичных и приватных данных
    - Владелец профиля видит больше полей (приватный профиль)
    - Другие пользователи видят только публичные поля
    - Оптимизация запросов через select_related и prefetch_related

    Поля публичного профиля:
    - id, username, first_name, last_name
    - avatar, role, bio
    - рейтинг, количество решенных задач

    Поля приватного профиля (только для владельца):
    - email, phone, date_joined
    - настройки уведомлений
    - история активности

    Доступ к действиям:
    - list — доступен всем (AllowAny)
    - retrieve — доступен всем (AllowAny)
    - me — только авторизованным (IsAuthenticated)
    - partial_update через me — только авторизованным
    """

    queryset = User.objects.all()

    def get_permissions(self):
        """
        Динамическое назначение прав доступа в зависимости от действия.
        - me и partial_update — только авторизованные пользователи
        - остальные действия — публичный доступ
        """
        if self.action in ("me", "partial_update"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def _is_owner(self, request, user_obj):
        """
        Проверяет, является ли текущий пользователь владельцем профиля.
        Используется для выбора между публичным и приватным сериализатором.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.pk == user_obj.pk
        )

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия:
        - list — компактный сериализатор для списка пользователей
        - me — приватный профиль (все поля)
        - retrieve — публичный или приватный в зависимости от владельца
        """
        if self.action == "list":
            return UserListSerializer
        if self.action == "me":
            return UserPrivateProfileSerializer
        return UserPublicProfileSerializer

    def get_queryset(self):
        """
        Возвращает queryset пользователей с оптимизацией запросов.
        Предварительно загружает связанные данные наставников:
        - специализация наставника
        - технологии наставника
        """
        return (
            User.objects.all()
            .select_related("mentor_profile__specialization")
            .prefetch_related("mentor_profile__technology")
        )

    def list(self, request, *args, **kwargs):
        """
        Получение списка всех пользователей.

        Возвращает только публичные данные о пользователях.
        Поддерживается пагинация (если настроена).
        """
        queryset = self.get_queryset()
        serializer = UserListSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Получение детальной информации о пользователе.

        Автоматически определяет уровень доступа:
        - Если запрашивает владелец — возвращает приватный профиль
        - Если другой пользователь — возвращает публичный профиль
        """
        user_obj = get_object_or_404(self.get_queryset(), pk=kwargs.get("pk"))

        if self._is_owner(request, user_obj):
            serializer = UserPrivateProfileSerializer(
                user_obj,
                context={"request": request},
            )
        else:
            serializer = UserPublicProfileSerializer(
                user_obj,
                context={"request": request},
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request, *args, **kwargs):
        """
        Получение или редактирование своего профиля.

        GET /users/me/ — получение полного приватного профиля
        PATCH /users/me/ — частичное обновление профиля

        Поддерживаемые поля для обновления:
        - first_name — имя
        - last_name — фамилия
        - avatar — аватар
        - bio — информация о себе
        - email — email (требует подтверждения)
        - phone — номер телефона
        - notification_settings — настройки уведомлений

        Обновление происходит частично (partial=True),
        поэтому можно отправлять только изменяемые поля.
        """
        if request.method.lower() == "get":
            serializer = UserPrivateProfileSerializer(
                request.user,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserPrivateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
