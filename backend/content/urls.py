from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    CodingChallengeViewSet,
    CourseViewSet,
    LessonCheckBoxQuestionViewSet,
    LessonRadioQuestionViewSet,
    LessonTheoryViewSet,
    ModuleViewSet,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"modules", ModuleViewSet, basename="modules")
router.register(
    r"lessons-theory",
    LessonTheoryViewSet,
    basename="lessons-theory",
)
router.register(
    r"lessons-radio",
    LessonRadioQuestionViewSet,
    basename="lessons-radio",
)
router.register(
    r"lessons-checkbox",
    LessonCheckBoxQuestionViewSet,
    basename="lessons-checkbox",
)
router.register(r"challenges", CodingChallengeViewSet, basename="challenges")

app_name = "content"

urlpatterns = [
    path("content/", include(router.urls)),
]
