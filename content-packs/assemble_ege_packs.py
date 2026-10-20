#!/usr/bin/env python3
"""Собрать ZIP-пакеты импорта для ЕГЭ №1–№27.

Текст теории берётся из theory.html и кладётся в questions.json.
В ZIP theory.html не входит: сайт читает questions.json.
Готовые архивы по порядку: content-packs/к-импорту/.
Если в папке пакета уже есть questions.json и картинки, они важнее
копии с рабочего стола.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from pack_lessons import N11_PRACTICE, N7_PRACTICE  # noqa: E402

DESKTOP = Path.home() / "OneDrive" / "Desktop" / "BervinovVideos"
DESKTOP_PACKS = DESKTOP / "import-packs"
READY = ROOT / "к-импорту"

PACKS = (
    {
        "name": "ege-n1",
        "topic": "ЕГЭ информатика, задание 1 — графы",
        "theory_title": "Задание 1 ЕГЭ: графы",
        "theory_comment": "Сначала прочитайте теорию, затем решите вопросы — как в «Итог версия».",
        "theory_images": [
            "01-intro-graph.png",
            "08-task1-graph.png",
            "09-task2-graph.png",
            "10-task3-graph.png",
        ],
        "question_images": {
            "Игрушка: кто такой пункт 4": ["01-intro-graph.png"],
            "Ответ примера 1": ["02-ex1-graph.png"],
            "Ответ примера 2": ["03-ex2-graph.png"],
            "Ответ примера 3": ["04-ex3-graph.png"],
            "Ответ примера 4": ["05-ex4-graph.png"],
            "Ответ примера 5": ["06-ex5-graph.png"],
            "Ответ примера 6": ["07-ex6-graph.png"],
        },
        "desktop_src": DESKTOP / "Number1",
        "copy_images": [
            "01-intro-graph.png",
            "02-ex1-graph.png",
            "03-ex2-graph.png",
            "04-ex3-graph.png",
            "05-ex4-graph.png",
            "06-ex5-graph.png",
            "07-ex6-graph.png",
            "08-task1-graph.png",
            "09-task2-graph.png",
            "10-task3-graph.png",
        ],
        "fallback_practice": None,
    },
    {
        "name": "ege-n4",
        "topic": "ЕГЭ информатика, задание 4 — условие Фано",
        "theory_title": "Задание 4 ЕГЭ: дерево Фано",
        "theory_comment": "Держите дерево перед глазами: влево 0, вправо 1, буква только в листе.",
        "theory_images": [
            "01-task1-step1-G.png",
            "06-task1-step6-free.png",
            "07-task1-step7-result.png",
            "08-task2-tree.png",
            "09-task3-tree.png",
            "10-task4-tree.png",
        ],
        "question_images": {
            "Код буквы Г в задаче 1": ["01-task1-step1-G.png"],
            "Ответ задачи 1": ["07-task1-step7-result.png"],
            "Ответ задачи 2": ["08-task2-tree.png"],
            "Код буквы С в задаче 4": ["10-task4-tree.png"],
        },
        "desktop_src": DESKTOP / "Number4",
        "copy_images": [
            "01-task1-step1-G.png",
            "02-task1-step2-D.png",
            "03-task1-step3-E.png",
            "04-task1-step4-Zh.png",
            "05-task1-step5-Z.png",
            "06-task1-step6-free.png",
            "07-task1-step7-result.png",
            "08-task2-tree.png",
            "09-task3-tree.png",
            "10-task4-tree.png",
        ],
        "fallback_practice": None,
    },
    {
        "name": "ege-n7",
        "topic": "ЕГЭ информатика, задание 7 — картинки и звук",
        "theory_title": "Задание 7 ЕГЭ: кодирование картинок и звука",
        "theory_comment": "Главная ловушка — биты и байты. 1 Кбайт = 1024 байт.",
        "theory_images": [
            "pixel-grid.png",
            "palette.png",
            "bit-depth.png",
            "file-size.png",
            "sound-formula.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": N7_PRACTICE,
    },
    {
        "name": "ege-n11",
        "topic": "ЕГЭ информатика, задание 11 — пароли и память",
        "theory_title": "Задание 11 ЕГЭ: кодирование паролей",
        "theory_comment": "Сначала биты на символ, потом на пароль, потом округление до байт.",
        "theory_images": [
            "alphabet-bits.png",
            "password-layout.png",
            "round-up-bytes.png",
            "users-total.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": N11_PRACTICE,
    },
    {
        "name": "ege-n2",
        "topic": "ЕГЭ информатика, задание 2 — логика",
        "theory_title": "Задание 2 ЕГЭ: логика",
        "theory_comment": "И, ИЛИ, НЕ и стрелка. Сначала таблица, потом считаем единицы.",
        "theory_images": [
            "01-logic-ops.png",
            "02-truth-and.png",
            "03-impl.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n3",
        "topic": "ЕГЭ информатика, задание 3 — базы данных",
        "theory_title": "Задание 3 ЕГЭ: базы данных",
        "theory_comment": "Две таблицы связаны номером ученика. Считаем людей или строки.",
        "theory_images": [
            "01-students.png",
            "02-grades.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n5",
        "topic": "ЕГЭ информатика, задание 5 — простой алгоритм",
        "theory_title": "Задание 5 ЕГЭ: простой алгоритм",
        "theory_comment": "Двоичная запись, прибавить единицы или дописать цифру справа.",
        "theory_images": [
            "01-binary-18.png",
            "02-append-6.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n6",
        "topic": "ЕГЭ информатика, задание 6 — черепаха",
        "theory_title": "Задание 6 ЕГЭ: черепаха",
        "theory_comment": "Целые точки внутри фигуры и на границе считают отдельно.",
        "theory_images": [
            "01-square-5.png",
            "02-rect.png",
            "03-square-6.png",
        ],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n8",
        "topic": "ЕГЭ информатика, задание 8 — перебор слов",
        "theory_title": "Задание 8 ЕГЭ: перебор слов",
        "theory_comment": "Слова в алфавитном порядке. Номер считают как число в системе счисления.",
        "theory_images": ["01-word-list.png", "02-tok.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n9",
        "topic": "ЕГЭ информатика, задание 9 — электронные таблицы",
        "theory_title": "Задание 9 ЕГЭ: электронные таблицы",
        "theory_comment": "Файл .ods. СЧЁТЕСЛИ ищет тройку, потом сравнивают среднее.",
        "theory_images": ["01-sheet.png", "02-counts.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n10",
        "topic": "ЕГЭ информатика, задание 10 — поиск в тексте",
        "theory_title": "Задание 10 ЕГЭ: поиск в тексте",
        "theory_comment": "Файл .odt. Сочетание внутри слова и отдельное слово считают по-разному.",
        "theory_images": ["01-text.png", "02-find.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n12",
        "topic": "ЕГЭ информатика, задание 12 — лента",
        "theory_title": "Задание 12 ЕГЭ: лента",
        "theory_comment": "Головка читает клетку: записать, сдвинуться, сменить состояние.",
        "theory_images": ["01-commands.png", "02-trace.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n13",
        "topic": "ЕГЭ информатика, задание 13 — IP-адреса",
        "theory_title": "Задание 13 ЕГЭ: IP-адреса",
        "theory_comment": "Маска делит адрес на сеть и номер компьютера.",
        "theory_images": ["01-mask.png", "02-hosts.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n14",
        "topic": "ЕГЭ информатика, задание 14 — системы счисления",
        "theory_title": "Задание 14 ЕГЭ: системы счисления",
        "theory_comment": "Цифры по степеням основания, неизвестная цифра, число нулей.",
        "theory_images": ["01-base9.png", "02-digit.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
    {
        "name": "ege-n15",
        "topic": "ЕГЭ информатика, задание 15 — отрезки",
        "theory_title": "Задание 15 ЕГЭ: отрезки",
        "theory_comment": "Отрезок A должен закрыть все x, где выражение иначе ложно.",
        "theory_images": ["01-line.png", "02-cover.png"],
        "question_images": {},
        "desktop_src": None,
        "copy_images": [],
        "fallback_practice": None,
    },
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _theory_html(spec: dict) -> str:
    text = (ROOT / spec["name"] / "theory.html").read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
        match = re.search(r"<body[^>]*>(.*)</body>", text, re.S | re.I)
        if not match:
            raise ValueError(f"{spec['name']}: в theory.html нет body")
        return match.group(1).strip()
    return text.strip()


def _theory_lesson(spec: dict) -> dict:
    html = _theory_html(spec)
    lesson = {
        "type": "theory",
        "title": spec["theory_title"],
        "content": html.strip(),
        "comment": spec["theory_comment"],
    }
    if spec["theory_images"]:
        lesson["images"] = list(spec["theory_images"])
    return lesson


def _load_practice(spec: dict) -> list[dict]:
    repo_q = ROOT / spec["name"] / "questions.json"
    # №7 и №11 раньше брались из pack_lessons.py и затирали правки.
    # Если в паке уже лежит свой questions.json с вопросами — он и есть источник.
    if spec["fallback_practice"] is not None and repo_q.is_file():
        raw = _read_json(repo_q)
        lessons = raw.get("lessons") if isinstance(raw, dict) else raw
        practice = [item for item in lessons if item.get("type") != "theory"]
        if practice:
            return practice
    if spec["fallback_practice"] is not None:
        return json.loads(json.dumps(spec["fallback_practice"]))
    desktop_q = spec["desktop_src"] / "questions.json" if spec["desktop_src"] else None
    repo_q = ROOT / spec["name"] / "questions.json"
    src = None
    if repo_q.is_file():
        src = repo_q
    elif desktop_q and desktop_q.is_file():
        src = desktop_q
    if src is None:
        raise FileNotFoundError(
            f"Нет questions.json для {spec['name']}"
        )
    raw = _read_json(src)
    lessons = raw.get("lessons") if isinstance(raw, dict) else raw
    practice = [item for item in lessons if item.get("type") != "theory"]
    mapping = spec["question_images"]
    for item in practice:
        names = mapping.get(item.get("title"))
        if names:
            item["images"] = list(names)
    if spec["name"] == "ege-n1" and not any(
        x.get("title") == "Ответ примера 6" for x in practice
    ):
        practice.append(
            {
                "type": "short_answer",
                "title": "Ответ примера 6",
                "question_text": (
                    "В примере 6 теории сумма длин E–G и B–D. "
                    "Какой ответ? Только число."
                ),
                "correct_answer": "90",
                "answer_normalize": "strip_casefold",
                "solution_text": (
                    "<p><strong>Подробный разбор.</strong> "
                    "Спросили сумму длин дорог E–G и B–D.</p>"
                    "<ol><li>Одной особой точки нет: двойки A, C, F "
                    "и тройки B, D, E, G.</li>"
                    "<li>У A оба соседа — тройки, и у каждой из них "
                    "рядом две двойки. В таблице так только пункт 2.</li>"
                    "<li>Схема как зеркало. Дороги 43 и 47, "
                    "сумма <strong>90</strong>.</li></ol>"
                ),
                "points": 3,
                "images": ["07-ex6-graph.png"],
            }
        )
    if spec["name"] == "ege-n4" and not any(
        x.get("title") == "Ответ задачи 3" for x in practice
    ):
        practice.append(
            {
                "type": "short_answer",
                "title": "Ответ задачи 3",
                "question_text": (
                    "В задаче 3 теории нужна суммарная длина кодов "
                    "всех восьми букв слова «БЛОКЧЕЙН». Какое число? "
                    "Только цифры."
                ),
                "correct_answer": "27",
                "answer_normalize": "strip_casefold",
                "explanation": (
                    "Известные 2+4+3+5 и новые 2+3+4+4 дают 27."
                ),
                "points": 3,
                "images": ["09-task3-tree.png"],
            }
        )
    return practice


def _copy_desktop_images(spec: dict) -> None:
    names = spec["copy_images"]
    if not names:
        return
    src_dir = spec["desktop_src"] / "images"
    dest = ROOT / spec["name"] / "images"
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in names:
        src = src_dir / name
        target = dest / name
        if target.is_file():
            continue
        if not src.is_file():
            missing.append(name)
            continue
        shutil.copy2(src, target)
    if missing:
        print("Нет картинок (пропуск):", spec["name"], ", ".join(missing))


def _svg(path: Path, body: str, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">\n'
            f"{body}\n</svg>\n"
        ),
        encoding="utf-8",
    )


def _write_n7_images() -> None:
    folder = ROOT / "ege-n7" / "images"
    _svg(
        folder / "pixel-grid.svg",
        """
  <rect width="420" height="160" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Пиксельная сетка 8×4</text>
  <g transform="translate(16,44)">
    <rect x="0" y="0" width="384" height="96" fill="#f4f4f4" stroke="#333"/>
  </g>
  <g transform="translate(16,44)" stroke="#333">
    <rect x="0" y="0" width="48" height="24" fill="#ef4444"/>
    <rect x="48" y="0" width="48" height="24" fill="#22c55e"/>
    <rect x="96" y="0" width="48" height="24" fill="#3b82f6"/>
    <rect x="144" y="0" width="48" height="24" fill="#f59e0b"/>
    <rect x="192" y="0" width="48" height="24" fill="#a855f7"/>
    <rect x="240" y="0" width="48" height="24" fill="#06b6d4"/>
    <rect x="288" y="0" width="48" height="24" fill="#ec4899"/>
    <rect x="336" y="0" width="48" height="24" fill="#84cc16"/>
    <rect x="0" y="24" width="48" height="24" fill="#f97316"/>
    <rect x="48" y="24" width="48" height="24" fill="#14b8a6"/>
    <rect x="96" y="24" width="48" height="24" fill="#6366f1"/>
    <rect x="144" y="24" width="48" height="24" fill="#eab308"/>
    <rect x="192" y="24" width="48" height="24" fill="#ef4444"/>
    <rect x="240" y="24" width="48" height="24" fill="#22c55e"/>
    <rect x="288" y="24" width="48" height="24" fill="#3b82f6"/>
    <rect x="336" y="24" width="48" height="24" fill="#f59e0b"/>
    <rect x="0" y="48" width="48" height="24" fill="#a855f7"/>
    <rect x="48" y="48" width="48" height="24" fill="#06b6d4"/>
    <rect x="96" y="48" width="48" height="24" fill="#ec4899"/>
    <rect x="144" y="48" width="48" height="24" fill="#84cc16"/>
    <rect x="192" y="48" width="48" height="24" fill="#f97316"/>
    <rect x="240" y="48" width="48" height="24" fill="#14b8a6"/>
    <rect x="288" y="48" width="48" height="24" fill="#6366f1"/>
    <rect x="336" y="48" width="48" height="24" fill="#eab308"/>
    <rect x="0" y="72" width="48" height="24" fill="#64748b"/>
    <rect x="48" y="72" width="48" height="24" fill="#ef4444"/>
    <rect x="96" y="72" width="48" height="24" fill="#22c55e"/>
    <rect x="144" y="72" width="48" height="24" fill="#3b82f6"/>
    <rect x="192" y="72" width="48" height="24" fill="#f59e0b"/>
    <rect x="240" y="72" width="48" height="24" fill="#a855f7"/>
    <rect x="288" y="72" width="48" height="24" fill="#06b6d4"/>
    <rect x="336" y="72" width="48" height="24" fill="#1a1a1a"/>
  </g>
