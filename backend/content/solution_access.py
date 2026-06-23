"""Доступ к эталонному решению (видео + текст) после успеха или N ошибок."""

from __future__ import annotations

SOLUTION_FAIL_THRESHOLD = 3


def _authenticated_user(request):
    if not request:
        return None
    user = getattr(request, "user", None)
    if not user or getattr(user, "is_anonymous", True):
        return None
    return user


def theory_solution_unlocked() -> bool:
    return True


def radio_wrong_attempts(user, question) -> int:
    if not user:
        return 0
    from progress.models import UserAnswerRadio

    return UserAnswerRadio.objects.filter(
        user=user, question=question, is_correct=False
    ).count()


def radio_solution_unlocked(user, question) -> bool:
    if not user:
        return False
    from progress.models import UserAnswerRadio

    if UserAnswerRadio.objects.filter(
        user=user, question=question, is_correct=True
    ).exists():
        return True
    return radio_wrong_attempts(user, question) >= SOLUTION_FAIL_THRESHOLD


def checkbox_wrong_attempts(user, question) -> int:
    if not user:
        return 0
    from progress.models import UserAnswerCheckBox

    row = (
        UserAnswerCheckBox.objects.filter(user=user, question=question)
        .only("failed_attempts", "is_correct")
        .first()
    )
    if not row or row.is_correct:
        return 0
    return row.failed_attempts or 0


def checkbox_solution_unlocked(user, question) -> bool:
    if not user:
        return False
    from progress.models import UserAnswerCheckBox

    row = (
        UserAnswerCheckBox.objects.filter(user=user, question=question)
        .only("is_correct", "failed_attempts")
        .first()
    )
    if not row:
        return False
    if row.is_correct:
        return True
    return (row.failed_attempts or 0) >= SOLUTION_FAIL_THRESHOLD


def coding_wrong_attempts(user, challenge) -> int:
    if not user:
        return 0
    from progress.models import CodeSubmission

    return (
        CodeSubmission.objects.filter(
            user=user,
            challenge=challenge,
        )
        .exclude(status__in=("pending", "running", "completed"))
        .count()
    )


def coding_solution_unlocked(user, challenge) -> bool:
    if not user:
        return False
    from progress.models import CodeSubmission

    if CodeSubmission.objects.filter(
        user=user, challenge=challenge, status="completed"
    ).exists():
        return True
    return coding_wrong_attempts(user, challenge) >= SOLUTION_FAIL_THRESHOLD


def build_reference_solution(obj, request, *, unlocked: bool) -> dict | None:
    if not unlocked:
        return None
    from .video_utils import build_video_payload

    video = build_video_payload(obj, request)
    text = (getattr(obj, "solution_text", None) or "").strip()
    if not video and not text:
        return None
    return {"video": video, "text": text}


def has_reference_solution_content(obj) -> bool:
    video_url = (getattr(obj, "video_url", None) or "").strip()
    video_file = getattr(obj, "video_file", None)
    text = (getattr(obj, "solution_text", None) or "").strip()
    if text:
        return True
    if video_url:
        return True
    try:
        if video_file and video_file.name:
            return True
    except ValueError:
        pass
    return False
