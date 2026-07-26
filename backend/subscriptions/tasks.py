from celery import shared_task

from .reminders import EXPIRY_REMINDER_DAYS, send_expiry_reminders


@shared_task(name="subscriptions.send_pro_expiry_reminders")
def send_pro_expiry_reminders_task():
    return send_expiry_reminders(days=EXPIRY_REMINDER_DAYS)
