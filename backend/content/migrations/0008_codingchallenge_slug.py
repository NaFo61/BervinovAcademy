# Generated manually for restoring slug on CodingChallenge.

from django.db import migrations, models
from django.utils.text import slugify
from unidecode import unidecode


def fill_challenge_slugs(apps, schema_editor):
    CodingChallenge = apps.get_model("content", "CodingChallenge")
    for obj in CodingChallenge.objects.all():
        base = slugify(unidecode(obj.title))[:180] or "challenge"
        candidate = base
        n = 1
        while (
            CodingChallenge.objects.filter(slug=candidate)
            .exclude(pk=obj.pk)
            .exists()
        ):
            candidate = f"{base}-{n}"[:200]
            n += 1
        obj.slug = candidate
        obj.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0007_alter_codingchallenge_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="codingchallenge",
            name="slug",
            field=models.SlugField(
                max_length=200,
                null=True,
                unique=True,
                verbose_name="URL адрес",
            ),
        ),
        migrations.RunPython(fill_challenge_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="codingchallenge",
            name="slug",
            field=models.SlugField(
                max_length=200,
                unique=True,
                verbose_name="URL адрес",
            ),
        ),
    ]
