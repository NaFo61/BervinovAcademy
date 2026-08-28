#!/usr/bin/env python3
"""Собрать ZIP-архивы для импорта content-pack из content-packs/."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "backend"))

from fixture.course_fixtures import _coding_search_pack, _graphs_pack  # noqa: E402

DESKTOP_OUT = Path.home() / "OneDrive" / "Desktop" / "BervinovVideos" / "import-packs"


def _write_questions(path: Path, *, topic: str, lessons: list) -> None:
    payload = {
        "meta": {"topic": topic, "images_dir": "images/"},
        "lessons": lessons,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _ensure_fixture_questions() -> None:
    _write_questions(
        ROOT / "ege-n1" / "questions.json",
        topic="ЕГЭ, задание 1 — графы",
        lessons=_graphs_pack(),
    )
    _write_questions(
        ROOT / "ege-n4" / "questions.json",
        topic="ЕГЭ, задание 4 — кодирование",
        lessons=_coding_search_pack(),
    )


def _zip_dir(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(src.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(src).as_posix())


def build_all() -> list[Path]:
    _ensure_fixture_questions()
    built: list[Path] = []
    for name in ("ege-n1", "ege-n4", "ege-n7"):
        src = ROOT / name
        zip_name = f"{name}-import.zip"
        out = ROOT / zip_name
        _zip_dir(src, out)
        built.append(out)
        if DESKTOP_OUT.parent.exists():
            DESKTOP_OUT.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, DESKTOP_OUT / zip_name)
    return built


if __name__ == "__main__":
    paths = build_all()
    for path in paths:
        print(path)
