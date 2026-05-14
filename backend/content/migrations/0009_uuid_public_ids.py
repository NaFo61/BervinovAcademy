import uuid

from django.db import migrations, models


CONTENT_MODELS = (
    "Technology",
    "Course",
    "Module",
    "LessonTheory",
    "LessonRadioQuestion",
    "RadioAnswerOption",
    "LessonCheckBoxQuestion",
    "CheckBoxAnswerOption",
    "CodingChallenge",
    "TestCase",
)


def fill_content_public_ids(apps, schema_editor):
    for model_name in CONTENT_MODELS:
        Model = apps.get_model("content", model_name)
        for obj in Model.objects.filter(public_id__isnull=True):
            obj.public_id = uuid.uuid4()
            obj.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0008_codingchallenge_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="technology",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="module",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="lessontheory",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="lessonradioquestion",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="radioansweroption",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="lessoncheckboxquestion",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="checkboxansweroption",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="codingchallenge",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                editable=False,
                null=True,
                unique=False,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.RunPython(
            fill_content_public_ids, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="technology",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="module",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="lessontheory",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="lessonradioquestion",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="radioansweroption",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="lessoncheckboxquestion",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="checkboxansweroption",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="codingchallenge",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.AlterField(
            model_name="testcase",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
    ]
