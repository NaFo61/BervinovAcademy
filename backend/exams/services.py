"""Бизнес-логика контрольных работ."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from exams.models import (
    ExamAccessGrant,
    ExamAttempt,
    ExamAttemptStep,
    ExamFocusEvent,
)

from content.container_lessons import iter_container_lessons
from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Exam,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    RadioAnswerOption,
)
from progress.models import (
    CodeSubmission,
    UserAnswerCheckBox,
    UserAnswerRadio,
    UserLessonTheoryRead,
)
from progress.stats import build_completed_lesson_keys


class ExamAccessError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _lesson_key(kind: str, public_id) -> str:
    return f"{kind}-{public_id}"


def exam_lesson_items(exam: Exam, active_only: bool = True):
    return iter_container_lessons(exam, active_only=active_only)


def exam_max_score(exam: Exam) -> int:
    total = 0
    for kind, item in exam_lesson_items(exam):
        if kind in ("radio", "checkbox"):
            total += item.points
        elif kind == "coding":
            total += item.points
    return total


def _module_completed(user, module: Module) -> bool:
    [module.id]
    keys = build_completed_lesson_keys(user, module.course)
    from content.container_lessons import iter_container_lessons

    required = set()
    for kind, lesson in iter_container_lessons(module, active_only=True):
        required.add(_lesson_key(kind, lesson.public_id))
    if not required:
        return True
    return required.issubset(keys)


def _has_active_grant(
    user, exam: Exam, grant_types: list[str] | None = None
) -> bool:
    qs = ExamAccessGrant.objects.filter(
        user=user,
        exam=exam,
        is_active=True,
        consumed_at__isnull=True,
    )
    if grant_types:
        qs = qs.filter(grant_type__in=grant_types)
    return qs.exists()


def _latest_finished_attempt(user, exam: Exam):
    return (
        ExamAttempt.objects.filter(
            user=user,
            exam=exam,
            status__in=(
                ExamAttempt.Status.SUBMITTED,
                ExamAttempt.Status.EXPIRED,
            ),
        )
        .order_by("-submitted_at", "-started_at")
        .first()
    )


def get_exam_access(user, exam: Exam) -> dict:
    """Проверка, может ли ученик начать КР."""
    reasons = []

    for module in exam.prerequisite_modules.filter(is_active=True):
        if not _module_completed(user, module):
            reasons.append(
                {
                    "code": "prerequisite_module",
                    "module_public_id": str(module.public_id),
                    "module_title": module.title,
                }
            )

    active = ExamAttempt.objects.filter(
        user=user,
        exam=exam,
        status=ExamAttempt.Status.IN_PROGRESS,
    ).first()

    finished = _latest_finished_attempt(user, exam)

    if exam.mentor_unlock_required and not active:
        if not _has_active_grant(
            user, exam, [ExamAccessGrant.GrantType.UNLOCK]
        ):
            reasons.append({"code": "mentor_unlock_required"})

    if finished and not active:
        if not _has_active_grant(
            user, exam, [ExamAccessGrant.GrantType.RETAKE]
        ):
            reasons.append(
                {
                    "code": "already_completed",
                    "attempt_public_id": str(finished.public_id),
                    "passed": finished.passed,
                    "score": finished.score,
                    "max_score": finished.max_score,
                }
            )

    blocked = len(reasons) > 0
    can_start = not blocked and not active

    return {
        "can_start": can_start,
        "blocked": blocked,
        "reasons": reasons,
        "active_attempt_public_id": str(active.public_id) if active else None,
        "latest_attempt": (
            _serialize_attempt_brief(finished) if finished else None
        ),
    }


def _serialize_attempt_brief(attempt: ExamAttempt | None) -> dict | None:
    if not attempt:
        return None
    return {
        "public_id": str(attempt.public_id),
        "status": attempt.status,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "passed": attempt.passed,
        "submitted_at": (
            attempt.submitted_at.isoformat() if attempt.submitted_at else None
        ),
    }


def expire_attempt_if_needed(attempt: ExamAttempt) -> ExamAttempt:
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        return attempt
    if timezone.now() >= attempt.expires_at:
        return finalize_attempt(attempt, ExamAttempt.SubmitReason.TIMEOUT)
    return attempt


def remaining_seconds(attempt: ExamAttempt) -> int:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        return 0
    delta = attempt.expires_at - timezone.now()
    return max(0, int(delta.total_seconds()))


@transaction.atomic
def start_attempt(user, exam: Exam) -> ExamAttempt:
    access = get_exam_access(user, exam)
    if access.get("active_attempt_public_id"):
        attempt = ExamAttempt.objects.get(
            public_id=access["active_attempt_public_id"]
        )
        return expire_attempt_if_needed(attempt)
    if not access["can_start"]:
        code = access["reasons"][0]["code"] if access["reasons"] else "blocked"
        raise ExamAccessError(code, "Нельзя начать контрольную")

    grant_qs = ExamAccessGrant.objects.filter(
        user=user,
        exam=exam,
        is_active=True,
        consumed_at__isnull=True,
    )
    grant = grant_qs.order_by("-created_at").first()

    started = timezone.now()
    attempt = ExamAttempt.objects.create(
        user=user,
        exam=exam,
        status=ExamAttempt.Status.IN_PROGRESS,
        started_at=started,
        expires_at=started + timedelta(minutes=exam.duration_minutes),
        max_score=exam_max_score(exam),
    )

    if grant:
        grant.consumed_at = timezone.now()
        grant.is_active = False
        grant.save(update_fields=["consumed_at", "is_active"])

    return attempt


def get_attempt_steps_payload(attempt: ExamAttempt) -> list[dict]:
    steps = []
    for kind, item in exam_lesson_items(attempt.exam):
        step = attempt.steps.filter(
            step_kind=kind, content_public_id=item.public_id
        ).first()
        steps.append(
            {
                "kind": kind,
                "public_id": str(item.public_id),
                "title": item.title,
                "order_index": item.order_index,
                "max_points": item.points if kind != "theory" else 0,
                "answered": step is not None,
                "is_correct": step.is_correct if step else None,
                "points_earned": step.points_earned if step else 0,
                "payload": step.payload if step else {},
            }
        )
    return steps


def serialize_attempt(attempt: ExamAttempt) -> dict:
    attempt = expire_attempt_if_needed(attempt)
    exam = attempt.exam
    live_score = sum(s.points_earned for s in attempt.steps.all())
    display_score = live_score if attempt.is_active else attempt.score
    return {
        "public_id": str(attempt.public_id),
        "exam_public_id": str(exam.public_id),
        "exam_title": exam.title,
        "course_public_id": str(exam.course.public_id),
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat(),
        "expires_at": attempt.expires_at.isoformat(),
        "submitted_at": (
            attempt.submitted_at.isoformat() if attempt.submitted_at else None
        ),
        "submit_reason": attempt.submit_reason or None,
        "remaining_seconds": remaining_seconds(attempt),
        "score": display_score,
        "max_score": attempt.max_score or exam_max_score(exam),
        "passed": attempt.passed if not attempt.is_active else None,
        "focus_warn_count": attempt.focus_warn_count,
        "navigation_mode": exam.navigation_mode,
        "tab_policy": exam.tab_policy,
        "tab_warn_limit": exam.tab_warn_limit,
        "steps": get_attempt_steps_payload(attempt),
    }


def _get_exam_lesson(kind: str, public_id, exam: Exam):
    if kind == ExamAttemptStep.StepKind.THEORY:
        return LessonTheory.objects.get(
            public_id=public_id, exam=exam, is_active=True
        )
    if kind == ExamAttemptStep.StepKind.RADIO:
        return LessonRadioQuestion.objects.get(
            public_id=public_id, exam=exam, is_active=True
        )
    if kind == ExamAttemptStep.StepKind.CHECKBOX:
        return LessonCheckBoxQuestion.objects.get(
            public_id=public_id, exam=exam, is_active=True
        )
    if kind == ExamAttemptStep.StepKind.CODING:
        return CodingChallenge.objects.get(
            public_id=public_id, exam=exam, is_active=True
        )
    raise ValueError(f"Unknown step kind: {kind}")


def _linear_allows(attempt: ExamAttempt, kind: str, public_id) -> bool:
    if attempt.exam.navigation_mode != Exam.NavigationMode.LINEAR:
        return True
    for step_kind, item in exam_lesson_items(attempt.exam):
        key = (step_kind, str(item.public_id))
        if key == (kind, str(public_id)):
            return True
        step = attempt.steps.filter(
            step_kind=step_kind, content_public_id=item.public_id
        ).first()
        if step_kind == "theory":
            if not step:
                return False
            continue
        if not step or not step.is_correct:
            return False
    return True


@transaction.atomic
def record_theory_read(
    attempt: ExamAttempt, lesson: LessonTheory
) -> ExamAttemptStep:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ExamAccessError("not_in_progress", "Попытка уже завершена")
    if not _linear_allows(attempt, "theory", lesson.public_id):
        raise ExamAccessError(
            "linear_locked", "Сначала завершите предыдущие задания"
        )

    step, _ = ExamAttemptStep.objects.update_or_create(
        attempt=attempt,
        step_kind=ExamAttemptStep.StepKind.THEORY,
        content_public_id=lesson.public_id,
        defaults={
            "order_index": lesson.order_index,
            "is_correct": True,
            "points_earned": 0,
            "max_points": 0,
            "payload": {"read": True},
        },
    )
    return step


@transaction.atomic
def record_radio_answer(
    attempt: ExamAttempt,
    question: LessonRadioQuestion,
    selected: RadioAnswerOption,
) -> ExamAttemptStep:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ExamAccessError("not_in_progress", "Попытка уже завершена")
    if not _linear_allows(attempt, "radio", question.public_id):
        raise ExamAccessError(
            "linear_locked", "Сначала завершите предыдущие задания"
        )

    is_correct = selected.is_correct
    points = question.points if is_correct else 0
    step, _ = ExamAttemptStep.objects.update_or_create(
        attempt=attempt,
        step_kind=ExamAttemptStep.StepKind.RADIO,
        content_public_id=question.public_id,
        defaults={
            "order_index": question.order_index,
            "is_correct": is_correct,
            "points_earned": points,
            "max_points": question.points,
            "payload": {
                "selected_answer_public_id": str(selected.public_id),
                "selected_answer_text": selected.text,
            },
        },
    )
    return step


@transaction.atomic
def record_checkbox_answer(
    attempt: ExamAttempt,
    question: LessonCheckBoxQuestion,
    selected_options,
) -> ExamAttemptStep:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ExamAccessError("not_in_progress", "Попытка уже завершена")
    if not _linear_allows(attempt, "checkbox", question.public_id):
        raise ExamAccessError(
            "linear_locked", "Сначала завершите предыдущие задания"
        )

    correct = set(question.answers.filter(is_correct=True))
    selected = set(selected_options)
    is_correct = selected == correct
    points = question.points if is_correct else 0
    step, _ = ExamAttemptStep.objects.update_or_create(
        attempt=attempt,
        step_kind=ExamAttemptStep.StepKind.CHECKBOX,
        content_public_id=question.public_id,
        defaults={
            "order_index": question.order_index,
            "is_correct": is_correct,
            "points_earned": points,
            "max_points": question.points,
            "payload": {
                "selected_answer_public_ids": [
                    str(o.public_id) for o in selected_options
                ],
            },
        },
    )
    return step


@transaction.atomic
def record_coding_submission(
    attempt: ExamAttempt,
    submission: CodeSubmission,
) -> ExamAttemptStep:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ExamAccessError("not_in_progress", "Попытка уже завершена")
    challenge = submission.challenge
    if not _linear_allows(attempt, "coding", challenge.public_id):
        raise ExamAccessError(
            "linear_locked", "Сначала завершите предыдущие задания"
        )

    passed = (
        submission.status == CodeSubmission.STATUS_COMPLETED
        and submission.total_tests > 0
        and submission.tests_passed >= submission.total_tests
    )
    points = challenge.points if passed else 0
    step, _ = ExamAttemptStep.objects.update_or_create(
        attempt=attempt,
        step_kind=ExamAttemptStep.StepKind.CODING,
        content_public_id=challenge.public_id,
        defaults={
            "order_index": challenge.order_index,
            "is_correct": passed,
            "points_earned": points,
            "max_points": challenge.points,
            "payload": {
                "submission_public_id": str(submission.public_id),
                "tests_passed": submission.tests_passed,
                "total_tests": submission.total_tests,
            },
            "code_submission": submission,
        },
    )
    return step


@transaction.atomic
def record_focus_event(
    attempt: ExamAttempt,
    event_type: str = "visibility_hidden",
    metadata: dict | None = None,
) -> dict:
    attempt = expire_attempt_if_needed(attempt)
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        return {"logged": False, "attempt_status": attempt.status}

    ExamFocusEvent.objects.create(
        attempt=attempt,
        event_type=event_type,
        metadata=metadata or {},
    )

    warn_triggered = False
    if attempt.exam.tab_policy == Exam.TabPolicy.WARN:
        attempt.focus_warn_count += 1
        attempt.save(update_fields=["focus_warn_count"])
        if attempt.focus_warn_count >= attempt.exam.tab_warn_limit:
            finalize_attempt(attempt, ExamAttempt.SubmitReason.WARN_LIMIT)
            warn_triggered = True

    return {
        "logged": True,
        "focus_warn_count": attempt.focus_warn_count,
        "warn_triggered_submit": warn_triggered,
        "attempt_status": attempt.status,
    }


def _compute_attempt_score(attempt: ExamAttempt) -> tuple[int, int]:
    score = 0
    max_score = attempt.max_score or exam_max_score(attempt.exam)
    for step in attempt.steps.all():
        score += step.points_earned
    return score, max_score


def _sync_attempt_to_course_progress(attempt: ExamAttempt):
    user = attempt.user
    for step in attempt.steps.filter(is_correct=True):
        kind = step.step_kind
        pid = step.content_public_id
        if kind == ExamAttemptStep.StepKind.THEORY:
            lesson = LessonTheory.objects.filter(public_id=pid).first()
            if lesson:
                UserLessonTheoryRead.objects.get_or_create(
                    user=user, lesson=lesson
                )
        elif kind == ExamAttemptStep.StepKind.RADIO:
            question = LessonRadioQuestion.objects.filter(
                public_id=pid
            ).first()
            if (
                question
                and not UserAnswerRadio.objects.filter(
                    user=user, question=question, is_correct=True
                ).exists()
            ):
                payload = step.payload or {}
                ans_pid = payload.get("selected_answer_public_id")
                if ans_pid:
                    option = RadioAnswerOption.objects.filter(
                        public_id=ans_pid
                    ).first()
                    if option:
                        UserAnswerRadio.objects.create(
                            user=user,
                            question=question,
                            selected_answer=option,
                        )
        elif kind == ExamAttemptStep.StepKind.CHECKBOX:
            question = LessonCheckBoxQuestion.objects.filter(
                public_id=pid
            ).first()
            if question:
                obj, created = UserAnswerCheckBox.objects.get_or_create(
                    user=user,
                    question=question,
                )
                if created or not obj.is_correct:
                    pids = (step.payload or {}).get(
                        "selected_answer_public_ids"
                    ) or []
                    options = list(
                        CheckBoxAnswerOption.objects.filter(public_id__in=pids)
                    )
                    obj.selected_answers.set(options)
                    obj.is_correct = step.is_correct
                    obj.points_earned = step.points_earned
                    obj.save()
        elif kind == ExamAttemptStep.StepKind.CODING:
            if step.code_submission_id and step.is_correct:
                pass  # CodeSubmission already exists for user


@transaction.atomic
def finalize_attempt(
    attempt: ExamAttempt,
    reason: str,
) -> ExamAttempt:
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        return attempt

    score, max_score = _compute_attempt_score(attempt)
    percent = round(100 * score / max_score) if max_score else 0
    passed = percent >= attempt.exam.pass_score_percent

    if reason == ExamAttempt.SubmitReason.TIMEOUT:
        status = ExamAttempt.Status.EXPIRED
    else:
        status = ExamAttempt.Status.SUBMITTED

    attempt.status = status
    attempt.submit_reason = reason
    attempt.submitted_at = timezone.now()
    attempt.score = score
    attempt.max_score = max_score
    attempt.passed = passed
    attempt.save()

    _sync_attempt_to_course_progress(attempt)
    return attempt


@transaction.atomic
def grant_exam_access(
    user,
    exam: Exam,
    granted_by,
    grant_type: str,
    note: str = "",
) -> ExamAccessGrant:
    return ExamAccessGrant.objects.create(
        user=user,
        exam=exam,
        grant_type=grant_type,
        granted_by=granted_by,
        note=note,
    )


def get_course_exam_summary(user, course) -> dict:
    exams = Exam.objects.filter(course=course, is_active=True).order_by(
        "order_index"
    )
    items = []
    passed = 0
    for exam in exams:
        latest = _latest_finished_attempt(user, exam)
        active = ExamAttempt.objects.filter(
            user=user,
            exam=exam,
            status=ExamAttempt.Status.IN_PROGRESS,
        ).first()
        if latest and latest.passed:
            passed += 1
        items.append(
            {
                "public_id": str(exam.public_id),
                "title": exam.title,
                "order_index": exam.order_index,
                "duration_minutes": exam.duration_minutes,
                "passed": bool(latest and latest.passed),
                "latest_score": latest.score if latest else None,
                "latest_max_score": latest.max_score if latest else None,
                "active_attempt_public_id": (
                    str(active.public_id) if active else None
                ),
            }
        )
    return {
        "total": exams.count(),
        "passed": passed,
        "items": items,
    }
