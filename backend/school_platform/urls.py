from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import IsAdminUser


def health_check(request):
    """Health check endpoint for Docker."""
    return JsonResponse({"status": "ok"})


def home_view(request):
    """Главная страница проекта."""
    from django.shortcuts import render

    return render(request, "home.html")


_schema_permission = [IsAdminUser] if not settings.DEBUG else []

urlpatterns = [
    path("", home_view, name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("api/", include("users.urls")),
    path("api/", include("content.urls")),
    path("api/", include("progress.urls")),
    path("api/", include("education.urls")),
    path("api/", include("mentoring.urls")),
    path("api/", include("exams.urls")),
    path("api/", include("communication.urls")),
    path("api/", include("subscriptions.urls")),
    path("api/", include("notify.urls")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=_schema_permission),
        name="schema",
    ),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(
            url_name="schema", permission_classes=_schema_permission
        ),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema", permission_classes=_schema_permission
        ),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
