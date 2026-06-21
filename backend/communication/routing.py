from common.drf import UUID_LOOKUP_REGEX
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        rf"^ws/chat/threads/(?P<thread_public_id>{UUID_LOOKUP_REGEX})/$",
        consumers.ChatConsumer.as_asgi(),
    ),
]
