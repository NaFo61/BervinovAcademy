# backend/school_platform/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_platform.settings")

app = Celery("school_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
