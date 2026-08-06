from common.drf import UUID_LOOKUP_REGEX
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotFound,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .oauth import (
    PROVIDERS,
    OAuthConflict,
    build_authorize_url,
    exchange_code,
    link_provider_to_user,
    provider_configured,
    resolve_or_create_user,
    unlink_provider,
)
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


class OAuthViewSet(viewsets.ViewSet):
    """Яндекс / VK OAuth: start, login, link, unlink."""

    throttle_scope = "login"

    def get_permissions(self):
        if getattr(self, "action", None) in ("link", "unlink"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def _provider(self, provider: str) -> str:
        provider = (provider or "").strip().lower()
        if provider not in PROVIDERS:
            raise ValidationError({"provider": "Неизвестный провайдер."})
        return provider

    def start(self, request, provider=None):
        provider = self._provider(provider)
        if not provider_configured(provider):
            return Response(
                {"detail": f"OAuth {provider} не настроен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        redirect_uri = (request.query_params.get("redirect_uri") or "").strip()
        try:
            data = build_authorize_url(
                provider=provider,
                redirect_uri=redirect_uri or None,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def exchange(self, request, provider=None):
        """POST /api/auth/oauth/{provider}/ — обмен code → JWT."""
        provider = self._provider(provider)
        code = request.data.get("code")
        redirect_uri = (request.data.get("redirect_uri") or "").strip() or None
        try:
            profile = exchange_code(
                provider=provider,
                code=code,
                redirect_uri=redirect_uri,
            )
            user, _created = resolve_or_create_user(profile)
        except OAuthConflict as exc:
            return Response(
                {"detail": exc.message},
                status=status.HTTP_409_CONFLICT,
            )
        except AuthenticationFailed as exc:
            return Response(
                {"detail": str(exc.detail if hasattr(exc, "detail") else exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response(
                {"detail": "Учетная запись неактивна."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(_issue_token_pair(user), status=status.HTTP_200_OK)

    def link(self, request, provider=None):
        provider = self._provider(provider)
        code = request.data.get("code")
        redirect_uri = (request.data.get("redirect_uri") or "").strip() or None
        try:
            profile = exchange_code(
                provider=provider,
                code=code,
                redirect_uri=redirect_uri,
            )
            link_provider_to_user(request.user, profile)
        except OAuthConflict as exc:
            return Response(
                {"detail": exc.message},
                status=status.HTTP_409_CONFLICT,
            )
        except AuthenticationFailed as exc:
            return Response(
                {"detail": str(exc.detail if hasattr(exc, "detail") else exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "provider": provider})

    def unlink(self, request, provider=None):
        provider = self._provider(provider)
        try:
            unlink_provider(request.user, provider)
        except NotFound as exc:
            return Response(
                {"detail": str(exc.detail)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "provider": provider})


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
