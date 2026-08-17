from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .chat_viewsets import ChatMessageViewSet, ChatThreadViewSet
from .viewsets import (
    AdminCallStatsView,
    ConferenceViewSet,
    LiveKitWebhookView,
    MentorUserSearchView,
    UserNotificationViewSet,
    WhiteboardStudioTokenView,
)

router = DefaultRouter()
router.register(r"conferences", ConferenceViewSet, basename="conference")
router.register(r"chat/threads", ChatThreadViewSet, basename="chat-thread")
router.register(r"chat/messages", ChatMessageViewSet, basename="chat-message")
router.register(
    r"notifications", UserNotificationViewSet, basename="notification"
)

app_name = "communication"

urlpatterns = [
    path("communication/users/search/", MentorUserSearchView.as_view()),
    path(
        "communication/admin/call-stats/",
        AdminCallStatsView.as_view(),
    ),
    path("communication/livekit/webhook/", LiveKitWebhookView.as_view()),
    path(
        "communication/whiteboard/studio/token/",
        WhiteboardStudioTokenView.as_view(),
    ),
    path("communication/", include(router.urls)),
]
