# Generated manually for chat media / reply / forward

from django.db import migrations, models
import communication.models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0007_alter_chatmessage_public_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="body",
            field=models.TextField(
                blank=True, default="", verbose_name="Текст"
            ),
        ),
        migrations.AlterField(
            model_name="chatmessage",
            name="kind",
            field=models.CharField(
                choices=[
                    ("text", "Текст"),
                    ("system", "Системное"),
                    ("image", "Изображение"),
                    ("video", "Видео"),
                    ("code", "Код"),
                ],
                db_index=True,
                default="text",
                max_length=16,
                verbose_name="Тип",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=communication.models.chat_attachment_upload_to,
                verbose_name="Вложение",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="code_language",
            field=models.CharField(
                blank=True,
                default="",
                max_length=32,
                verbose_name="Язык кода",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="reply_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="replies",
                to="communication.chatmessage",
                verbose_name="Ответ на",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="forwarded_from",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="forwards",
                to="communication.chatmessage",
                verbose_name="Переслано из",
            ),
        ),
    ]
