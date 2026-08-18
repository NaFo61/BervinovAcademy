"""Блоки теории: текст / картинка / заголовок / важно."""

from __future__ import annotations

import json
from typing import Any
import uuid

from common.html_sanitize import sanitize_html
from django.utils.html import escape
from rest_framework.exceptions import ValidationError as DrfValidationError

from content.attachments import is_image_attachment, serialize_attachment
from content.models import LessonAttachment, LessonTheory

BLOCK_TYPES = frozenset({"heading", "text", "image", "callout"})
HEADING_MAX_LEN = 300
CAPTION_MAX_LEN = 500


def _as_uuid(value) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_raw(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DrfValidationError(
                {"blocks": "Некорректный JSON блоков."}
            ) from exc
    if not isinstance(value, list):
        raise DrfValidationError({"blocks": "Ожидается список блоков."})
    return value


def normalize_blocks(value: Any, *, theory: LessonTheory) -> list[dict]:
    raw = _parse_raw(value)
    owned = {
        att.public_id: att
        for att in LessonAttachment.objects.filter(theory=theory)
    }
    result: list[dict] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise DrfValidationError(
                {"blocks": f"Блок {index}: ожидается объект."}
            )
        block_type = str(item.get("type") or "").strip()
        if block_type not in BLOCK_TYPES:
            raise DrfValidationError(
                {
                    "blocks": (
                        f"Блок {index}: неизвестный тип «{block_type}». "
                        "Можно: heading, text, image, callout."
                    )
                }
            )
        block_id = _as_uuid(item.get("id")) or uuid.uuid4()
        if block_type == "heading":
            text = str(item.get("text") or "").strip()[:HEADING_MAX_LEN]
            result.append(
                {"id": str(block_id), "type": "heading", "text": text}
            )
            continue
        if block_type in ("text", "callout"):
            html = sanitize_html(str(item.get("html") or ""))
            result.append(
                {"id": str(block_id), "type": block_type, "html": html}
            )
            continue
        attachment_id = _as_uuid(item.get("attachment_id"))
        if attachment_id is None:
            raise DrfValidationError(
                {"blocks": f"Блок {index}: у картинки нет файла."}
            )
        attachment = owned.get(attachment_id)
        if attachment is None:
            raise DrfValidationError(
                {"blocks": (f"Блок {index}: картинка не из этого урока.")}
            )
        if not is_image_attachment(attachment):
            raise DrfValidationError(
                {
                    "blocks": (
                        f"Блок {index}: этот файл не картинка. "
                        "Нужны png, jpg, gif, webp или svg."
                    )
                }
            )
        caption = str(item.get("caption") or "").strip()[:CAPTION_MAX_LEN]
        result.append(
            {
                "id": str(block_id),
                "type": "image",
                "attachment_id": str(attachment_id),
                "caption": caption,
            }
        )
    return result


def flatten_blocks(blocks: list[dict] | None) -> str:
    parts: list[str] = []
    for item in blocks or []:
        block_type = item.get("type")
        if block_type == "heading":
            text = escape(str(item.get("text") or "").strip())
            if text:
                parts.append(f"<h2>{text}</h2>")
            continue
        if block_type == "text":
            html = item.get("html") or ""
            if html:
                parts.append(str(html))
            continue
        if block_type == "callout":
            html = item.get("html") or ""
            parts.append(f'<div class="theory-callout">{html}</div>')
            continue
        if block_type == "image":
            caption = escape(str(item.get("caption") or "").strip())
            if caption:
                parts.append(f"<p><em>{caption}</em></p>")
    return sanitize_html("".join(parts))


def serialize_blocks_for_api(theory: LessonTheory, request=None) -> list[dict]:
    blocks = list(theory.blocks or [])
    if not blocks:
        return []
    by_id = {str(att.public_id): att for att in theory.attachments.all()}
    out: list[dict] = []
    for item in blocks:
        row = dict(item)
        if row.get("type") == "image":
            att = by_id.get(str(row.get("attachment_id") or ""))
            if att is None:
                continue
            payload = serialize_attachment(att, request)
            row["url"] = payload.get("url") or ""
            row["name"] = payload.get("name") or ""
            row["content_type"] = payload.get("content_type") or ""
        out.append(row)
    return out


def prune_image_blocks(theory: LessonTheory, attachment_public_id) -> None:
    target = str(attachment_public_id)
    blocks = list(theory.blocks or [])
    kept = [
        item
        for item in blocks
        if not (
            item.get("type") == "image"
            and str(item.get("attachment_id") or "") == target
        )
    ]
    if kept == blocks:
        return
    theory.blocks = kept
    theory.content = flatten_blocks(kept)
    theory.save(update_fields=["blocks", "content"])
