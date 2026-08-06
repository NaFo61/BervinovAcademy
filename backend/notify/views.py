"""API: VK status/webhook, Web Push."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from notify.models import PushSubscription
from notify.vk_api import community_write_url
from notify.vk_api import is_configured as vk_configured
from notify.webpush_api import is_configured as push_configured
from notify.webpush_api import vapid_public_key
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class VkStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                "linked": bool(u.vk_id),
                "vk_id": u.vk_id,
                "messages_allowed": bool(u.vk_messages_allowed),
                "bot_configured": vk_configured(),
                "group_id": (
                    getattr(settings, "VK_GROUP_ID", "") or ""
                ).strip(),
                "write_url": community_write_url(),
            }
        )


class WebPushVapidView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "configured": push_configured(),
                "public_key": vapid_public_key(),
            }
        )


class WebPushSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not push_configured():
            return Response(
                {"detail": "Web Push не настроен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        endpoint = (request.data.get("endpoint") or "").strip()
        keys = request.data.get("keys") or {}
        p256dh = (keys.get("p256dh") or "").strip()
        auth = (keys.get("auth") or "").strip()
        if not endpoint or not p256dh or not auth:
            return Response(
                {"detail": "Нужны endpoint и keys.p256dh/auth."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ua = (request.META.get("HTTP_USER_AGENT") or "")[:512]
        sub, _ = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": ua,
            },
        )
        return Response({"ok": True, "public_id": str(sub.public_id)})

    def delete(self, request):
        endpoint = (request.data.get("endpoint") or "").strip()
        if endpoint:
            PushSubscription.objects.filter(
                user=request.user, endpoint=endpoint
            ).delete()
        else:
            PushSubscription.objects.filter(user=request.user).delete()
        return Response({"ok": True})


@method_decorator(csrf_exempt, name="dispatch")
class VkWebhookView(View):
    def post(self, request, secret: str):
        expected = (getattr(settings, "VK_CALLBACK_SECRET", "") or "").strip()
        if not expected or secret != expected:
            return HttpResponseForbidden("forbidden")
        try:
            event = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"ok": False}, status=400)

        etype = (event.get("type") or "").strip()
        body_secret = (event.get("secret") or "").strip()
        # confirmation от VK часто без secret в теле (только group_id);
        # остальные события — требуем совпадение secret.
        if etype != "confirmation":
            if body_secret != expected:
                return HttpResponseForbidden("forbidden")
        elif body_secret and body_secret != expected:
            return HttpResponseForbidden("forbidden")

        try:
            from notify.vk_handlers import handle_callback_event

            confirmation = handle_callback_event(event)
        except Exception:
            logger.exception("VK webhook handler failed")
            return HttpResponse("ok")

        if confirmation is not None:
            return HttpResponse(confirmation, content_type="text/plain")
        return HttpResponse("ok")
