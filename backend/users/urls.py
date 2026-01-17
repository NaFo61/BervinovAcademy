from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
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

router = DefaultRouter()
router.register(r"users", UserProfileViewSet, basename="users")

app_name = "users"

urlpatterns = [
    path("auth/", include(auth_router.urls)),
    path("", include(router.urls)),
]
