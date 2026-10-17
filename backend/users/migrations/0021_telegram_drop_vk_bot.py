from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0020_email_verified"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="vk_messages_allowed",
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_id",
            field=models.BigIntegerField(
                blank=True,
                help_text="Числовой id пользователя в Telegram",
                null=True,
                unique=True,
                verbose_name="Telegram ID",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_chat_id",
            field=models.BigIntegerField(
                blank=True,
                help_text="Куда бот пишет в личный чат",
                null=True,
                verbose_name="Telegram chat id",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_username",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                verbose_name="Telegram username",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_linked_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Telegram привязан",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="vk_id",
            field=models.BigIntegerField(
                blank=True,
                help_text="Идентификатор VK ID (вход)",
                null=True,
                unique=True,
                verbose_name="VK ID",
            ),
        ),
    ]
