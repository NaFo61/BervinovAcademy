from django.urls import path

from notify.views import (
    TelegramLinkView,
    TelegramStatusView,
    TelegramWebhookView,
    WebPushSubscribeView,
    WebPushVapidView,
)

urlpatterns = [
    path(
        "telegram/status/",
        TelegramStatusView.as_view(),
        name="telegram-status",
    ),
    path(
        "telegram/link/",
        TelegramLinkView.as_view(),
        name="telegram-link",
    ),
    path(
        "telegram/webhook/<str:secret>/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
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