""",
        420,
        160,
    )
    _svg(
        folder / "palette.svg",
        """
  <rect width="420" height="140" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Палитра: K цветов → i бит, 2^i ≥ K</text>
  <text x="16" y="56" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">40 цветов: 2^5 = 32 мало, 2^6 = 64 хватает → i = 6</text>
  <rect x="16" y="72" width="28" height="28" fill="#ef4444" stroke="#333"/>
  <rect x="48" y="72" width="28" height="28" fill="#22c55e" stroke="#333"/>
  <rect x="80" y="72" width="28" height="28" fill="#3b82f6" stroke="#333"/>
  <rect x="112" y="72" width="28" height="28" fill="#f59e0b" stroke="#333"/>
  <text x="152" y="92" font-family="Times New Roman, serif" font-size="15" fill="#555">… всего K клеток</text>
""",
        420,
        140,
    )
    _svg(
        folder / "bit-depth.svg",
        """
  <rect width="420" height="130" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Глубина i — бит на один пиксель</text>
  <text x="16" y="58" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">1 бит → 2 цвета · 8 бит → 256 · 24 бита → 3 байта</text>
  <text x="16" y="88" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">N = 2^i    не путать: 24 бита ≠ 24 байта</text>
""",
        420,
        130,
    )
    _svg(
        folder / "file-size.svg",
        """
  <rect width="460" height="140" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Размер картинки без сжатия</text>
  <text x="16" y="58" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">V = ширина × высота × i бит</text>
  <text x="16" y="86" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">байты = V / 8     Кбайт = байты / 1024</text>
  <text x="16" y="114" font-family="Times New Roman, serif" font-size="15" fill="#2f6fbd">640×480, 4 бита → 150 Кбайт</text>
