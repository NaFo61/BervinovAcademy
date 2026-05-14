"""
Сборка manifest, запуск одного контейнера песочницы, разбор JSON-результата.
"""

from __future__ import annotations

import concurrent.futures
import io
import json
import logging
import tarfile
from typing import Any

logger = logging.getLogger(__name__)


def normalize_stdout_for_compare(s: str | None) -> str:
    """Та же политика, что в ``services/code_check_sandbox/judge.py``."""
    if s is None:
        return ""
    return str(s).rstrip("\n")


def build_manifest_from_payload(incoming: dict[str, Any]) -> dict[str, Any]:
    """Упорядочить тесты по ``order_index`` и вынести лимиты из payload."""
    code = incoming.get("code")
    if code is None:
        code = ""
    elif not isinstance(code, str):
        code = str(code)

    limits = incoming.get("limits") or {}
    if not isinstance(limits, dict):
        limits = {}

    time_limit_ms = int(limits.get("time_limit_ms") or 2000)
    memory_limit_mb = int(limits.get("memory_limit_mb") or 256)

    raw_cases = incoming.get("test_cases") or []
    if not isinstance(raw_cases, list):
        raw_cases = []

    cases: list[dict[str, Any]] = []
    for item in raw_cases:
        if not isinstance(item, dict):
            continue
        cases.append(
            {
                "order_index": int(item.get("order_index") or 0),
                "input_data": item.get("input_data")
                if item.get("input_data") is not None
                else "",
                "expected_output": item.get("expected_output")
                if item.get("expected_output") is not None
                else "",
                "is_hidden": bool(item.get("is_hidden")),
            }
        )
    cases.sort(key=lambda t: t["order_index"])

    return {
        "version": 1,
        "code": code,
        "test_cases": cases,
        "time_limit_ms": max(time_limit_ms, 1),
        "memory_limit_mb": max(memory_limit_mb, 32),
    }


def parse_judge_stdout(stdout: str) -> dict[str, Any]:
    """Последняя непустая строка stdout — JSON с полями judge."""
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("Пустой stdout от песочницы")
    return json.loads(lines[-1])


_MAX_KAFKA_FEEDBACK_CHARS = 8000


def _sanitize_failure_feedback(obj: dict[str, Any]) -> dict[str, Any]:
    """Поля для API пользователя: номер теста, фактический и ожидаемый вывод."""
    out: dict[str, Any] = {}
    n = obj.get("failed_test_number")
    if isinstance(n, int) and n >= 1:
        out["failed_test_number"] = n

    for key in ("actual_output", "expected_output"):
        if key not in obj:
            continue
        val = obj.get(key)
        if val is None:
            out[key] = None
            continue
        if not isinstance(val, str):
            val = str(val)
        if len(val) > _MAX_KAFKA_FEEDBACK_CHARS:
            val = val[: _MAX_KAFKA_FEEDBACK_CHARS - 3] + "..."
        out[key] = val
    return out


def _validate_sandbox_result(obj: dict[str, Any]) -> dict[str, Any]:
    status = (obj.get("status") or "error").strip().lower()
    if status not in ("accepted", "wrong_answer", "error"):
        status = "error"
    passed = obj.get("passed_tests")
    total = obj.get("total_tests")
    if not isinstance(passed, int) or passed < 0:
        passed = 0
    if not isinstance(total, int) or total < 0:
        total = 0
    message = obj.get("message")
    if message is None:
        message = ""
    elif not isinstance(message, str):
        message = str(message)
    base: dict[str, Any] = {
        "status": status,
        "passed_tests": passed,
        "total_tests": total,
        "message": message.strip(),
    }
    base.update(_sanitize_failure_feedback(obj))
    return base


def build_kafka_payload_from_sandbox(
    submission_public_id: str, sandbox: dict[str, Any]
) -> dict[str, Any]:
    """Совместимо с ``progress.kafka_results_consumer``."""
    v = _validate_sandbox_result(sandbox)
    payload: dict[str, Any] = {
        "submission_public_id": submission_public_id,
        "status": v["status"],
        "message": v["message"] or v["status"],
        "passed_tests": v["passed_tests"],
        "total_tests": v["total_tests"],
    }
    for k in ("failed_test_number", "actual_output", "expected_output"):
        if k in v:
            payload[k] = v[k]
    return payload


def _manifest_tar_for_put_archive(manifest: dict[str, Any]) -> bytes:
    """Tar с одним файлом ``manifest.json`` для ``Container.put_archive``."""
    raw = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))
    return buf.getvalue()


