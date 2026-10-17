"""Celery: Web Push и напоминания об учёбе."""

from __future__ import annotations

from celery import shared_task


@shared_task(name="notify.deliver_outbound")
def deliver_outbound(
    user_id: int,
    title: str,
    body: str = "",
    url: str = "",
    kind: str = "",
) -> dict:
    from django.contrib.auth import get_user_model

    from notify.models import PushSubscription
    from notify.webpush_api import send_web_push

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {"ok": False, "reason": "no_user"}

    push_ok = 0
    for sub in PushSubscription.objects.filter(user=user):
        if send_web_push(subscription=sub, title=title, body=body, url=url):
            push_ok += 1

    return {"ok": True, "web_push": push_ok, "kind": kind}


@shared_task(name="notify.send_study_reminders")
def send_study_reminders() -> dict:
    from notify.study_reminders import send_abandoned_and_streak_reminders

    return send_abandoned_and_streak_reminders()
