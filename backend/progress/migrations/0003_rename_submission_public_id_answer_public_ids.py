import uuid

from django.db import migrations, models


def fill_answer_public_ids(apps, schema_editor):
    RA = apps.get_model("progress", "UserAnswerRadio")
    for obj in RA.objects.filter(public_id__isnull=True):
        obj.public_id = uuid.uuid4()
        obj.save(update_fields=["public_id"])

    CB = apps.get_model("progress", "UserAnswerCheckBox")
    for obj in CB.objects.filter(public_id__isnull=True):
        obj.public_id = uuid.uuid4()
        obj.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0002_codesubmission_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="codesubmission",
            old_name="submission_id",
            new_name="public_id",
        ),
        migrations.AddField(
            model_name="useranswerradio",
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
            model_name="useranswercheckbox",
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
            fill_answer_public_ids, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="useranswerradio",
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
            model_name="useranswercheckbox",
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
