import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from progress.kafka_payloads import build_code_submission_kafka_payload
from progress.kafka_publisher import publish_code_submission_to_kafka
from progress.models import CodeSubmission

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CodeSubmission)
def enqueue_new_code_submission_to_kafka(sender, instance, created, **kwargs):
    """
    После успешного commit новой отправки — сообщение в топик для воркера
    проверки кода.
    """
    if not created:
        return
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return

    try:
        payload = build_code_submission_kafka_payload(instance)
    except Exception:
        logger.exception(
            "Kafka: не удалось собрать тело сообщения для отправки %s",
            instance.public_id,
        )
        return

    transaction.on_commit(
        lambda p=payload: publish_code_submission_to_kafka(p)
    )
    logger.info(
        "Kafka: отправка %s будет опубликована после commit транзакции.",
        instance.public_id,
    )
