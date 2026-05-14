#!/usr/bin/env python3
"""Trusted judge: sequential tests, stop on first failure. Final line = JSON."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

MANIFEST = Path(os.environ.get("MANIFEST_PATH", "/work/manifest.json"))
SOLUTION = Path("/tmp/solution.py")
# Максимум символов вывода в JSON для API (stdout/stderr/ожидаемый ответ).
_MAX_FEEDBACK_CHARS = 8000


def _clip(s: str, limit: int = _MAX_FEEDBACK_CHARS) -> str:
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 3)] + "..."


def _normalize(s: str | None) -> str:
    if s is None:
        return ""
    return str(s).rstrip("\n")


def _emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def _valid_tests(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return sorted(
        out,
        key=lambda t: int(t.get("order_index") or 0),
    )


def main() -> int:
    """
    Всегда завершаемся с кодом 0, если напечатан итоговый JSON — иначе
    ``docker run`` бросает ContainerError и раннер не разберёт stdout.
    """
    if not MANIFEST.is_file():
        _emit(
            {
                "status": "error",
                "passed_tests": 0,
                "total_tests": 0,
                "message": "Файл manifest не найден.",
            }
        )
        return 0
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        _emit(
            {
                "status": "error",
                "passed_tests": 0,
                "total_tests": 0,
                "message": f"Некорректный manifest: {e}",
            }
        )
        return 0

    code = data.get("code")
    if code is None:
        code = ""
    if not isinstance(code, str):
        code = str(code)

    tests_sorted = _valid_tests(data.get("test_cases"))
    total = len(tests_sorted)
    time_limit_ms = int(data.get("time_limit_ms") or 2000)
    deadline = time.monotonic() + max(time_limit_ms / 1000.0, 0.01)

    try:
        SOLUTION.write_text(code, encoding="utf-8")
    except OSError as e:
        _emit(
            {
                "status": "error",
                "passed_tests": 0,
                "total_tests": total,
                "message": f"Не удалось записать решение: {e}",
            }
        )
        return 0

    passed = 0
    for tc in tests_sorted:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            n = passed + 1
            _emit(
                {
                    "status": "error",
                    "passed_tests": passed,
                    "total_tests": total,
                    "message": f"Превышен общий лимит времени (тест № {n}).",
                    "failed_test_number": n,
                    "actual_output": None,
                    "expected_output": None,
                }
            )
            return 0

        hidden = bool(tc.get("is_hidden"))
        inp = tc.get("input_data")
        exp = tc.get("expected_output")
        if inp is None:
            inp = ""
        elif not isinstance(inp, str):
            inp = str(inp)
        if exp is None:
            exp = ""
        elif not isinstance(exp, str):
            exp = str(exp)

        timeout_sec = max(min(remaining, 60.0), 0.001)
        try:
            proc = subprocess.run(
                [sys.executable, "-u", str(SOLUTION)],
                input=inp,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd="/tmp",
            )
        except subprocess.TimeoutExpired:
            n = passed + 1
            msg = (
                f"Превышен лимит времени на скрытом тесте № {n}."
                if hidden
                else f"Превышен лимит времени на тесте № {n}."
            )
            _emit(
                {
                    "status": "error",
                    "passed_tests": passed,
                    "total_tests": total,
                    "message": msg,
                    "failed_test_number": n,
                    "actual_output": None,
                    "expected_output": None,
                }
            )
            return 0

        if proc.returncode != 0:
            n = passed + 1
            tail = (proc.stderr or "")[-800:].strip()
            err_full = _clip((proc.stderr or "").strip())
            if hidden:
                msg = f"Ошибка выполнения на скрытом тесте № {n}."
                act: str | None = None
            else:
                msg = (
                    f"Ошибка выполнения на тесте № {n} (код {proc.returncode})"
                    + (f": {tail}" if tail else ".")
                )
                act = err_full if err_full else _clip((proc.stdout or "").strip())
            _emit(
                {
                    "status": "error",
                    "passed_tests": passed,
                    "total_tests": total,
                    "message": msg,
                    "failed_test_number": n,
                    "actual_output": act,
                    "expected_output": None,
                }
            )
            return 0

        got = _normalize(proc.stdout)
        want = _normalize(exp)
        if got != want:
            n = passed + 1
            if hidden:
                msg = f"Неверный ответ на скрытом тесте № {n}."
                act_out: str | None = None
                exp_out: str | None = None
            else:
                msg = f"Неверный ответ на тесте № {n}."
                act_out = _clip(got)
                exp_out = _clip(want)
            _emit(
                {
                    "status": "wrong_answer",
                    "passed_tests": passed,
                    "total_tests": total,
                    "message": msg,
                    "failed_test_number": n,
                    "actual_output": act_out,
                    "expected_output": exp_out,
                }
            )
            return 0

        passed += 1

    _emit(
        {
            "status": "accepted",
            "passed_tests": passed,
            "total_tests": total,
            "message": "Все тесты пройдены.",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
