from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0023_lessontheory_blocks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="codingchallenge",
            name="memory_limit_mb",
            field=models.PositiveIntegerField(
                default=256,
                help_text=(
                    "Максимальное использование памяти в мегабайтах "
                    "(не больше 512)"
                ),
                validators=[
                    MinValueValidator(32),
                    MaxValueValidator(512),
                ],
                verbose_name="Лимит памяти (МБ)",
            ),
        ),
        migrations.AlterField(
            model_name="codingchallenge",
            name="time_limit_ms",
            field=models.PositiveIntegerField(
                default=2000,
                help_text=(
                    "Максимальное время выполнения решения в миллисекундах "
                    "(не больше 10000)"
                ),
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(10000),
                ],
                verbose_name="Лимит времени (мс)",
            ),
        ),
    ]
