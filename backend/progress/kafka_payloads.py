"""
Сборка JSON для публикации отправки кода в Kafka (воркер без доступа к БД).
"""

from __future__ import annotations

from typing import Any

from django.db.models import Prefetch

from content.models import CodingChallenge, TestCase
from progress.models import CodeSubmission


def build_code_submission_kafka_payload(
    submission: CodeSubmission,
) -> dict[str, Any]:
    """
    Собирает JSON для воркера. Если тестов у задачи нет — ``test_cases`` пустой список.
    """
    challenge = (
        CodingChallenge.objects.select_related("module", "course")
        .prefetch_related(
            Prefetch(
                "test_cases",
                queryset=TestCase.objects.order_by("order_index"),
            )
        )
        .get(pk=submission.challenge_id)
    )
    test_cases = list(challenge.test_cases.all())

    payload: dict[str, Any] = {
        "submission_public_id": str(submission.public_id),
        "user_public_id": str(submission.user.public_id),
        "challenge_public_id": str(challenge.public_id),
        "challenge_order_index": challenge.order_index,
        "code": submission.code,
        "status": submission.status,
        "limits": {
            "time_limit_ms": challenge.time_limit_ms,
            "memory_limit_mb": challenge.memory_limit_mb,
        },
        "test_cases": [
            {
                "order_index": tc.order_index,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden,
            }
            for tc in test_cases
        ],
    }
    if challenge.module_id:
        payload["module_public_id"] = str(challenge.module.public_id)
    if challenge.course_id:
        payload["course_public_id"] = str(challenge.course.public_id)
    if submission.submitted_at:
        payload["submitted_at"] = submission.submitted_at.isoformat()
    return payload
