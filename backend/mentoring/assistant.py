"""LLM / mock assistant for lesson-context questions."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from django.conf import settings

from mentoring.models import (
    DEFAULT_ASSISTANT_BASE_PROMPT,
    AssistantSettings,
)

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def render_prompt_template(template: str, values: dict) -> str:
    """Replace ``{{name}}``; unknown names → empty string."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        raw = values.get(key, "")
        if raw is None:
            return ""
        return str(raw)

    return _PLACEHOLDER_RE.sub(repl, template or "")


def _format_public_tests(challenge) -> str:
    lines = []
    for tc in challenge.test_cases.filter(is_hidden=False).order_by(
        "order_index"
    ):
        lines.append(
            f"#{tc.order_index}\n"
            f"Ввод:\n{tc.input_data}\n"
            f"Ожидаемый вывод:\n{tc.expected_output}"
        )
    return "\n\n".join(lines) if lines else "(публичных тестов нет)"


def _condition_from_challenge(challenge) -> str:
    parts = []
    if (challenge.description or "").strip():
        parts.append(challenge.description.strip())
    if (challenge.instructions or "").strip():
        parts.append(challenge.instructions.strip())
    return "\n\n".join(parts)


def _load_coding_challenge(context: dict):
    pid = (context.get("lesson_public_id") or "").strip()
    kind = (context.get("lesson_kind") or "").strip().lower()
    if not pid:
        return None
    if kind and kind not in ("coding", "code", "challenge"):
        return None
    from content.models import CodingChallenge

    try:
        return (
            CodingChallenge.objects.select_related("course")
            .prefetch_related("test_cases")
            .get(public_id=pid)
        )
    except (CodingChallenge.DoesNotExist, ValueError, TypeError):
        return None


def build_prompt_values(context: dict | None) -> dict[str, str]:
    ctx = dict(context or {})
    challenge = _load_coding_challenge(ctx)

    title = (ctx.get("lesson_title") or "").strip()
    course = (ctx.get("course_title") or "").strip()
    condition = (ctx.get("lesson_statement") or "").strip()
    tests = (ctx.get("tests_blurb") or "").strip()
    code = (ctx.get("user_code") or "").strip()

    if challenge:
        if not title:
            title = challenge.title or ""
        if not course and challenge.course_id:
            course = challenge.course.title or ""
        ch_condition = _condition_from_challenge(challenge)
        if ch_condition:
            condition = ch_condition
        tests = _format_public_tests(challenge)

    return {
        "condition": condition[:4000],
        "tests": tests[:4000],
        "title": title[:500],
        "course": course[:500],
        "code": code[:8000],
    }


def resolve_prompt_template(context: dict | None) -> str:
    """Override на задаче > base settings > встроенный дефолт."""
    ctx = context or {}
    challenge = _load_coding_challenge(ctx)
    if challenge and (challenge.assistant_prompt or "").strip():
        return challenge.assistant_prompt.strip()
    try:
        solo = AssistantSettings.objects.filter(pk=1).first()
        if solo and (solo.base_prompt or "").strip():
            return solo.base_prompt.strip()
    except Exception:  # noqa: BLE001 — таблица ещё не мигрирована
        pass
    return DEFAULT_ASSISTANT_BASE_PROMPT


def build_system_prompt(context: dict | None) -> str:
    template = resolve_prompt_template(context)
    values = build_prompt_values(context)
    return render_prompt_template(template, values)


def _context_blurb(context: dict | None) -> str:
    """Короткое описание для mock-режима."""
    values = build_prompt_values(context)
    parts = []
    if values["course"]:
        parts.append(f"Курс: {values['course']}")
    if values["title"]:
        kind = (context or {}).get("lesson_kind") or "урок"
        parts.append(f"{kind}: {values['title']}")
    if values["condition"]:
        parts.append(f"Условие:\n{values['condition'][:1200]}")
    if values["tests"]:
        parts.append(f"Тесты:\n{values['tests'][:800]}")
    return "\n".join(parts) if parts else "Контекст урока не передан."


def _mock_reply(*, message: str, context: dict | None) -> dict:
    blurb = _context_blurb(context)
    reply = (
        "Я ИИ-помощник (демо-режим без ключа LLM).\n\n"
        f"Вопрос: {message.strip() or '—'}\n\n"
        f"Контекст задания:\n{blurb}\n\n"
        "Подсказка: сформулируйте, что уже пробовали и где застряли. "
        "Когда в .env появится ключ Gemini (OPENAI_API_KEY) и "
        "ASSISTANT_LLM_ENABLED=true, ответы станут от настоящей модели."
    )
    return {"reply": reply, "mode": "mock", "model": None}


def _llm_enabled() -> bool:
    if not getattr(settings, "ASSISTANT_LLM_ENABLED", False):
        return False
    return bool(getattr(settings, "OPENAI_API_KEY", "") or "")


def _call_openai_compatible(
    *, message: str, history: list[dict], context: dict | None
) -> dict:
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    base = (getattr(settings, "OPENAI_BASE_URL", "") or "").rstrip("/")
    key = settings.OPENAI_API_KEY
    system = build_system_prompt(context)
    messages = [{"role": "system", "content": system}]
    for item in history[-12:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:4000]})
    messages.append(
        {"role": "user", "content": (message or "").strip()[:4000]}
    )

    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": 0.4}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"LLM HTTP {exc.code}: {body}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    choices = data.get("choices") or []
    content = ""
    if choices:
        content = (
            (choices[0].get("message") or {}).get("content") or ""
        ).strip()
    if not content:
        raise RuntimeError("Пустой ответ модели.")
    return {"reply": content, "mode": "llm", "model": model}


def generate_assistant_reply(
    *,
    message: str,
    history: list[dict] | None = None,
    context: dict | None = None,
) -> dict:
    text = (message or "").strip()
    if not text:
        return {
            "reply": "Напишите вопрос по текущему заданию.",
            "mode": "mock",
            "model": None,
        }
    if _llm_enabled():
        try:
            return _call_openai_compatible(
                message=text,
                history=list(history or []),
                context=context,
            )
        except Exception:  # noqa: BLE001 — fallback to mock
            mock = _mock_reply(message=text, context=context)
            mock["reply"] = (
                "Не удалось связаться с LLM, поэтому демо-ответ:\n\n"
                + mock["reply"]
            )
            mock["mode"] = "mock_fallback"
            return mock
    return _mock_reply(message=text, context=context)
