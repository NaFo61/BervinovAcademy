"""Unit-тесты логики конспекта без сети."""

from django.test import override_settings
import pytest

from communication.lesson_summary import (
    DEFAULT_SUMMARY_SYSTEM_PROMPT,
    summarize_transcript,
)


@override_settings(ASSISTANT_LLM_ENABLED=False, OPENAI_API_KEY="")
def test_summarize_transcript_demo_without_llm():
    text = "разобрали циклы for и while, задали три задачи"
    out = summarize_transcript(text)
    assert "демо" in out.lower() or "Конспект" in out
    assert "циклы" in out.lower() or "for" in out.lower()


@override_settings(ASSISTANT_LLM_ENABLED=False)
def test_summarize_empty_raises():
    with pytest.raises(RuntimeError, match="Нет текста"):
        summarize_transcript("   ")


def test_default_prompt_is_russian_school_style():
    assert "ЕГЭ" in DEFAULT_SUMMARY_SYSTEM_PROMPT
    assert "короткий" in DEFAULT_SUMMARY_SYSTEM_PROMPT.lower()
