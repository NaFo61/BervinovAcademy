from django.db import migrations


def seed_pro_plan(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    Plan.objects.update_or_create(
        code="pro",
        defaults={
            "title": "Про",
            "description": (
                "Чат с ментором, видео-разборы эталонных решений и созвоны."
            ),
            "duration_days": 30,
            "is_active": True,
            "features": [
                "mentor_chat",
                "solution_video",
                "conference",
            ],
        },
    )


def unseed_pro_plan(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    Plan.objects.filter(code="pro").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_plan_entitlement"),
    ]

    operations = [
        migrations.RunPython(seed_pro_plan, unseed_pro_plan),
    ]
