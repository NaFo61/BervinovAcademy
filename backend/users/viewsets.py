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
    """ViewSet for user registration"""

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
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
    """ViewSet for user login"""

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "login"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {**serializer.validated_data}, status=status.HTTP_200_OK
        )


class UserLogoutViewSet(viewsets.GenericViewSet):
    """ViewSet for user logout"""

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
    """Custom token refresh viewset"""

    permission_classes = [AllowAny]
    throttle_scope = "token_refresh"

    def create(self, request, *args, **kwargs):
        """Refresh access token"""
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
    queryset = User.objects.all()

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
