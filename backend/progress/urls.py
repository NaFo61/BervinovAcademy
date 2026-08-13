from django.urls import include, path
from rest_framework.routers import DefaultRouter

from progress.views import (
    CertificateDetailView,
    CertificateListView,
    CourseProgressView,
)
from progress.viewsets import (
    LessonUserCommentViewSet,
    UserAnswerCheckBoxViewSet,
    UserAnswerRadioViewSet,
    UserAnswerShortViewSet,
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
    r"short-answer",
    UserAnswerShortViewSet,
    basename="answers-short-answer",
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
    path(
        "progress/certificates/",
        CertificateListView.as_view(),
        name="certificate-list",
    ),
    path(
        "progress/certificates/<uuid:public_id>/",
        CertificateDetailView.as_view(),
        name="certificate-detail",
    ),
    path("progress/", include(answers_router.urls)),
]
