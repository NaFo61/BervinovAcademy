from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    ConferenceViewSet,
    LiveKitWebhookView,
    MentorUserSearchView,
    UserNotificationViewSet,
)

router = DefaultRouter()
router.register(r"conferences", ConferenceViewSet, basename="conference")
router.register(
    r"notifications", UserNotificationViewSet, basename="notification"
)

app_name = "communication"

urlpatterns = [
    path("communication/users/search/", MentorUserSearchView.as_view()),
    path("communication/livekit/webhook/", LiveKitWebhookView.as_view()),
    path("communication/", include(router.urls)),
]
