"""Проверка существования урока для пользовательских комментариев."""

from __future__ import annotations

import uuid

from django.utils.translation import gettext_lazy as _

LESSON_KINDS = frozenset({"theory", "radio", "checkbox", "coding"})


def lesson_exists(kind: str, lesson_public_id) -> bool:
    from content.models import (
        CodingChallenge,
        LessonCheckBoxQuestion,
        LessonRadioQuestion,
        LessonTheory,
    )

    try:
        pid = (
            lesson_public_id
            if isinstance(lesson_public_id, uuid.UUID)
            else uuid.UUID(str(lesson_public_id))
        )
    except (TypeError, ValueError):
        return False

    checks = {
        "theory": lambda: LessonTheory.objects.filter(
            public_id=pid, is_active=True
        ).exists(),
        "radio": lambda: LessonRadioQuestion.objects.filter(
            public_id=pid, is_active=True
        ).exists(),
        "checkbox": lambda: LessonCheckBoxQuestion.objects.filter(
            public_id=pid, is_active=True
        ).exists(),
        "coding": lambda: CodingChallenge.objects.filter(
            public_id=pid, is_active=True
        ).exists(),
    }
    checker = checks.get(kind)
    return bool(checker and checker())


def lesson_kind_label(kind: str) -> str:
    labels = {
        "theory": _("теория"),
        "radio": _("вопрос"),
        "checkbox": _("вопрос"),
        "coding": _("задача"),
    }
    return str(labels.get(kind, kind))
