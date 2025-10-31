import time

from celery import shared_task
from django.shortcuts import get_object_or_404

from users.models import Specialization


def translate_specialization_title(specialization_id):
    specialization = get_object_or_404(Specialization, id=specialization_id)
    title = specialization.title
    first_letter_ord = ord(title[0])
    if 1040 <= first_letter_ord <= 1071 or first_letter_ord == 203:
        title_en = f"en{title}"
        specialization.title_ru = title
        specialization.title_en = title_en
    else:
        title_ru = f"ru{title}"
        specialization.title_en = title
        specialization.title_ru = title_ru
    specialization.save()


@shared_task
def test_task():
    print("⏳ Запуск тестовой задачи...")
    time.sleep(3)
    print("✅ Задача выполнена!")
    return "done"
