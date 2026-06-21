# Generated manually — system events for conferences in chat

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0004_chat_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="conference",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chat_messages",
                to="communication.conference",
                verbose_name="Конференция",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="system_event",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=32,
                verbose_name="Системное событие",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="system_payload",
            field=models.JSONField(
                blank=True,
                null=True,
                verbose_name="Данные события",
            ),
        ),
    ]
