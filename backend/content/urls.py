from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import CourseViewSet, LessonTheoryViewSet, ModuleViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"modules", ModuleViewSet, basename="modules")
router.register(
    r"lessons-theory",
    LessonTheoryViewSet,
    basename="lessons-theory",
)

app_name = "content"

urlpatterns = [
    path("content/", include(router.urls)),
]
