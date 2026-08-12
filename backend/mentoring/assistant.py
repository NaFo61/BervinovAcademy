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
_PROMPT_SECTION_SEP = "\n\n---\n\n"

_KIND_ALIASES = {
    "coding": "coding",
    "code": "coding",
    "challenge": "coding",
    "theory": "theory",
    "radio": "radio",
    "checkbox": "checkbox",
    "short_answer": "short_answer",
    "short-answer": "short_answer",
}


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


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")


def _normalize_kind(raw: str) -> str:
    return _KIND_ALIASES.get((raw or "").strip().lower(), "")


def _load_lesson(context: dict):
    """Return ``(kind, instance)`` or ``(None, None)``."""
    pid = (context.get("lesson_public_id") or "").strip()
    if not pid:
        return None, None
    kind = _normalize_kind(context.get("lesson_kind") or "")
    from content.editor_registry import LESSON_KINDS, lesson_model

    kinds = [kind] if kind in LESSON_KINDS else list(LESSON_KINDS)
    for k in kinds:
        model = lesson_model(k)
        qs = model.objects.select_related(
            "course",
            "module",
            "module__course",
            "exam",
            "exam__course",
        )
        if k == "coding":
            qs = qs.prefetch_related("test_cases")
        try:
            return k, qs.get(public_id=pid)
        except (model.DoesNotExist, ValueError, TypeError):
            continue
    return None, None


def _condition_from_lesson(kind: str, lesson) -> tuple[str, str]:
    """Return ``(condition, instructions)`` for placeholders."""
    if kind == "coding":
        parts = []
        if (lesson.description or "").strip():
            parts.append(lesson.description.strip())
        instructions = (lesson.instructions or "").strip()
        if instructions:
            parts.append(instructions)
        return "\n\n".join(parts), instructions
    if kind == "theory":
        text = _strip_html(lesson.content or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text, ""
    question = (getattr(lesson, "question_text", None) or "").strip()
    return question, ""


def _course_for_lesson(lesson):
    if getattr(lesson, "module_id", None) and lesson.module_id:
        return lesson.module.course
    if getattr(lesson, "course_id", None) and lesson.course_id:
        return lesson.course
    if getattr(lesson, "exam_id", None) and lesson.exam_id:
        return lesson.exam.course
    return None


def _base_prompt_text() -> str:
    try:
        solo = AssistantSettings.objects.filter(pk=1).first()
        if solo and (solo.base_prompt or "").strip():
            return solo.base_prompt.strip()
    except Exception:  # noqa: BLE001 — таблица ещё не мигрирована
        pass
    return DEFAULT_ASSISTANT_BASE_PROMPT


def build_prompt_values(context: dict | None) -> dict[str, str]:
    ctx = dict(context or {})
    kind, lesson = _load_lesson(ctx)

    title = (ctx.get("lesson_title") or "").strip()
    course = (ctx.get("course_title") or "").strip()
    module = (ctx.get("module_title") or "").strip()
    condition = (ctx.get("lesson_statement") or "").strip()
    instructions = (ctx.get("lesson_instructions") or "").strip()
    tests = (ctx.get("tests_blurb") or "").strip()
    code = (ctx.get("user_code") or "").strip()
    kind_label = kind or _normalize_kind(ctx.get("lesson_kind") or "") or ""

    if lesson:
        if not title:
            title = lesson.title or ""
        course_obj = _course_for_lesson(lesson)
        if not course and course_obj is not None:
            course = course_obj.title or ""
        if not module and getattr(lesson, "module_id", None):
            module = lesson.module.title or ""
        db_condition, db_instructions = _condition_from_lesson(kind, lesson)
        if db_condition:
            condition = db_condition
        if db_instructions:
            instructions = db_instructions
        if kind == "coding":
            tests = _format_public_tests(lesson)

    return {
        "condition": condition[:8000],
        "instructions": instructions[:8000],
        "tests": tests[:4000],
        "title": title[:500],
        "course": course[:500],
        "module": module[:500],
        "kind": kind_label[:64],
        "code": code[:8000],
    }


def resolve_prompt_template(context: dict | None) -> str:
    """Сборка: общий + курс + модуль + урок (пустые пропускаются)."""
    parts = [_base_prompt_text()]
    kind, lesson = _load_lesson(context or {})
    course_obj = _course_for_lesson(lesson) if lesson else None
    if course_obj is not None:
        course_prompt = (course_obj.assistant_prompt or "").strip()
        if course_prompt:
            parts.append(course_prompt)
    if lesson and getattr(lesson, "module_id", None):
        module_prompt = (lesson.module.assistant_prompt or "").strip()
        if module_prompt:
            parts.append(module_prompt)
    if lesson:
        task_prompt = (getattr(lesson, "assistant_prompt", None) or "").strip()
        if task_prompt:
            parts.append(task_prompt)
    return _PROMPT_SECTION_SEP.join(parts)


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
    if values["module"]:
        parts.append(f"Модуль: {values['module']}")
    if values["title"]:
        kind = values["kind"] or (context or {}).get("lesson_kind") or "урок"
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
        "Когда в .env появятся OPENAI_API_KEY (например ProxyAPI) и "
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
