from celery import shared_task
from django.conf import settings

from .services import (
    close_conferences_without_mentor,
    expire_stale_conferences,
)


@shared_task(name="communication.expire_stale_conferences")
def expire_stale_conferences_task():
    ttl = getattr(settings, "CONFERENCE_WAITING_TTL_HOURS", 24)
    return expire_stale_conferences(ttl_hours=ttl)


@shared_task(name="communication.close_conferences_without_mentor")
def close_conferences_without_mentor_task():
    minutes = getattr(settings, "CONFERENCE_MENTOR_ABSENCE_MINUTES", 5)
    return close_conferences_without_mentor(absence_minutes=minutes)
