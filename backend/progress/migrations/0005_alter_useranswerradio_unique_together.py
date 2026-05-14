# Generated manually for multiple radio attempts per user/question.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0004_alter_codesubmission_public_id"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="useranswerradio",
            unique_together=set(),
        ),
    ]
