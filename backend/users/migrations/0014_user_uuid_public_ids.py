import uuid

from django.db import migrations, models


def fill_users_public_ids(apps, schema_editor):
    for label in ("User", "Student", "Specialization", "Mentor"):
        Model = apps.get_model("users", label)
        for obj in Model.objects.filter(public_id__isnull=True):
            obj.public_id = uuid.uuid4()
            obj.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_alter_mentor_options_alter_specialization_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
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
            model_name="student",
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
            model_name="specialization",
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
            model_name="mentor",
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
            fill_users_public_ids, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="user",
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
            model_name="student",
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
            model_name="specialization",
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
            model_name="mentor",
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
