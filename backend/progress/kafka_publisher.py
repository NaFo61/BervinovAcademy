"""
Публикация отправок кода в Kafka (kafka-python).

При пустом ``KAFKA_BOOTSTRAP_SERVERS`` в настройках — не вызывается брокер.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

_producer: Any = None


def _producer_kwargs() -> dict[str, Any]:
    hosts = [
        h.strip()
        for h in settings.KAFKA_BOOTSTRAP_SERVERS.split(",")
        if h.strip()
    ]
    return {
        "bootstrap_servers": hosts,
        "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
        "linger_ms": 50,
    }


def get_kafka_producer():
    """Ленивый singleton producer (потокобезопасен в kafka-python)."""
    global _producer
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return None
    if _producer is None:
        from kafka import KafkaProducer

        _producer = KafkaProducer(**_producer_kwargs())
    return _producer


def publish_code_submission_to_kafka(payload: dict) -> None:
    """
    Отправить JSON в топик. Сбои брокера только в лог — HTTP не падает.
    """
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return
    producer = get_kafka_producer()
    if producer is None:
        return
    topic = settings.KAFKA_TOPIC_CODE_SUBMISSIONS
    try:
        future = producer.send(topic, value=payload)
        future.get(timeout=10)
    except Exception:
        logger.exception(
            "Не удалось опубликовать отправку в Kafka (submission_public_id=%s, "
            "топик=%s).",
            payload.get("submission_public_id"),
            topic,
        )
    else:
        logger.info(
            "Сообщение об отправке кода отправлено в Kafka: "
            "submission_public_id=%s, топик=%s.",
            payload.get("submission_public_id"),
            topic,
        )


def reset_kafka_producer() -> None:
    """Закрыть producer (тесты / смена настроек)."""
    global _producer
    if _producer is not None:
        try:
            _producer.close()
        except Exception:
            logger.debug(
                "Не удалось корректно закрыть Kafka producer.",
                exc_info=True,
            )
        _producer = None