""",
        460,
        140,
    )
    _svg(
        folder / "sound-formula.svg",
        """
  <rect width="480" height="140" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Звук</text>
  <text x="16" y="58" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">V = частота × время × глубина × каналы  (бит)</text>
  <text x="16" y="86" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">моно = 1 канал, стерео = 2</text>
  <text x="16" y="114" font-family="Times New Roman, serif" font-size="15" fill="#2f6fbd">8000 Гц · 8 с · 16 бит · моно → 125 Кбайт</text>
""",
        480,
        140,
    )


def _write_n11_images() -> None:
    folder = ROOT / "ege-n11" / "images"
    _svg(
        folder / "alphabet-bits.svg",
        """
  <rect width="460" height="150" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Биты на один символ: 2^i ≥ K</text>
  <text x="16" y="60" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">10 цифр → 4 бита     26 букв → 5 бит</text>
  <text x="16" y="90" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">36 знаков (цифры+буквы) → 6 бит</text>
  <text x="16" y="122" font-family="Times New Roman, serif" font-size="15" fill="#b91c1c">Нельзя: «26 бит на букву»</text>
""",
        460,
        150,
    )
    _svg(
        folder / "password-layout.svg",
        """
  <rect width="500" height="150" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Пароль из L символов + запас</text>
  <rect x="16" y="48" width="70" height="40" fill="#dbeafe" stroke="#1e40af"/>
  <rect x="86" y="48" width="70" height="40" fill="#dbeafe" stroke="#1e40af"/>
  <rect x="156" y="48" width="70" height="40" fill="#dbeafe" stroke="#1e40af"/>
  <text x="28" y="74" font-family="Times New Roman, serif" font-size="14">симв.</text>
  <text x="98" y="74" font-family="Times New Roman, serif" font-size="14">симв.</text>
  <text x="168" y="74" font-family="Times New Roman, serif" font-size="14">… L</text>
  <rect x="250" y="48" width="110" height="40" fill="#fef3c7" stroke="#b45309"/>
  <text x="262" y="74" font-family="Times New Roman, serif" font-size="14">+ контроль</text>
  <text x="16" y="122" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">биты = i × L + запас</text>
