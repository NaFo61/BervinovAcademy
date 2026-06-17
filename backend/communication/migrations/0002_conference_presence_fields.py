from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conference",
            name="guest_in_room",
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name="conference",
            name="guest_joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conference",
            name="last_guest_left_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conference",
            name="last_mentor_left_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conference",
            name="mentor_in_room",
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name="conference",
            name="mentor_joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="conference",
            index=models.Index(
                fields=["mentor_in_room", "last_mentor_left_at"],
                name="communicati_mentor__0bc8c3_idx",
            ),
        ),
    ]
