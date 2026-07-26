"""API: Telegram link, Web Push, webhook."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from notify.linking import issue_link_token, unlink_telegram
from notify.models import PushSubscription
from notify.telegram_api import is_configured as tg_configured
from notify.webpush_api import is_configured as push_configured
from notify.webpush_api import vapid_public_key
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class TelegramStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                "linked": bool(u.telegram_id),
                "telegram_username": u.telegram_username or "",
                "telegram_linked_at": u.telegram_linked_at,
                "bot_configured": tg_configured(),
            }
        )


class TelegramLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not tg_configured():
            return Response(
                {"detail": "Telegram-бот не настроен на сервере."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        data = issue_link_token(user=request.user)
        return Response(data)


class TelegramUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        unlink_telegram(user=request.user)
        return Response({"ok": True})


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
class TelegramWebhookView(View):
    def post(self, request, secret: str):
        expected = (
            getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or ""
        ).strip()
        if not expected or secret != expected:
            return HttpResponseForbidden("forbidden")
        try:
            update = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"ok": False}, status=400)
        try:
            from notify.bot_handlers import handle_update

            handle_update(update)
        except Exception:
            logger.exception("Telegram webhook handler failed")
        return JsonResponse({"ok": True})
