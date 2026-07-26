"""FastAPI: health + Kafka consumer → один Docker-run на отправку → результат."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI

from app.config import Settings, load_settings
from app.docker_execution import (
    build_kafka_payload_from_sandbox,
    run_submission_check,
)

logger = logging.getLogger(__name__)


def _bootstrap_list(servers: str) -> list[str]:
    return [h.strip() for h in servers.split(",") if h.strip()]


async def _handle_message(
    raw: bytes | None,
    producer: AIOKafkaProducer,
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> None:
    if raw is None:
        return
    try:
        incoming = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.exception("Некорректный JSON в сообщении Kafka, пропуск")
        return
    if not isinstance(incoming, dict):
        logger.warning("Ожидался объект JSON, получено: %s", type(incoming))
        return

    user_id = incoming.get("user_public_id", "?")
    challenge_id = incoming.get("challenge_public_id", "?")
    sub_id = incoming.get("submission_public_id", "?")
    logger.info(
        "Проверка кода: submission=%s, пользователь=%s, задача=%s",
        sub_id,
        user_id,
        challenge_id,
    )

    async with semaphore:
        try:
            payload = await asyncio.to_thread(
                run_submission_check, incoming, settings
            )
        except Exception:
            logger.exception(
                "Ошибка проверки submission=%s",
                sub_id,
            )
            raw_cases = incoming.get("test_cases") or []
            total = (
                len(raw_cases) if isinstance(raw_cases, list) else 0
            )
            sid = str(incoming.get("submission_public_id") or "")
            payload = build_kafka_payload_from_sandbox(
                sid,
                {
                    "status": "error",
                    "passed_tests": 0,
                    "total_tests": total,
                    "message": (
                        "Исключение воркера при проверке "
                        "(см. логи code-check-runner)."
                    ),
                },
            )
    try:
        await producer.send_and_wait(settings.kafka_topic_out, payload)
    except Exception:
        logger.exception(
            "Не удалось отправить результат в Kafka для submission=%s",
            sub_id,
        )


async def _consume_once(settings: Settings) -> None:
    """Один цикл подключения к Kafka. Падает при обрыве — вызывающий ретраит."""
    hosts = _bootstrap_list(settings.kafka_bootstrap_servers)
    semaphore = asyncio.Semaphore(settings.max_concurrent_runs)
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_in,
        bootstrap_servers=hosts,
        group_id=settings.kafka_group_id,
        auto_offset_reset=settings.kafka_auto_offset_reset,
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=hosts,
        value_serializer=lambda v: json.dumps(
            v, ensure_ascii=False
        ).encode("utf-8"),
    )
    await consumer.start()
    await producer.start()
    logger.info(
        "Kafka consumer готов: topic=%s group=%s",
        settings.kafka_topic_in,
        settings.kafka_group_id,
    )
    try:
        async for msg in consumer:
            await _handle_message(
                msg.value, producer, settings, semaphore
            )
    finally:
        await producer.stop()
        await consumer.stop()
        logger.info("Kafka consumer/producer остановлены.")


async def _consume_loop(settings: Settings) -> None:
    """Держит consumer живым: после ребута Kafka / сетевых сбоев переподключается."""
    delay = 3.0
    while True:
        try:
            await _consume_once(settings)
            delay = 3.0
        except asyncio.CancelledError:
            logger.info("Остановка consumer…")
            raise
        except Exception:
            logger.exception(
                "Kafka consumer упал, повтор через %.0f с "
                "(health остаётся ок — без ретрая проверки зависают)",
                delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 30.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    task = asyncio.create_task(_consume_loop(settings))
    app.state.consumer_task = task
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Code check runner", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