""",
        500,
        150,
    )
    _svg(
        folder / "round-up-bytes.svg",
        """
  <rect width="460" height="140" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Округление до целого числа байт</text>
  <text x="16" y="60" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">20 бит = 2 байта + 4 бита → нужно 3 байта</text>
  <text x="16" y="92" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">Округляют каждый пароль, потом × число людей</text>
""",
        460,
        140,
    )
    _svg(
        folder / "users-total.svg",
        """
  <rect width="460" height="140" fill="#ffffff"/>
  <text x="16" y="28" font-family="Times New Roman, serif" font-size="16" fill="#1a1a1a">Все пользователи</text>
  <text x="16" y="60" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">всего = (байты на пароль) × (число людей)</text>
  <text x="16" y="92" font-family="Times New Roman, serif" font-size="15" fill="#1a1a1a">Кбайт: делить на 1024</text>
  <text x="16" y="122" font-family="Times New Roman, serif" font-size="15" fill="#2f6fbd">200 × 3 байта = 600 байт</text>
""",
        460,
        140,
    )


def _zip_dir(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(src.rglob("*")):
            if not file.is_file():
                continue
            if file.name in ("theory.html", "preview.html"):
                continue
            rel = file.relative_to(src).as_posix()
            zf.write(file, rel)


def _validate_lessons(lessons: list[dict], pack_name: str) -> None:
    kinds = {"checkbox", "radio", "short_answer", "theory", "coding"}
    if not lessons:
        raise ValueError(f"{pack_name}: пустой список уроков")
    for index, item in enumerate(lessons, start=1):
        kind = item.get("type")
        title = (item.get("title") or "").strip()
        if kind not in kinds:
            raise ValueError(f"{pack_name} #{index}: type {kind}")
        if not title:
            raise ValueError(f"{pack_name} #{index}: пустой title")
        if kind == "theory" and not str(item.get("content") or "").strip():
            raise ValueError(f"{pack_name}: пустая теория")
        if kind in ("radio", "checkbox"):
            answers = item.get("answers") or []
            if not answers:
                raise ValueError(f"{pack_name}: нет answers у {title}")
            if kind == "radio" and sum(1 for row in answers if row[1]) != 1:
                raise ValueError(f"{pack_name}: radio {title}")
            if kind == "checkbox" and not any(row[1] for row in answers):
                raise ValueError(f"{pack_name}: checkbox {title}")
        if kind == "short_answer" and not str(
            item.get("correct_answer") or ""
        ).strip():
            raise ValueError(f"{pack_name}: short {title}")


def build_pack(spec: dict) -> Path:
    name = spec["name"]
    dest_dir = ROOT / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    _copy_desktop_images(spec)
    if name == "ege-n7" and not (dest_dir / "images" / "pixel-grid.png").is_file():
        _write_n7_images()
    if name == "ege-n11" and not (
        dest_dir / "images" / "alphabet-bits.png"
    ).is_file():
        _write_n11_images()

    lessons = [_theory_lesson(spec)] + _load_practice(spec)
    _validate_lessons(lessons, name)
    _write_json(
        dest_dir / "questions.json",
        {
            "meta": {
                "topic": spec["topic"],
                "images_dir": "images/",
                "scheme": {
                    "theory": 1,
                    "checkbox": sum(
                        1 for x in lessons if x["type"] == "checkbox"
                    ),
                    "radio": sum(1 for x in lessons if x["type"] == "radio"),
                    "short_answer": sum(
                        1 for x in lessons if x["type"] == "short_answer"
                    ),
                    "total": len(lessons),
                },
            },
            "lessons": lessons,
        },
    )
    zip_path = ROOT / f"{name}-import.zip"
    _zip_dir(dest_dir, zip_path)
    return zip_path


def _copy_to_desktop(zips: list[Path]) -> None:
    if not DESKTOP.parent.exists() and not DESKTOP.exists():
        return
    DESKTOP.mkdir(parents=True, exist_ok=True)
    DESKTOP_PACKS.mkdir(parents=True, exist_ok=True)
    readme_src = ROOT / "КАК-ИМПОРТИРОВАТЬ.md"
    if readme_src.is_file():
        shutil.copy2(readme_src, DESKTOP_PACKS / "КАК-ИМПОРТИРОВАТЬ.md")
        shutil.copy2(readme_src, DESKTOP / "КАК-ИМПОРТИРОВАТЬ.md")
    for zip_path in zips:
        shutil.copy2(zip_path, DESKTOP_PACKS / zip_path.name)
        shutil.copy2(zip_path, DESKTOP / zip_path.name)

    mapping = {
        "ege-n7": DESKTOP / "Number7",
        "ege-n11": DESKTOP / "Number11",
    }
    for name, folder in mapping.items():
        folder.mkdir(parents=True, exist_ok=True)
        src = ROOT / name
        shutil.copy2(src / "questions.json", folder / "questions.json")
        shutil.copy2(src / "manifest.json", folder / "manifest.json")
        images = src / "images"
        if images.is_dir():
            dest_img = folder / "images"
            dest_img.mkdir(parents=True, exist_ok=True)
            for img in images.iterdir():
                if img.is_file():
                    shutil.copy2(img, dest_img / img.name)

        theory = (src / "theory.html").read_text(encoding="utf-8")
        title = "Задание 7 ЕГЭ" if name == "ege-n7" else "Задание 11 ЕГЭ"
        (folder / "Итог версия.html").write_text(
            _standalone_html(title, theory),
            encoding="utf-8",
        )


def _standalone_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{
    font-family: "Times New Roman", Times, serif;
    max-width: 820px;
    margin: 0 auto;
    padding: 32px 20px 80px;
    color: #1a1a1a;
    line-height: 1.55;
    background: #fff;
    font-style: italic;
  }}
  h1 {{ font-size: 24px; margin: 0 0 12px; font-style: normal; }}
  h2 {{ font-size: 19px; margin: 40px 0 12px; padding-top: 16px; border-top: 1px solid #ddd; }}
  h3 {{ font-size: 16px; margin: 18px 0 8px; }}
  p, li {{ font-size: 16px; }}
  table {{ border-collapse: collapse; margin: 14px 0; }}
  td, th {{ border: 1px solid #333; padding: 6px 14px; text-align: center; }}
  mark {{ background: #fef08a; }}
  code {{ font-style: normal; }}
</style>
</head>
<body>
<h1>{title}</h1>
{body}
</body>
</html>
"""


