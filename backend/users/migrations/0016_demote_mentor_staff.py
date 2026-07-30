from django.db import migrations


def demote_mentor_staff(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="mentor").update(
        is_staff=False, is_superuser=False
    )


def restore_mentor_staff(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="mentor").update(is_staff=True)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0015_notify_telegram_push_study"),
    ]

    operations = [
        migrations.RunPython(demote_mentor_staff, restore_mentor_staff),
    ]
