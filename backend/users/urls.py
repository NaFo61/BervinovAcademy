from django.urls import include, path
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.routers import DefaultRouter

from users.viewsets import (
    OAuthViewSet,
    PasswordResetViewSet,
    RecoverySetupViewSet,
    TokenRefreshViewSet,
    UserLoginViewSet,
    UserLogoutViewSet,
    UserProfileViewSet,
    UserRegistrationViewSet,
)

auth_router = DefaultRouter()
auth_router.register(r"register", UserRegistrationViewSet, basename="register")
auth_router.register(r"login", UserLoginViewSet, basename="login")
auth_router.register(r"logout", UserLogoutViewSet, basename="logout")
auth_router.register(r"refresh", TokenRefreshViewSet, basename="refresh")
auth_router.register(
    r"password-reset", PasswordResetViewSet, basename="password-reset"
)

oauth_start = OAuthViewSet.as_view(
    {"get": "start"},
    permission_classes=[AllowAny],
)
oauth_exchange = OAuthViewSet.as_view(
    {"post": "exchange"},
    permission_classes=[AllowAny],
)
oauth_link = OAuthViewSet.as_view(
    {"post": "link"},
    permission_classes=[IsAuthenticated],
)
oauth_unlink = OAuthViewSet.as_view(
    {"post": "unlink"},
    permission_classes=[IsAuthenticated],
)
recovery_setup = RecoverySetupViewSet.as_view(
    {"post": "create"},
    permission_classes=[IsAuthenticated],
)

router = DefaultRouter()
router.register(r"users", UserProfileViewSet, basename="users")

app_name = "users"

urlpatterns = [
    path(
        "auth/oauth/<str:provider>/start/",
        oauth_start,
        name="oauth-start",
    ),
    path(
        "auth/oauth/<str:provider>/link/",
        oauth_link,
        name="oauth-link",
    ),
    path(
        "auth/oauth/<str:provider>/unlink/",
        oauth_unlink,
        name="oauth-unlink",
    ),
    path(
        "auth/oauth/<str:provider>/",
        oauth_exchange,
        name="oauth-exchange",
    ),
    path(
        "auth/recovery/setup/",
        recovery_setup,
        name="recovery-setup",
    ),
    path("auth/", include(auth_router.urls)),
    path("", include(router.urls)),
]
