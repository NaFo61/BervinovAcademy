import random

from django.contrib.auth import get_user_model

User = get_user_model()


def dashboard_callback(request, context):
    # Фейковые числовые показатели
    total_users = 1843
    total_courses = 27
    active_students = 1560
    completed_courses = 820

    # Фейковые данные для графиков
    months = [
        "Янв",
        "Фев",
        "Мар",
        "Апр",
        "Май",
        "Июн",
        "Июл",
        "Авг",
        "Сен",
        "Окт",
        "Ноя",
        "Дек",
    ]
    activity_data = [random.randint(20, 100) for _ in months]
    course_names = [
        "Python",
        "Django",
        "JavaScript",
        "React",
        "SQL",
        "ML",
        "UI/UX",
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
