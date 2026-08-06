from django.urls import path
from notify.views import (
    VkStatusView,
    VkWebhookView,
    WebPushSubscribeView,
    WebPushVapidView,
)

urlpatterns = [
    path("vk/status/", VkStatusView.as_view(), name="vk-status"),
    path(
        "vk/webhook/<str:secret>/",
        VkWebhookView.as_view(),
        name="vk-webhook",
    ),
    path(
        "push/vapid/",
        WebPushVapidView.as_view(),
        name="push-vapid",
    ),
    path(
        "push/subscribe/",
        WebPushSubscribeView.as_view(),
        name="push-subscribe",
    ),
]
