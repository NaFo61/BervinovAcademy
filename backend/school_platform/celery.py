import os

from celery import Celery

# Указываем Django настройки для Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_platform.settings")

app = Celery("school_platform")

# Подхватывает все настройки CELERY_ из settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находит таски во всех приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
