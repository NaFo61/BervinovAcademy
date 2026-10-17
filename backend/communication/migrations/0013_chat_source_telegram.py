from django.db import migrations, models


def vk_source_to_site(apps, schema_editor):
    ChatMessage = apps.get_model("communication", "ChatMessage")
    ChatMessage.objects.filter(source="vk").update(source="site")


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0012_vk_oauth_drop_telegram"),
    ]

    operations = [
        migrations.RunPython(vk_source_to_site, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="chatmessage",
            name="source",
            field=models.CharField(
                choices=[("site", "Сайт"), ("telegram", "Telegram")],
                db_index=True,
                default="site",
                max_length=16,
                verbose_name="Источник",
            ),
        ),
    ]
