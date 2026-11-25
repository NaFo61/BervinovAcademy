"""Рисунок общей доски школы. Не зависит от tldraw."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from django.db import transaction

from .models import UserBoard

KIND = "academy-board"
VERSION = 1
MAX_ITEMS = 800
MAX_POINTS = 2500
MAX_SNAPSHOT_CHARS = 4 * 1024 * 1024

_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,40}$")
_COLORS = {
    "#0B1226": "#0B1226",
    "#2563EB": "#2563EB",
    "#E11D48": "#E11D48",
    "#059669": "#059669",
}


class BoardDocumentError(ValueError):
    """Снимок или штрих нельзя сохранить."""


def empty_document() -> dict[str, Any]:
    return {
        "kind": KIND,
        "version": VERSION,
        "revision": 0,
        "items": [],
    }


def academy_board_from_snapshot(snapshot: Any) -> dict[str, Any]:
    """Достать рисунок школы из снимка. Чужой формат — пустая доска."""
    if not isinstance(snapshot, dict):
        return empty_document()
    if snapshot.get("kind") == KIND:
        return _coerce_document(snapshot)
    nested = snapshot.get("academy_board")
    if isinstance(nested, dict) and nested.get("kind") == KIND:
        return _coerce_document(nested)
    return empty_document()


def load_document(owner) -> dict[str, Any]:
    board = UserBoard.objects.filter(owner=owner).first()
    if board is None:
        return empty_document()
    return academy_board_from_snapshot(board.snapshot_json)


def commit_item(owner, actor, item: dict) -> tuple[dict, dict]:
    """Добавить или заменить фигуру. Возвращает (документ, фигура)."""
    clean = validate_item(item)
    with transaction.atomic():
        board = _locked_board(owner, actor)
        prev = _dict(board.snapshot_json)
        doc = academy_board_from_snapshot(prev)
        items = _upsert(list(doc["items"]), clean)
        _ensure_item_count(items)
        doc = _with_items(doc, items, bump=True)
        board.snapshot_json = _pack(prev, doc)
        _ensure_size(board.snapshot_json)
        board.updated_by = actor
        board.save(update_fields=["snapshot_json", "updated_by", "updated_at"])
    return doc, clean


def remove_items(owner, actor, ids: list) -> dict:
    """Убрать фигуры по id. Чужие id пропускаются."""
    drop = _clean_ids(ids)
    with transaction.atomic():
        board = _locked_board(owner, actor)
        prev = _dict(board.snapshot_json)
        doc = academy_board_from_snapshot(prev)
        items = [it for it in doc["items"] if it.get("id") not in drop]
        if len(items) == len(doc["items"]):
            return doc
        doc = _with_items(doc, items, bump=True)
        board.snapshot_json = _pack(prev, doc)
        _ensure_size(board.snapshot_json)
        board.updated_by = actor
        board.save(update_fields=["snapshot_json", "updated_by", "updated_at"])
    return doc


def save_snapshot_put(owner, actor, raw: dict, base_revision=None):
    """Сохранить PUT снимка. Формат tldraw не затирает рисунок школы."""
    if not isinstance(raw, dict):
        raise BoardDocumentError("Нужен объект snapshot.")
    with transaction.atomic():
        board = _locked_board(owner, actor)
        prev = _dict(board.snapshot_json)
        if raw.get("kind") == KIND:
            stored = _merge_academy_put(prev, raw, base_revision)
        else:
            stored = _preserve_academy(prev, raw)
        _ensure_size(stored)
        board.snapshot_json = stored
        board.updated_by = actor
        board.save(update_fields=["snapshot_json", "updated_by", "updated_at"])
    return board


def validate_item(raw: Any) -> dict:
    if not isinstance(raw, dict):
        raise BoardDocumentError("Неверная фигура.")
    item_id = raw.get("id")
    if not isinstance(item_id, str) or not _ITEM_ID_RE.fullmatch(item_id):
        raise BoardDocumentError("Неверный id фигуры.")
    kind = raw.get("type")
    if kind == "stroke":
        return {
            "id": item_id,
            "type": "stroke",
            "color": _color(raw.get("color")),
            "size": _num(raw.get("size"), 2, 24, "Неверная толщина."),
            "points": _points(raw.get("points")),
        }
    if kind == "image":
        return {
            "id": item_id,
            "type": "image",
            "src": _src(raw.get("src")),
            "x": _num(raw.get("x"), -200, 8000, "Неверное место картинки."),
            "y": _num(raw.get("y"), -200, 8000, "Неверное место картинки."),
            "w": _num(raw.get("w"), 8, 2000, "Неверный размер картинки."),
            "h": _num(raw.get("h"), 8, 2000, "Неверный размер картинки."),
        }
    raise BoardDocumentError("Неизвестный тип фигуры.")


def _merge_academy_put(prev: dict, raw: dict, base_revision) -> dict:
    current = academy_board_from_snapshot(prev)
    incoming = _coerce_document(raw, strict=True)
    cur_rev = int(current["revision"])
    base = cur_rev if base_revision is None else _as_revision(base_revision)
    if base < cur_rev:
        incoming["items"] = _union(current["items"], incoming["items"])
        incoming["revision"] = cur_rev
    elif _same_items(current["items"], incoming["items"]):
        incoming["revision"] = cur_rev
    else:
        incoming["revision"] = cur_rev + 1
    return _pack(prev, incoming)


def _preserve_academy(prev: dict, incoming: dict) -> dict:
    stored = dict(incoming)
    academy = academy_board_from_snapshot(prev)
    if academy["items"] or int(academy["revision"]) > 0:
        stored["academy_board"] = {
            "kind": KIND,
            "version": VERSION,
            "revision": academy["revision"],
            "items": academy["items"],
        }
    return stored


def _pack(prev: dict, doc: dict) -> dict:
    document = prev.get("document") if isinstance(prev, dict) else None
    body = {
        "kind": KIND,
        "version": VERSION,
        "revision": int(doc["revision"]),
        "items": list(doc["items"]),
    }
    if not isinstance(document, dict):
        return body
    packed = {"document": document, "academy_board": body}
    if "session" in prev:
        packed["session"] = prev["session"]
    return packed


def _coerce_document(raw: dict, strict: bool = False) -> dict[str, Any]:
    items = raw.get("items")
    if not isinstance(items, list):
        if strict:
            raise BoardDocumentError("В снимке нет списка фигур.")
        items = []
    clean: list[dict] = []
    for item in items[:MAX_ITEMS]:
        try:
            clean.append(validate_item(item))
        except BoardDocumentError:
            if strict:
                raise
    revision = raw.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        revision = 0
    if revision < 0:
        revision = 0
    return {
        "kind": KIND,
        "version": VERSION,
        "revision": revision,
        "items": clean,
    }


def _with_items(doc: dict, items: list, bump: bool) -> dict:
    revision = int(doc["revision"])
    if bump:
        revision += 1
    return {
        "kind": KIND,
        "version": VERSION,
        "revision": revision,
        "items": items,
    }


def _upsert(items: list, item: dict) -> list:
    for index, old in enumerate(items):
        if old.get("id") == item["id"]:
            items[index] = item
            return items
    items.append(item)
    return items


def _union(current: list, incoming: list) -> list:
    merged = list(current)
    for item in incoming:
        merged = _upsert(merged, item)
    _ensure_item_count(merged)
    return merged


def _same_items(left: list, right: list) -> bool:
    return json.dumps(left, sort_keys=True) == json.dumps(
        right, sort_keys=True
    )


def _ensure_item_count(items: list) -> None:
    if len(items) > MAX_ITEMS:
        raise BoardDocumentError("На доске слишком много рисунков.")


def _ensure_size(stored: dict) -> None:
    encoded = json.dumps(stored, separators=(",", ":"), ensure_ascii=False)
    if len(encoded) > MAX_SNAPSHOT_CHARS:
        raise BoardDocumentError("Снимок доски слишком большой.")


def _locked_board(owner, actor) -> UserBoard:
    UserBoard.objects.get_or_create(
        owner=owner,
        defaults={"updated_by": actor},
    )
    return UserBoard.objects.select_for_update().get(owner=owner)


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _clean_ids(ids: list) -> set[str]:
    if not isinstance(ids, list):
        raise BoardDocumentError("Нужен список id.")
    clean = set()
    for item_id in ids[:MAX_ITEMS]:
        if isinstance(item_id, str) and _ITEM_ID_RE.fullmatch(item_id):
            clean.add(item_id)
    return clean


def _as_revision(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BoardDocumentError("Неверная версия доски.")
    if value < 0:
        raise BoardDocumentError("Неверная версия доски.")
    return value


def _color(value: Any) -> str:
    if not isinstance(value, str):
        raise BoardDocumentError("Неверный цвет.")
    upper = value.strip().upper()
    for key, canonical in _COLORS.items():
        if key.upper() == upper:
            return canonical
    raise BoardDocumentError("Неверный цвет.")


def _num(value: Any, low: float, high: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BoardDocumentError(label)
    number = float(value)
    if not math.isfinite(number) or number < low or number > high:
        raise BoardDocumentError(label)
    return round(number, 1)


def _points(value: Any) -> list:
    if not isinstance(value, list) or not value or len(value) > MAX_POINTS:
        raise BoardDocumentError("Неверная линия.")
    points = []
    for pair in value:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise BoardDocumentError("Неверная линия.")
        points.append(
            [
                _num(pair[0], -200, 8000, "Неверная линия."),
                _num(pair[1], -200, 8000, "Неверная линия."),
            ]
        )
    return points


def _src(value: Any) -> str:
    if not isinstance(value, str):
        raise BoardDocumentError("Неверная картинка.")
    src = value.strip()
    if not src or len(src) > 2000:
        raise BoardDocumentError("Неверная картинка.")
    if src.startswith("/") and not src.startswith("//"):
        return src
    lowered = src.lower()
    if lowered.startswith("https://") or lowered.startswith("http://"):
        return src
    raise BoardDocumentError("Неверная картинка.")
