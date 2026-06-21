# Generated manually for course mentor field

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0013_exam_system"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="mentor",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"role__in": ("mentor", "admin")},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mentored_courses",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ментор курса",
            ),
        ),
    ]
