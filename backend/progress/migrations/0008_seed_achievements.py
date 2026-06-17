from django.db import migrations


DEFAULT_ACHIEVEMENTS = [
    {
        "code": "tasks_1",
        "kind": "tasks_solved",
        "threshold": 1,
        "title": "Первый шаг",
        "description": "Решил первую задачу или тест",
        "emoji": "👶",
        "order_index": 10,
    },
    {
        "code": "tasks_10",
        "kind": "tasks_solved",
        "threshold": 10,
        "title": "Десятка",
        "description": "10 решённых задач и тестов",
        "emoji": "🔟",
        "order_index": 20,
    },
    {
        "code": "tasks_100",
        "kind": "tasks_solved",
        "threshold": 100,
        "title": "Сотня",
        "description": "100 решённых задач и тестов",
        "emoji": "💯",
        "order_index": 30,
    },
    {
        "code": "theories_10",
        "kind": "theories_read",
        "threshold": 10,
        "title": "Книжный червь",
        "description": "10 прочитанных теорий",
        "emoji": "📚",
        "order_index": 40,
    },
    {
        "code": "quizzes_10",
        "kind": "quizzes_solved",
        "threshold": 10,
        "title": "Эрудит",
        "description": "10 пройденных тестов",
        "emoji": "🧠",
        "order_index": 50,
    },
    {
        "code": "courses_1",
        "kind": "courses_completed",
        "threshold": 1,
        "title": "Выпускник",
        "description": "Полностью пройден 1 курс",
        "emoji": "🎓",
        "order_index": 60,
    },
    {
        "code": "courses_5",
        "kind": "courses_completed",
        "threshold": 5,
        "title": "Марафонец",
        "description": "5 полностью пройденных курсов",
        "emoji": "🏃",
        "order_index": 70,
    },
    {
        "code": "streak_7",
        "kind": "streak_days",
        "threshold": 7,
        "title": "Серия 7 дней",
        "description": "7 дней активности подряд",
        "emoji": "🔥",
        "order_index": 80,
    },
    {
        "code": "streak_30",
        "kind": "streak_days",
        "threshold": 30,
        "title": "Серия 30 дней",
        "description": "30 дней активности подряд",
        "emoji": "⚡",
        "order_index": 90,
    },
]


def seed_achievements(apps, schema_editor):
    Achievement = apps.get_model("progress", "Achievement")
    for row in DEFAULT_ACHIEVEMENTS:
        Achievement.objects.update_or_create(
            code=row["code"],
            defaults=row,
        )


def unseed_achievements(apps, schema_editor):
    Achievement = apps.get_model("progress", "Achievement")
    Achievement.objects.filter(
        code__in=[row["code"] for row in DEFAULT_ACHIEVEMENTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0007_achievement_models"),
    ]

    operations = [
        migrations.RunPython(seed_achievements, unseed_achievements),
    ]
