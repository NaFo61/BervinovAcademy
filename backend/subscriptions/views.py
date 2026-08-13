"""Публичное описание тарифа Про."""

from __future__ import annotations

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    PromoRedeemError,
    ensure_pro_plan,
    redeem_promo,
    subscription_payload,
)

FEATURE_COPY = {
    "mentor_chat": {
        "title": "Чат с ментором",
        "blurb": "Пишите ментору курса, задавайте вопросы по заданиям.",
    },
    "solution_video": {
        "title": "Видео-разборы",
        "blurb": "Эталонный текст доступен всем; видео с объяснением — в Про.",
    },
    "conference": {
        "title": "Созвоны",
        "blurb": "Видеозвонки с ментором прямо на платформе.",
    },
}


class ProPlanView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plan = ensure_pro_plan()
        features = []
        for code in plan.features or []:
            meta = FEATURE_COPY.get(code, {"title": code, "blurb": ""})
            features.append(
                {
                    "code": code,
                    "title": meta["title"],
                    "blurb": meta["blurb"],
                }
            )
        payload = {
            "code": plan.code,
            "title": plan.title,
            "description": plan.description,
            "duration_days": plan.duration_days,
            "features": features,
            "purchase_available": False,
            "cta_text": (
                "Оплата картой скоро. Если есть промокод — введите его ниже."
            ),
        }
        user = request.user
        if user and user.is_authenticated:
            payload["subscription"] = subscription_payload(user)
        else:
            payload["subscription"] = None
        return Response(payload)


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(subscription_payload(request.user))


class RedeemPromoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = ""
        if isinstance(request.data, dict):
            raw = request.data.get("code") or ""
        try:
            _entitlement, promo = redeem_promo(user=request.user, code=raw)
        except PromoRedeemError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(
            {
                "ok": True,
                "duration_days": promo.duration_days,
                "subscription": subscription_payload(request.user),
            }
        )
