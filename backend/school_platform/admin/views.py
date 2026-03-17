import random

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def dashboard_callback(request, context):
    # Фейковые числовые показатели
    total_users = 1843  # Всего пользователей
    total_courses = 27  # Всего курсов
    active_students = 1560  # Активных студентов
    completed_courses = 820  # Завершенных курсов

    # Фейковые данные для графиков
    months = [
        _("Янв"),
        _("Фев"),
        _("Мар"),
        _("Апр"),
        _("Май"),
        _("Июн"),
        _("Июл"),
        _("Авг"),
        _("Сен"),
        _("Окт"),
        _("Ноя"),
        _("Дек"),
    ]
    activity_data = [random.randint(20, 100) for _ in months]
    course_names = [
        _("Python"),
        _("Django"),
        _("JavaScript"),
        _("React"),
        _("SQL"),
        _("Машинное обучение"),
        _("UI/UX дизайн"),
    ]
    course_counts = [random.randint(30, 150) for _ in course_names]

    # Добавляем в контекст
    context.update(
        {
            "total_users": total_users,
            "total_courses": total_courses,
            "active_students": active_students,
            "completed_courses": completed_courses,
            "months": months,
            "activity_data": activity_data,
            "course_names": course_names,
            "course_counts": course_counts,
        }
    )
    return context
