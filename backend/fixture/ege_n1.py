"""Разборы задания 1 ЕГЭ (графы): текст из JSON, картинки — в S3 через редактор."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.files.base import ContentFile

from content.attachments import bind_parent
from content.container_lessons import iter_module_lessons
from content.models import LessonAttachment, LessonTheory, Module
from content.theory_blocks import flatten_blocks, normalize_blocks

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "ege-n1"
COURSE_SLUG = "ege-informatika"
GRAPHS_MODULE_TITLE = "1-й урок ЕГЭ: Графы"
INTRO_TITLE = "Таблица дорог и матрица смежности"
EGE_N1_FOLDERS = ("01", "02", "03", "04", "05", "06")
SVG_CONTENT_TYPE = "image/svg+xml"

# Ответы из academy-blocks.json — не выдумывать другие.
EGE_N1_ANSWERS = {
    "Простое: какие номера у B и F": "26",
    "Простое: какие номера у B и C": "56",
    "Среднее: сумма A–G и A–D": "26",
    "Среднее: сумма B–D и E–G": "42",
    "Сложнее: сумма E–F и C–D": "37",
    "Самое сложное: сумма E–G и B–D": "90",
}


def load_ege_n1_theory_lessons(*, video_url: str = "") -> list[dict]:
    rows: list[dict] = []
    for folder in EGE_N1_FOLDERS:
        src = ASSETS_DIR / folder
        payload = json.loads(
            (src / "academy-blocks.json").read_text(encoding="utf-8")
        )
        row = {
            "type": "theory",
            "title": payload["title"],
            "content": "",
            "blocks": payload["blocks"],
            "assets_dir": src,
        }
        if video_url:
            row["video_url"] = video_url
        rows.append(row)
    return rows


def apply_ege_n1_blocks(
    theory: LessonTheory, blocks: list, assets_dir: Path | str
) -> None:
    """Пишет blocks + content. Картинки из папки — только если файл есть."""
    assets_dir = Path(assets_dir)
    file_to_id: dict[str, str] = {}
    for block in blocks:
        if block.get("type") != "image":
            continue
        rel = str(block.get("file") or "")
        path = assets_dir / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        attachment = LessonAttachment(
            original_name=path.name[:255],
            content_type=SVG_CONTENT_TYPE,
            size=len(data),
        )
        bind_parent(attachment=attachment, kind="theory", lesson=theory)
        attachment.file.save(path.name, ContentFile(data), save=True)
        file_to_id[rel] = str(attachment.public_id)

    if not file_to_id and theory.blocks:
        return

    if file_to_id:
        keep = set(file_to_id.values())
        for att in list(theory.attachments.all()):
            if str(att.public_id) not in keep:
                att.delete()

    prepared: list[dict] = []
    for block in blocks:
        item = dict(block)
        if item.get("type") == "image":
            att_id = file_to_id.get(str(item.get("file") or ""))
            if not att_id:
                continue
            item["attachment_id"] = att_id
            item.pop("file", None)
        prepared.append(item)

    theory.blocks = normalize_blocks(prepared, theory=theory)
    theory.content = flatten_blocks(theory.blocks)
    theory.save(update_fields=["blocks", "content"])


def ensure_ege_n1_in_module(
    module: Module, *, video_url: str = ""
) -> list[LessonTheory]:
    """
    Создаёт или обновляет 6 уроков теории. Задания модуля не меняет.
    Ставит разборы сразу после вводной теории, если она есть.
    """
    packs = load_ege_n1_theory_lessons(video_url=video_url)
    lessons: list[LessonTheory] = []
    for pack in packs:
        theory = LessonTheory.objects.filter(
            module=module, title=pack["title"]
        ).first()
        if theory is None:
            theory = LessonTheory.objects.create(
                module=module,
                title=pack["title"],
                content="<p></p>",
                is_active=True,
                video_url=video_url,
            )
        else:
            theory.is_active = True
            theory.save(update_fields=["is_active"])
        apply_ege_n1_blocks(theory, pack["blocks"], pack["assets_dir"])
        lessons.append(theory)
    _reorder_graphs_module(module, lessons)
    return lessons


def _reorder_graphs_module(
    module: Module, n1_lessons: list[LessonTheory]
) -> None:
    n1_ids = {lesson.pk for lesson in n1_lessons}
    intro: list = []
    rest: list = []
    for _kind, obj in iter_module_lessons(module, active_only=False):
        if obj.pk in n1_ids and isinstance(obj, LessonTheory):
            continue
        if isinstance(obj, LessonTheory) and obj.title == INTRO_TITLE:
            intro.append(obj)
        else:
            rest.append(obj)

    ordered = intro + list(n1_lessons) + rest
    for index, obj in enumerate(ordered, start=1):
        if obj.order_index != index:
            obj.order_index = index
            obj.save(update_fields=["order_index"])
