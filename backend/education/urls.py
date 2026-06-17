from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import EnrollmentViewSet

router = DefaultRouter()
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")

app_name = "education"

urlpatterns = [
    path("education/", include(router.urls)),
]
