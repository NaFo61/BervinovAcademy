from django.urls import include, path
from rest_framework.routers import DefaultRouter

from progress.viewsets import (
    UserAnswerCheckBoxViewSet,
    UserAnswerRadioViewSet,
    UserCodeSubmissionViewSet,
)

router = DefaultRouter()
router.register(
    r"radio-answers", UserAnswerRadioViewSet, basename="radio-answers"
)
router.register(
    r"checkbox-answers", UserAnswerCheckBoxViewSet, basename="checkbox-answers"
)
router.register(
    r"code-submissions", UserCodeSubmissionViewSet, basename="code-submissions"
)

app_name = "progress"

urlpatterns = [
    path("progress/", include(router.urls)),
]
