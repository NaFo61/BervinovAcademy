from django.urls import include, path
from rest_framework.routers import DefaultRouter

from progress.viewsets import (
    UserAnswerCheckBoxViewSet,
    UserAnswerRadioViewSet,
    UserCodeSubmissionViewSet,
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

app_name = "progress"

urlpatterns = [
    path("progress/", include(answers_router.urls)),
]
