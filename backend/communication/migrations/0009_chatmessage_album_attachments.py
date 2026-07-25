# Generated manually for chat albums

import communication.models
import django.db.models.deletion
from django.db import migrations, models


def copy_legacy_attachments(apps, schema_editor):
    ChatMessage = apps.get_model("communication", "ChatMessage")
    ChatMessageAttachment = apps.get_model(
        "communication", "ChatMessageAttachment"
    )
    for msg in ChatMessage.objects.exclude(attachment="").iterator():
        if not msg.attachment:
            continue
        kind = msg.kind if msg.kind in ("image", "video") else "image"
        ChatMessageAttachment.objects.create(
            message_id=msg.pk,
            file=msg.attachment,
            kind=kind,
            sort_order=0,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0008_chatmessage_media_reply_forward"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="kind",
            field=models.CharField(
                choices=[
                    ("text", "Текст"),
                    ("system", "Системное"),
                    ("image", "Изображение"),
                    ("video", "Видео"),
                    ("album", "Альбом"),
                    ("code", "Код"),
                ],
                db_index=True,
                default="text",
                max_length=16,
                verbose_name="Тип",
            ),
        ),
        migrations.CreateModel(
            name="ChatMessageAttachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=communication.models.chat_attachment_upload_to,
                        verbose_name="Файл",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("image", "Изображение"),
                            ("video", "Видео"),
                        ],
                        max_length=16,
                        verbose_name="Тип",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Порядок"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="communication.chatmessage",
                        verbose_name="Сообщение",
                    ),
                ),
            ],
            options={
                "verbose_name": "Вложение чата",
                "verbose_name_plural": "Вложения чата",
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.RunPython(copy_legacy_attachments, migrations.RunPython.noop),
    ]
