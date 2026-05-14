"""
Чтение результатов проверки из Kafka и обновление ``CodeSubmission``.

Формат сообщения — как у воркера ``services/code_check_emulator`` (JSON с полями
``submission_public_id``, ``status``, ``message``, ``passed_tests``, ``total_tests``,
опционально ``failed_test_number``, ``actual_output``, ``expected_output``).
"""

from __future__ import annotations

import json
import logging
from typing import Any
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)

_MAX_FEEDBACK_STORE = 8000


def _feedback_rows_from_kafka(payload: dict[str, Any]) -> dict[str, Any]:
    """Сохраняем в ``CodeSubmission.test_results`` только пользовательский фидбек."""
    out: dict[str, Any] = {}
    n = payload.get("failed_test_number")
    if isinstance(n, int) and n >= 1:
        out["failed_test_number"] = n
    for key in ("actual_output", "expected_output"):
        if key not in payload:
            continue
        val = payload[key]
        if val is None:
            out[key] = None
            continue
        if not isinstance(val, str):
            val = str(val)
        if len(val) > _MAX_FEEDBACK_STORE:
            val = val[: _MAX_FEEDBACK_STORE - 3] + "..."
        out[key] = val
    return out


def apply_code_submission_result_payload(
    payload: dict[str, Any],
) -> tuple[bool, str]:
    """
    Обновить отправку по сообщению из топика результатов.

    Вердикт ``accepted`` из воркера отображается в модели как ``completed``
    (успешное завершение проверки).

    Returns:
        (успех, причина пропуска или ошибки на русском — для логов и отладки)
    """
    from progress.models import CodeSubmission

    raw_id = payload.get("submission_public_id")
    if not raw_id:
        return False, "нет поля submission_public_id"
    try:
        uid = uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        return False, f"некорректный submission_public_id: {raw_id!r}"

    try:
        sub = CodeSubmission.objects.get(public_id=uid)
    except CodeSubmission.DoesNotExist:
        return False, f"отправка не найдена: {uid}"

    if sub.status == CodeSubmission.STATUS_COMPLETED:
        return True, "уже завершена"

    verdict = (payload.get("status") or "").strip().lower()
    if verdict == "accepted":
        django_status = CodeSubmission.STATUS_COMPLETED
    else:
        django_status = "error"

    message = (payload.get("message") or "").strip()
    passed = payload.get("passed_tests")
    total = payload.get("total_tests")
    if not isinstance(passed, int) or passed < 0:
        passed = 0
    if not isinstance(total, int) or total < 0:
        total = 0

    sub.status = django_status
    sub.tests_passed = passed
    sub.total_tests = total
    if django_status == "error":
        sub.error_message = message or verdict or "error"
        sub.test_results = _feedback_rows_from_kafka(payload)
    else:
        sub.error_message = ""
        sub.test_results = {}
    sub.save()
    logger.info(
        "Отправка кода %s: из Kafka verdict=%r → статус Django=%s, "
        "тесты %s/%s, сообщение=%r",
        uid,
        verdict,
        django_status,
        passed,
        total,
        (message or "")[:500],
    )
    return True, ""


def run_results_consumer_forever() -> None:
    """Блокирующий цикл ``KafkaConsumer`` (для management-команды / отдельного процесса)."""
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        raise RuntimeError(
            "KAFKA_BOOTSTRAP_SERVERS пуст — consumer результатов не запускается."
        )

    from kafka import KafkaConsumer

    hosts = [
        h.strip()
        for h in settings.KAFKA_BOOTSTRAP_SERVERS.split(",")
        if h.strip()
    ]
    topic = settings.KAFKA_TOPIC_CODE_RESULTS
    group = settings.KAFKA_GROUP_CODE_RESULTS
    offset_reset = settings.KAFKA_RESULTS_AUTO_OFFSET_RESET

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=hosts,
        group_id=group,
        enable_auto_commit=True,
        auto_offset_reset=offset_reset,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        consumer_timeout_ms=1000,
    )
    logger.info(
        "Запущен consumer результатов Kafka: топик=%s, группа=%s",
        topic,
        group,
    )
    try:
        while True:
            batch = consumer.poll(timeout_ms=1000)
            if not batch:
                continue
            for _tp, records in batch.items():
                for record in records:
                    value = record.value
                    if not isinstance(value, dict):
                        logger.warning(
                            "Результаты Kafka: ожидался dict, получен %s",
                            type(value),
                        )
                        continue
                    ok, reason = apply_code_submission_result_payload(value)
                    if not ok:
                        logger.warning(
                            "Результаты Kafka: сообщение пропущено (%s), "
                            "тело=%s",
                            reason,
                            value,
                        )
    finally:
        consumer.close()
        logger.info("Consumer результатов Kafka остановлен.")