def run_submission_in_docker(
    incoming: dict[str, Any],
    settings: Any,
) -> dict[str, Any]:
    """
    Один контейнер песочницы на отправку. Manifest передаётся через API
    ``put_archive`` в ``/work``. При ``read_only`` rootfs запись в ``/work`` из
    слоя образа невозможна, поэтому на ``/work`` вешается анонимный volume.
    """
    import docker
    from docker.errors import APIError, DockerException
    from docker.types import Mount
    from requests.exceptions import ReadTimeout

    submission_id = str(incoming.get("submission_public_id") or "")
    manifest = build_manifest_from_payload(incoming)
    total_cases = len(manifest["test_cases"])
    manifest_tar = _manifest_tar_for_put_archive(manifest)

    mem_mb = int(manifest["memory_limit_mb"])
    time_ms = int(manifest["time_limit_ms"])
    outer_timeout = int(time_ms / 1000) + int(
        settings.docker_run_timeout_buffer_sec
    )
    outer_timeout = max(outer_timeout, 5)

    client = docker.from_env()
    run_kw: dict[str, Any] = {
        "network_mode": "none",
        "read_only": True,
        # Writable /work for put_archive while rootfs stays read-only.
        "mounts": [Mount("/work", None, type="volume")],
        "tmpfs": {
            "/tmp": "rw,nosuid,nodev,size=64m",
        },
        "mem_limit": f"{mem_mb}m",
        "memswap_limit": f"{mem_mb}m",
        "cpu_period": int(settings.sandbox_cpu_period),
        "cpu_quota": int(settings.sandbox_cpu_quota),
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": int(settings.sandbox_pids_limit),
        "user": "1000:1000",
    }
    container = None
    try:
        try:
            container = client.containers.create(
                settings.sandbox_image,
                **run_kw,
            )
        except (APIError, DockerException, OSError) as e:
            logger.exception(
                "Ошибка API Docker при создании контейнера песочницы, submission=%s",
                submission_id,
            )
            return build_kafka_payload_from_sandbox(
                submission_id,
                {
                    "status": "error",
                    "passed_tests": 0,
                    "total_tests": total_cases,
                    "message": f"Ошибка Docker: {e}",
                },
            )

        try:
            if not container.put_archive("/work", manifest_tar):
                logger.error(
                    "put_archive(/work) вернул False submission=%s",
                    submission_id,
                )
                return build_kafka_payload_from_sandbox(
                    submission_id,
                    {
                        "status": "error",
                        "passed_tests": 0,
                        "total_tests": total_cases,
                        "message": "Не удалось передать manifest в песочницу.",
                    },
                )
            container.start()
        except APIError as e:
            logger.exception(
                "Ошибка Docker: put_archive или start контейнера, submission=%s",
                submission_id,
            )
            return build_kafka_payload_from_sandbox(
                submission_id,
                {
                    "status": "error",
                    "passed_tests": 0,
                    "total_tests": total_cases,
                    "message": f"Ошибка Docker: {e}",
                },
            )

        try:
            try:
                wait_out = container.wait(timeout=outer_timeout)
            except ReadTimeout:
                logger.warning(
                    "Таймаут ожидания песочницы submission=%s",
                    submission_id,
                )
                try:
                    container.kill()
                except APIError:
                    logger.debug(
                        "kill песочницы после таймаута не удался",
                        exc_info=True,
                    )
                return build_kafka_payload_from_sandbox(
                    submission_id,
                    {
                        "status": "error",
                        "passed_tests": 0,
                        "total_tests": total_cases,
                        "message": (
                            "Превышено время ожидания проверки (Docker)."
                        ),
                    },
                )

            exit_code = int(wait_out.get("StatusCode", -1))
            stdout_b = container.logs(stdout=True, stderr=False) or b""
            stderr_b = container.logs(stdout=False, stderr=True) or b""
            stdout = stdout_b.decode("utf-8", errors="replace")
            stderr = stderr_b.decode("utf-8", errors="replace")

            if exit_code != 0:
                logger.warning(
                    "Контейнер песочницы завершился с ошибкой submission=%s "
                    "exit=%s stderr_tail=%r",
                    submission_id,
                    exit_code,
                    (stderr or "")[-400:],
                )
                try:
                    parsed = parse_judge_stdout(stdout)
                    sandbox = _validate_sandbox_result(parsed)
                except (ValueError, json.JSONDecodeError, TypeError):
                    sandbox = {
                        "status": "error",
                        "passed_tests": 0,
                        "total_tests": total_cases,
                        "message": (
                            "Песочница завершилась с ошибкой без результата."
                        ),
                    }
                return build_kafka_payload_from_sandbox(submission_id, sandbox)

            try:
                parsed = parse_judge_stdout(stdout)
                sandbox = _validate_sandbox_result(parsed)
            except (ValueError, json.JSONDecodeError, TypeError) as e:
                logger.warning(
                    "Не удалось разобрать stdout песочницы submission=%s: %s",
                    submission_id,
                    e,
                )
                sandbox = {
                    "status": "error",
                    "passed_tests": 0,
                    "total_tests": total_cases,
                    "message": "Некорректный ответ песочницы.",
                }
            return build_kafka_payload_from_sandbox(submission_id, sandbox)
        except APIError as e:
            logger.exception(
                "Ошибка Docker при ожидании контейнера или чтении логов, submission=%s",
                submission_id,
            )
            return build_kafka_payload_from_sandbox(
                submission_id,
                {
                    "status": "error",
                    "passed_tests": 0,
                    "total_tests": total_cases,
                    "message": f"Ошибка Docker: {e}",
                },
            )
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except APIError:
                logger.debug(
                    "Не удалось удалить контейнер песочницы",
                    exc_info=True,
                )


def run_submission_check(
    incoming: dict[str, Any],
    settings: Any,
) -> dict[str, Any]:
    """Один ``docker run`` песочницы на отправку."""
    submission_id = str(incoming.get("submission_public_id") or "")

    if not submission_id:
        return build_kafka_payload_from_sandbox(
            "",
            {
                "status": "error",
                "passed_tests": 0,
                "total_tests": 0,
                "message": "Нет submission_public_id.",
            },
        )

    result = run_submission_in_docker(incoming, settings)
    logger.info(
        "Проверка в Docker завершена: submission=%s, статус=%s, тесты=%s/%s, "
        "сообщение=%r",
        submission_id,
        result.get("status"),
        result.get("passed_tests"),
        result.get("total_tests"),
        (result.get("message") or "")[:300],
    )
    return result
