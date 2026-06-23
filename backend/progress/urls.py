from django.urls import include, path
from rest_framework.routers import DefaultRouter

from progress.views import CourseProgressView
from progress.viewsets import (
    LessonUserCommentViewSet,
    UserAnswerCheckBoxViewSet,
    UserAnswerRadioViewSet,
    UserCodeSubmissionViewSet,
    UserLessonTheoryReadViewSet,
)

answers_router = DefaultRouter()
answers_router.register(
    r"radio", UserAnswerRadioViewSet, basename="answers-radio"
)
answers_router.register(
    r"checkbox",
    UserAnswerCheckBoxViewSet,
    basename="answers-checkbox",
)
answers_router.register(
    r"code", UserCodeSubmissionViewSet, basename="answers-code"
)
answers_router.register(
    r"theory", UserLessonTheoryReadViewSet, basename="reads-theory"
)
answers_router.register(
    r"lesson-comments",
    LessonUserCommentViewSet,
    basename="lesson-comments",
)

app_name = "progress"

urlpatterns = [
    path(
        "progress/course/",
        CourseProgressView.as_view(),
        name="course-progress",
    ),
    path("progress/", include(answers_router.urls)),
]
