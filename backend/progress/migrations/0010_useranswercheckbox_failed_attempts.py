# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0009_exam_system"),
    ]

    operations = [
        migrations.AddField(
            model_name="useranswercheckbox",
            name="failed_attempts",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name="Число неверных попыток",
            ),
        ),
    ]
