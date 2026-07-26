"""Celery: outbound Telegram + Web Push; study reminders."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


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
    from notify.telegram_api import send_message
    from notify.webpush_api import send_web_push

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {"ok": False, "reason": "no_user"}

    text = title if not body else f"{title}\n\n{body}"
    if url:
        text = f"{text}\n\n{url}"

    tg_ok = False
    if user.telegram_id:
        markup = None
        if url:
            markup = {"inline_keyboard": [[{"text": "Открыть", "url": url}]]}
        tg_ok = send_message(user.telegram_id, text, reply_markup=markup)

    push_ok = 0
    for sub in PushSubscription.objects.filter(user=user):
        if send_web_push(subscription=sub, title=title, body=body, url=url):
            push_ok += 1

    return {"ok": True, "telegram": tg_ok, "web_push": push_ok, "kind": kind}


@shared_task(name="notify.send_study_reminders")
def send_study_reminders() -> dict:
    from notify.study_reminders import send_abandoned_and_streak_reminders

    return send_abandoned_and_streak_reminders()
