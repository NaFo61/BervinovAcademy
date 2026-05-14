import uuid

import pytest

from progress.kafka_results_consumer import (
    apply_code_submission_result_payload,
)
from progress.models import CodeSubmission

pytest_plugins = (
    "content.tests.conftest",
    "users.tests.conftest",
)


@pytest.mark.django_db
def test_apply_result_accepted_maps_to_completed(
    student_user, coding_challenge
):
    sub = CodeSubmission.objects.create(
        user=student_user,
        challenge=coding_challenge,
        code="print(1)",
        status="pending",
    )
    ok, reason = apply_code_submission_result_payload(
        {
            "submission_public_id": str(sub.public_id),
            "status": "accepted",
            "message": "ok",
            "passed_tests": 2,
            "total_tests": 2,
        }
    )
    assert ok and reason == ""
    sub.refresh_from_db()
    assert sub.status == CodeSubmission.STATUS_COMPLETED
    assert sub.tests_passed == 2
    assert sub.total_tests == 2
    assert sub.error_message == ""
    assert sub.test_results == {}
    assert sub.completed_at is not None


@pytest.mark.django_db
def test_apply_result_wrong_answer_maps_to_error(
    student_user, coding_challenge
):
    sub = CodeSubmission.objects.create(
        user=student_user,
        challenge=coding_challenge,
        code="print(1)",
        status="pending",
    )
    ok, _ = apply_code_submission_result_payload(
        {
            "submission_public_id": str(sub.public_id),
            "status": "wrong_answer",
            "message": "WA",
            "passed_tests": 0,
            "total_tests": 2,
        }
    )
    assert ok
    sub.refresh_from_db()
    assert sub.status == "error"
    assert sub.error_message == "WA"
    assert sub.test_results == {}


@pytest.mark.django_db
def test_apply_result_wrong_answer_stores_feedback_fields(
    student_user, coding_challenge
):
    sub = CodeSubmission.objects.create(
        user=student_user,
        challenge=coding_challenge,
        code="print(1)",
        status="pending",
    )
    ok, _ = apply_code_submission_result_payload(
        {
            "submission_public_id": str(sub.public_id),
            "status": "wrong_answer",
            "message": "Неверный ответ на тесте № 2.",
            "passed_tests": 1,
            "total_tests": 3,
            "failed_test_number": 2,
            "actual_output": "got",
            "expected_output": "want",
        }
    )
    assert ok
    sub.refresh_from_db()
    assert sub.test_results == {
        "failed_test_number": 2,
        "actual_output": "got",
        "expected_output": "want",
    }


@pytest.mark.django_db
def test_apply_result_missing_submission_id():
    ok, reason = apply_code_submission_result_payload({"status": "accepted"})
    assert not ok
    assert "submission" in reason.lower()


@pytest.mark.django_db
def test_apply_result_unknown_submission(student_user, coding_challenge):
    ok, reason = apply_code_submission_result_payload(
        {
            "submission_public_id": str(uuid.uuid4()),
            "status": "accepted",
            "passed_tests": 0,
            "total_tests": 0,
        }
    )
    assert not ok
    assert "не найдена" in reason


@pytest.mark.django_db
def test_apply_result_does_not_overwrite_completed(
    student_user, coding_challenge
):
    sub = CodeSubmission.objects.create(
        user=student_user,
        challenge=coding_challenge,
        code="print(1)",
        status=CodeSubmission.STATUS_COMPLETED,
        tests_passed=3,
        total_tests=3,
        error_message="",
        test_results={},
    )
    ok, reason = apply_code_submission_result_payload(
        {
            "submission_public_id": str(sub.public_id),
            "status": "wrong_answer",
            "message": "would overwrite",
            "passed_tests": 0,
            "total_tests": 3,
        }
    )
    assert ok and reason == "уже завершена"
    sub.refresh_from_db()
    assert sub.status == CodeSubmission.STATUS_COMPLETED
    assert sub.tests_passed == 3
    assert sub.error_message == ""
    assert sub.test_results == {}
