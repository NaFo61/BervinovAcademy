# Generated manually — общий order_index уроков в модуле

import django.db.models.deletion
from django.db import migrations, models


def renumber_module_lessons(apps, schema_editor):
    """Пронумеровать уроки в каждом модуле без коллизий между типами."""
    Module = apps.get_model("content", "Module")
    specs = [
        ("LessonTheory", "module_id"),
        ("LessonRadioQuestion", "module_id"),
        ("LessonCheckBoxQuestion", "module_id"),
        ("CodingChallenge", "module_id"),
    ]
    CodingChallenge = apps.get_model("content", "CodingChallenge")
    CodingChallenge.objects.filter(module__isnull=True).delete()

    for module in Module.objects.all():
        items = []
        for model_name, _ in specs:
            Model = apps.get_model("content", model_name)
            for obj in Model.objects.filter(module_id=module.id).order_by(
                "order_index", "pk"
            ):
                items.append((obj.order_index, obj.pk, obj))
        items.sort(key=lambda row: (row[0], row[1]))
        for idx, (_, _, obj) in enumerate(items, start=1):
            if obj.order_index != idx:
                obj.order_index = idx
                obj.save(update_fields=["order_index"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0010_remove_codingchallenge_slug"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="lessontheory",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="lessonradioquestion",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="lessoncheckboxquestion",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="codingchallenge",
            unique_together=set(),
        ),
        migrations.RunPython(renumber_module_lessons, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="codingchallenge",
            name="module",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="challenges",
                to="content.module",
                verbose_name="Модуль",
            ),
        ),
    ]
