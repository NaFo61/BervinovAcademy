"""Нормализация и сравнение кратких ответов."""

from __future__ import annotations

import re

NORMALIZE_STRIP_CASEFOLD = "strip_casefold"
NORMALIZE_EXACT = "exact"
NORMALIZE_NUMERIC = "numeric"

_WS_RE = re.compile(r"\s+")


def normalize_answer(value: str, mode: str = NORMALIZE_STRIP_CASEFOLD) -> str:
    text = "" if value is None else str(value)
    if mode == NORMALIZE_EXACT:
        return text
    if mode == NORMALIZE_NUMERIC:
        # Reserved: for now same as strip_casefold (no 01==1).
        text = text.strip()
        text = _WS_RE.sub(" ", text)
        return text.casefold()
    # strip_casefold (default)
    text = text.strip()
    text = _WS_RE.sub(" ", text)
    return text.casefold()


def answers_match(
    correct: str,
    user_answer: str,
    *,
    mode: str = NORMALIZE_STRIP_CASEFOLD,
) -> bool:
    return normalize_answer(correct, mode) == normalize_answer(
        user_answer, mode
    )
