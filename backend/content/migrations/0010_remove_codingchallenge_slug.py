from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0009_uuid_public_ids"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="codingchallenge",
            name="slug",
        ),
    ]
