import logging

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Слушать Kafka-топик с результатами проверки кода и обновлять CodeSubmission."

    def handle(self, *args, **options):
        if not settings.KAFKA_BOOTSTRAP_SERVERS:
            self.stderr.write(
                self.style.ERROR(
                    "KAFKA_BOOTSTRAP_SERVERS пуст — consumer не запускается."
                )
            )
            raise SystemExit(1)

        self.stdout.write(
            self.style.NOTICE(
                f"Запуск consumer: топик={settings.KAFKA_TOPIC_CODE_RESULTS}, "
                f"группа={settings.KAFKA_GROUP_CODE_RESULTS}, "
                f"брокеры={settings.KAFKA_BOOTSTRAP_SERVERS}. "
                f"Подробные сообщения — в логе Django (уровень "
                f"{logging.getLevelName(settings.DJANGO_LOG_LEVEL)})."
            )
        )
        from progress.kafka_results_consumer import (
            run_results_consumer_forever,
        )

        try:
            run_results_consumer_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("Останов по Ctrl+C."))
