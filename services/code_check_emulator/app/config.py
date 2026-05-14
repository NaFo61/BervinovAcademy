"""Настройки воркера проверки кода из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip()


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    kafka_topic_in: str
    kafka_topic_out: str
    kafka_group_id: str
    kafka_auto_offset_reset: str
    log_level: str
    sandbox_image: str
    max_concurrent_runs: int
    docker_run_timeout_buffer_sec: int
    sandbox_cpu_period: int
    sandbox_cpu_quota: int
    sandbox_pids_limit: int


def load_settings() -> Settings:
    return Settings(
        kafka_bootstrap_servers=_env(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        ),
        kafka_topic_in=_env("KAFKA_TOPIC_IN", "code-submissions"),
        kafka_topic_out=_env(
            "KAFKA_TOPIC_CODE_RESULTS", "code-submission-results"
        ),
        kafka_group_id=_env("KAFKA_GROUP_ID", "code-check-runner"),
        kafka_auto_offset_reset=_env("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
        sandbox_image=_env(
            "SANDBOX_IMAGE", "bervinov-academy-code-sandbox:local"
        ),
        max_concurrent_runs=max(1, _env_int("MAX_CONCURRENT_RUNS", 2)),
        docker_run_timeout_buffer_sec=max(
            1, _env_int("DOCKER_RUN_TIMEOUT_BUFFER_SEC", 5)
        ),
        sandbox_cpu_period=max(1000, _env_int("SANDBOX_CPU_PERIOD", 100_000)),
        sandbox_cpu_quota=max(
            1000, _env_int("SANDBOX_CPU_QUOTA", 100_000)
        ),
        sandbox_pids_limit=max(8, _env_int("SANDBOX_PIDS_LIMIT", 128)),
    )
