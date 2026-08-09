"""LLM / mock assistant for lesson-context questions."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from django.conf import settings


def _context_blurb(context: dict | None) -> str:
    ctx = context or {}
    parts = []
    if ctx.get("course_title"):
        parts.append(f"Курс: {ctx['course_title']}")
    if ctx.get("lesson_title"):
        kind = ctx.get("lesson_kind") or "урок"
        parts.append(f"{kind}: {ctx['lesson_title']}")
    statement = (ctx.get("lesson_statement") or "").strip()
    if statement:
        clipped = statement[:1200]
        parts.append(f"Условие:\n{clipped}")
    return "\n".join(parts) if parts else "Контекст урока не передан."


def _mock_reply(*, message: str, context: dict | None) -> dict:
    blurb = _context_blurb(context)
    reply = (
        "Я ИИ-помощник (демо-режим без ключа LLM).\n\n"
        f"Вопрос: {message.strip() or '—'}\n\n"
        f"Контекст задания:\n{blurb}\n\n"
        "Подсказка: сформулируйте, что уже пробовали и где застряли. "
        "Когда появится OPENAI_API_KEY, ответы станут от настоящей модели."
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
    system = (
        "Ты помощник ученика онлайн-школы. Отвечай по-русски, кратко и по делу. "
        "Помогай разобраться с текущим заданием, не выдавай готовое полное "
        "решение сразу — сначала наводящие подсказки. Контекст задания:\n"
        f"{_context_blurb(context)}"
    )
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
