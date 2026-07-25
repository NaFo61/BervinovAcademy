from common.drf import UUID_LOOKUP_REGEX
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .password_reset import confirm_reset_code, issue_reset_code
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserListSerializer,
    UserPrivateProfileSerializer,
    UserPublicProfileSerializer,
    UserRegistrationSerializer,
    inject_access_claims,
)


def _issue_token_pair(user):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    inject_access_claims(access, user)
    return {"refresh": str(refresh), "access": str(access)}


class UserRegistrationViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            _issue_token_pair(user),
            status=status.HTTP_201_CREATED,
        )


class UserLoginViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "login"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {**serializer.validated_data}, status=status.HTTP_200_OK
        )


class PasswordResetViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    @action(detail=False, methods=["post"], url_path="request")
    def request_code(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login = serializer.validated_data["login"]
        _, dev_code = issue_reset_code(login)
        payload = {
            "message": (
                "Если аккаунт найден, мы отправили код восстановления."
            ),
        }
        if dev_code:
            payload["dev_code"] = dev_code
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ok, error = confirm_reset_code(
            login=serializer.validated_data["login"],
            code=serializer.validated_data["code"],
            password=serializer.validated_data["password"],
        )
        if not ok:
            return Response(
                {"detail": error}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"message": "Пароль успешно изменён. Теперь можно войти."},
            status=status.HTTP_200_OK,
        )


class UserLogoutViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
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
    permission_classes = [AllowAny]
    throttle_scope = "token_refresh"

    def create(self, request, *args, **kwargs):
        serializer = CustomTokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return Response(
                {"error": "Недействительный refresh токен"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    lookup_field = "public_id"
    lookup_value_regex = UUID_LOOKUP_REGEX

    def get_permissions(self):
        if self.action in ("me", "partial_update"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def _is_owner(self, request, user_obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.pk == user_obj.pk
        )

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        if self.action == "me":
            return UserPrivateProfileSerializer
        return UserPublicProfileSerializer

    def get_queryset(self):
        return (
            User.objects.all()
            .select_related("mentor_profile__specialization")
            .prefetch_related("mentor_profile__technology")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserListSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        user_obj = self.get_object()
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
