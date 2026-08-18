"""Добавляет 6 разборов №1 ЕГЭ в модуль «Графы» без пересборки курса."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from fixture.ege_n1 import (
    COURSE_SLUG,
    GRAPHS_MODULE_TITLE,
    ensure_ege_n1_in_module,
)

from content.models import Course, Module


class Command(BaseCommand):
    help = (
        "Добавляет или обновляет 6 уроков теории по заданию 1 ЕГЭ "
        "в модуле «1-й урок ЕГЭ: Графы». Задания и ответы не трогает."
    )

    def handle(self, *args, **options):
        try:
            course = Course.objects.get(slug=COURSE_SLUG)
        except Course.DoesNotExist as exc:
            raise CommandError(
                "Нет курса «ЕГЭ-информатика». "
                "Сначала создайте курс (ensure_ege_course)."
            ) from exc
        try:
            module = course.modules.get(
                title=GRAPHS_MODULE_TITLE, is_active=True
            )
        except Module.DoesNotExist as exc:
            raise CommandError(
                "Нет активного модуля «1-й урок ЕГЭ: Графы»."
            ) from exc

        with transaction.atomic():
            lessons = ensure_ege_n1_in_module(module)

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {len(lessons)} уроков теории в «{module.title}»."
            )
        )
        for lesson in lessons:
            self.stdout.write(f"  {lesson.order_index}. {lesson.title}")