def _packs_16_27() -> list[dict]:
    """№16–№27 лежат в тех же папках. В архив их раньше не клали."""
    packs = []
    for number in range(16, 28):
        folder = ROOT / f"ege-n{number}"
        questions = _read_json(folder / "questions.json")
        theory = next(
            item for item in questions["lessons"] if item.get("type") == "theory"
        )
        manifest = _read_json(folder / "manifest.json")
        packs.append(
            {
                "name": f"ege-n{number}",
                "topic": questions["meta"]["topic"],
                "theory_title": theory["title"],
                "theory_comment": theory.get("comment")
                or manifest.get("module_description", ""),
                "theory_images": list(theory.get("images") or []),
                "question_images": {},
                "desktop_src": None,
                "copy_images": [],
                "fallback_practice": None,
            }
        )
    return packs


def _ready_zip_name(zip_path: Path) -> str:
    number = int(zip_path.name.removeprefix("ege-n").split("-", 1)[0])
    return f"{number:02d}-{zip_path.name}"


def export_ready_copies(zips: list[Path]) -> list[Path]:
    """Копии с номерами 01…27 в папку, которую открывает владелец."""
    READY.mkdir(parents=True, exist_ok=True)
    published = []
    for zip_path in zips:
        target = READY / _ready_zip_name(zip_path)
        shutil.copy2(zip_path, target)
        published.append(target)
    readme = ROOT / "КАК-ИМПОРТИРОВАТЬ.md"
    if readme.is_file():
        shutil.copy2(readme, READY / readme.name)
    return published


def zip_existing_packs() -> list[Path]:
    """Упаковать текущие папки. questions.json не переписывается."""
    built = []
    for number in range(1, 28):
        name = f"ege-n{number}"
        src = ROOT / name
        if not (src / "manifest.json").is_file():
            raise FileNotFoundError(src / "manifest.json")
        if not (src / "questions.json").is_file():
            raise FileNotFoundError(src / "questions.json")
        zip_path = ROOT / f"{name}-import.zip"
        _zip_dir(src, zip_path)
        built.append(zip_path)
    export_ready_copies(built)
    return built


def build_all() -> list[Path]:
    built = [build_pack(spec) for spec in list(PACKS) + _packs_16_27()]
    _copy_to_desktop(built)
    export_ready_copies(built)
    return built


if __name__ == "__main__":
    for path in build_all():
        print(path)
