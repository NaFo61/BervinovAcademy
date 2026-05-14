"""Unit-тесты логики manifest / разбора stdout без реального Docker."""

from __future__ import annotations

import json

import pytest

from app.docker_execution import (
    build_kafka_payload_from_sandbox,
    build_manifest_from_payload,
    normalize_stdout_for_compare,
    parse_judge_stdout,
)


def test_normalize_stdout_strips_trailing_newlines() -> None:
    assert normalize_stdout_for_compare("hello\n\n") == "hello"
    assert normalize_stdout_for_compare(None) == ""


def test_build_manifest_sorts_by_order_index() -> None:
    incoming = {
        "code": "print(1)",
        "limits": {"time_limit_ms": 1500, "memory_limit_mb": 128},
        "test_cases": [
            {
                "order_index": 3,
                "input_data": "x",
                "expected_output": "3",
                "is_hidden": True,
            },
            {
                "order_index": 1,
                "input_data": "a",
                "expected_output": "1",
                "is_hidden": False,
            },
            {
                "order_index": 2,
                "input_data": "b",
                "expected_output": "2",
                "is_hidden": False,
            },
        ],
    }
    m = build_manifest_from_payload(incoming)
    assert m["version"] == 1
    assert m["code"] == "print(1)"
    assert m["time_limit_ms"] == 1500
    assert m["memory_limit_mb"] == 128
    assert [t["order_index"] for t in m["test_cases"]] == [1, 2, 3]
    assert m["test_cases"][0]["input_data"] == "a"


def test_build_manifest_defaults_and_skips_bad_cases() -> None:
    m = build_manifest_from_payload(
        {
            "code": None,
            "limits": "not-a-dict",
            "test_cases": [{}, "skip", {"order_index": 1}],
        }
    )
    assert m["code"] == ""
    assert m["time_limit_ms"] >= 1
    assert m["memory_limit_mb"] >= 32
    assert len(m["test_cases"]) == 2


def test_parse_judge_stdout_last_line_json() -> None:
    stdout = (
        "stderr-like line ignored\n"
        '{"status": "wrong_answer", "passed_tests": 1, '
        '"total_tests": 3, "message": "WA"}\n'
    )
    obj = parse_judge_stdout(stdout)
    assert obj["status"] == "wrong_answer"
    assert obj["passed_tests"] == 1
    assert obj["total_tests"] == 3


def test_parse_judge_stdout_empty_raises() -> None:
    with pytest.raises(ValueError):
        parse_judge_stdout("   \n")


def test_build_kafka_payload_coerces_invalid_status() -> None:
    payload = build_kafka_payload_from_sandbox(
        "550e8400-e29b-41d4-a716-446655440000",
        {
            "status": "unknown",
            "passed_tests": -1,
            "total_tests": "x",
            "message": None,
        },
    )
    assert payload["submission_public_id"] == (
        "550e8400-e29b-41d4-a716-446655440000"
    )
    assert payload["status"] == "error"
    assert payload["passed_tests"] == 0
    assert payload["total_tests"] == 0


def test_build_kafka_payload_round_trip_json_line() -> None:
    inner = {
        "status": "accepted",
        "passed_tests": 2,
        "total_tests": 2,
        "message": "Все тесты пройдены.",
    }
    line = json.dumps(inner, ensure_ascii=False)
    parsed = parse_judge_stdout(f"noise\n{line}\n")
    out = build_kafka_payload_from_sandbox("sub-1", parsed)
    assert out["status"] == "accepted"
    assert out["passed_tests"] == 2
    assert out["total_tests"] == 2


def test_build_kafka_payload_passes_failure_feedback() -> None:
    inner = {
        "status": "wrong_answer",
        "passed_tests": 1,
        "total_tests": 3,
        "message": "Неверный ответ на тесте № 2.",
        "failed_test_number": 2,
        "actual_output": "aa",
        "expected_output": "a",
    }
    out = build_kafka_payload_from_sandbox("sub-2", inner)
    assert out["submission_public_id"] == "sub-2"
    assert out["failed_test_number"] == 2
    assert out["actual_output"] == "aa"
    assert out["expected_output"] == "a"
