from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0005_chatmessage_conference_system"),
    ]

    operations = [
        migrations.AddField(
            model_name="directthread",
            name="mentor_last_read_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Ментор прочитал до",
            ),
        ),
        migrations.AddField(
            model_name="directthread",
            name="student_last_read_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Студент прочитал до",
            ),
        ),
    ]
