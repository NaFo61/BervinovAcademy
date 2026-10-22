"""STT + LLM для AI-конспекта урока."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_SYSTEM_PROMPT = (
    "Ты помощник репетитора по информатике (ЕГЭ). "
    "По расшифровке аудио урока ментор↔ученик сделай короткий конспект на русском.\n"
    "Правила:\n"
    "- 8–15 коротких пунктов или небольших абзацев;\n"
    "- что разобрали, какие ошибки/вопросы, что задано домой;\n"
    "- без воды, без приветствий, без Markdown-заголовков уровня #;\n"
    "- можно маркированный список;\n"
    "- если речь шумная/обрывочная — всё равно выдели суть."
)


def _llm_ready() -> bool:
    if not getattr(settings, "ASSISTANT_LLM_ENABLED", False):
        return False
    return bool(getattr(settings, "OPENAI_API_KEY", "") or "")


def transcribe_audio_file(path: Path) -> str:
    """Whisper-compatible ``/audio/transcriptions``."""
    if not _llm_ready():
        raise RuntimeError("LLM/STT не настроены (ASSISTANT_LLM_ENABLED).")

    base = (getattr(settings, "OPENAI_BASE_URL", "") or "").rstrip("/")
    key = settings.OPENAI_API_KEY
    model = getattr(settings, "OPENAI_STT_MODEL", "whisper-1") or "whisper-1"

    boundary = "----BervinovAcademyBoundary"
    filename = path.name or "audio.webm"
    raw = path.read_bytes()
    parts = []
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"{model}\r\n".encode()
    )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="language"\r\n\r\n'
        f"ru\r\n".encode()
    )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + raw
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{base}/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"STT HTTP {exc.code}: {err}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"STT failed: {exc}") from exc

    text = (data.get("text") or "").strip()
    if not text:
        raise RuntimeError("Пустая расшифровка аудио.")
    return text


def summarize_transcript(transcript: str) -> str:
    """Короткий конспект через chat/completions."""
    text = (transcript or "").strip()
    if not text:
        raise RuntimeError("Нет текста для конспекта.")

    if not _llm_ready():
        # Демо без ключа: усечённая расшифровка.
        clipped = text[:1200]
        return (
            "Конспект (демо без LLM):\n\n"
            + clipped
            + ("…" if len(text) > 1200 else "")
        )

    base = (getattr(settings, "OPENAI_BASE_URL", "") or "").rstrip("/")
    key = settings.OPENAI_API_KEY
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    system = (
        getattr(settings, "LESSON_SUMMARY_SYSTEM_PROMPT", "")
        or DEFAULT_SUMMARY_SYSTEM_PROMPT
    )

    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": ("Расшифровка урока:\n\n" + text[:24000]),
                },
            ],
        }
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"LLM HTTP {exc.code}: {err}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM failed: {exc}") from exc

    choices = data.get("choices") or []
    content = ""
    if choices:
        content = (
            (choices[0].get("message") or {}).get("content") or ""
        ).strip()
    if not content:
        raise RuntimeError("Пустой конспект от модели.")
    return content


def process_summary_record(summary_id: int) -> None:
    """Синхронная обработка одной записи (вызывается из Celery)."""
    import tempfile

    from communication.models import ConferenceLessonSummary

    try:
        summary = ConferenceLessonSummary.objects.select_related(
            "conference"
        ).get(pk=summary_id)
    except ConferenceLessonSummary.DoesNotExist:
        logger.warning("LessonSummary %s not found", summary_id)
        return

    summary.status = ConferenceLessonSummary.Status.PENDING
    summary.error_message = ""
    summary.save(update_fields=["status", "error_message", "updated_at"])

    tmp_path: Path | None = None
    try:
        if not summary.audio:
            raise RuntimeError("Нет аудиофайла.")
        suffix = Path(summary.audio.name).suffix or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            with summary.audio.open("rb") as src:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    tmp.write(chunk)
        transcript = transcribe_audio_file(tmp_path)
        summary.transcript = transcript
        summary.summary_md = summarize_transcript(transcript)
        summary.status = ConferenceLessonSummary.Status.READY
        summary.error_message = ""
        summary.save(
            update_fields=[
                "transcript",
                "summary_md",
                "status",
                "error_message",
                "updated_at",
            ]
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lesson summary %s failed", summary_id)
        summary.status = ConferenceLessonSummary.Status.FAILED
        summary.error_message = str(exc)[:500]
        summary.save(update_fields=["status", "error_message", "updated_at"])
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
