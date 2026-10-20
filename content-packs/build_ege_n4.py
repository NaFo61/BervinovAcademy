# -*- coding: utf-8 -*-
"""Задание 4: условие Фано. Четыре урока, в каждом теория, вопросы и программа."""

from __future__ import annotations

import html
import itertools
import json
import zipfile
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK = ROOT / "ege-n4"
READY = ROOT / "к-импорту"


def esc(text) -> str:
    return html.escape(str(text), quote=False)


def code_block(src: str) -> str:
    return "<pre><code>" + esc(src.strip("\n")) + "</code></pre>"


def can_descend(node: str, known: tuple[str, ...]) -> bool:
    return not any(node.startswith(old) for old in known)


def can_place(node: str, known: tuple[str, ...]) -> bool:
    if not node:
        return False
    return not any(node.startswith(old) or old.startswith(node) for old in known)


def best_codes(known: list[str], need: int, limit: int = 7) -> list[str]:
    """Самый короткий набор из need новых кодов. Ни один не начало другого."""
    known_t = tuple(known)

    @lru_cache(maxsize=None)
    def dp(node: str, left: int):
        if left == 0:
            return (0, ())
        if len(node) > limit or not can_descend(node, known_t):
            return None
        best = None
        if left == 1 and can_place(node, known_t):
            best = (len(node), (node,))
        for take_left in range(left + 1):
            left_res = dp(node + "0", take_left)
            if left_res is None:
                continue
            right_res = dp(node + "1", left - take_left)
            if right_res is None:
                continue
            total = left_res[0] + right_res[0]
            codes = tuple(sorted(left_res[1] + right_res[1], key=lambda item: (len(item), item)))
            if best is None or total < best[0]:
                best = (total, codes)
        return best

    found = dp("", need)
    if found is None:
        raise SystemExit(f"нет набора кодов: {known} need={need}")
    return list(found[1])


def shortest_one(known: list[str], prefer: str = "max", limit: int = 8) -> str:
    options: list[str] = []
    for length in range(1, limit + 1):
        level = []
        for index in range(2**length):
            code = f"{index:0{length}b}"
            if can_place(code, tuple(known)):
                level.append(code)
        if level:
            options = level
            break
    if not options:
        raise SystemExit(f"нет свободного кода: {known}")
    key = lambda item: int(item, 2)
    return max(options, key=key) if prefer == "max" else min(options, key=key)


def shortest_reverse(known: list[str], prefer: str = "max", limit: int = 8) -> str:
    """Обратное Фано: ни один код не окончание другого."""
    rev_known = [item[::-1] for item in known]
    options: list[str] = []
    for length in range(1, limit + 1):
        level = []
        for index in range(2**length):
            rev = f"{index:0{length}b}"
            if can_place(rev, tuple(rev_known)):
                level.append(rev[::-1])
        if level:
            options = level
            break
    if not options:
        raise SystemExit(f"нет обратного кода: {known}")
    key = lambda item: int(item, 2)
    return max(options, key=key) if prefer == "max" else min(options, key=key)


def encode_length(word: str, known_map: dict[str, str], limit: int = 5) -> tuple[int, dict[str, str]]:
    freq = Counter(word)
    unknown = [letter for letter in freq if letter not in known_map]
    known_codes = list(known_map.values())
    if len(unknown) > 3:
        raise SystemExit("для слова слишком много новых букв")
    candidates = []
    for length in range(1, limit + 1):
        for index in range(2**length):
            code = f"{index:0{length}b}"
            if can_place(code, tuple(known_codes)):
                candidates.append(code)
    letters = sorted(unknown, key=lambda letter: (-freq[letter], letter))
    best_total = None
    best_assign: dict[str, str] = {}
    for group in itertools.combinations(candidates, len(unknown)):
        bad = False
        for left, right in itertools.combinations(group, 2):
            if not can_place(left, (right,)):
                bad = True
                break
        if bad:
            continue
        codes = sorted(group, key=lambda item: (len(item), item))
        assign = dict(zip(letters, codes))
        total = 0
        for letter, count in freq.items():
            code = known_map.get(letter) or assign[letter]
            total += count * len(code)
        if best_total is None or total < best_total:
            best_total = total
            best_assign = {**known_map, **assign}
    if best_total is None:
        raise SystemExit(f"слово не кодируется: {word} {known_map}")
    return best_total, best_assign


def path_words(code: str) -> str:
    steps = ["вправо" if bit == "1" else "влево" for bit in code]
    return " → ".join(steps)


def tree_svg(pairs: list[tuple[str, str]], caption: str) -> str:
    """Дерево: влево 0, вправо 1. Известные буквы подписаны на листьях."""
    depth = max((len(code) for _letter, code in pairs), default=1)
    depth = max(2, min(depth, 5))
    col_w, row_h = 54, 58
    width = col_w * (2**depth) + 24
    height = row_h * (depth + 1) + 36
    nodes: dict[str, str] = {"": ""}
    for letter, code in pairs:
        built = ""
        for bit in code:
            built += bit
            nodes.setdefault(built, "")
        nodes[code] = letter
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="12" y="22" font-size="15" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(caption)}</text>',
    ]
    pos: dict[str, tuple[float, float]] = {}
    for level in range(depth + 1):
        count = 2**level
        for index in range(count):
            node = f"{index:0{level}b}" if level else ""
            x = 12 + (index + 0.5) * (width - 24) / count
            y = 40 + level * row_h
            pos[node] = (x, y)
            if level and node[:-1] in pos:
                px, py = pos[node[:-1]]
                parts.append(f'<line x1="{px}" y1="{py + 12}" x2="{x}" y2="{y - 12}" stroke="#cbd5e1" stroke-width="2"/>')
            label = nodes.get(node, "")
            occupied = bool(label)
            fill = "#ddd6fe" if occupied else "#ffffff"
            parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{fill}" stroke="#6366f1"/>')
            if occupied:
                parts.append(
                    f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(label)}</text>'
                )
            elif level:
                bit = node[-1]
                parts.append(
                    f'<text x="{x}" y="{y + 28}" text-anchor="middle" font-size="11" fill="#78716c" font-family="Segoe UI, Arial, sans-serif">{bit}</text>'
                )
    parts.append("</svg>")
    return "\n".join(parts)


def program_sum(known: list[str], need: int) -> str:
    shown = ", ".join(repr(item) for item in known)
    return f"""def conflicts(a, b):
    # Одно слово — начало другого. Так условие Фано ломается.
    return a.startswith(b) or b.startswith(a)

known = [{shown}]  # МЕНЯТЬ: уже занятые коды
need = {need}  # МЕНЯТЬ: сколько новых букв
limit = 5
free = []
for length in range(1, limit + 1):
    for i in range(2 ** length):
        code = f"{{i:0{{length}}b}}"
        if all(not conflicts(code, old) for old in known):
            free.append(code)

best = None
from itertools import combinations
for group in combinations(free, need):
    bad = False
    for i, left in enumerate(group):
        for right in group[i + 1:]:
            if conflicts(left, right):
                bad = True
    if bad:
        continue
    score = sum(len(code) for code in group)
    if best is None or score < best:
        best = score
print(best)
"""


def program_reverse(known: list[str]) -> str:
    shown = ", ".join(repr(item) for item in known)
    return f"""def conflicts(a, b):
    return a.startswith(b) or b.startswith(a)

known = [{shown}]  # МЕНЯТЬ: коды как в условии
rev = [code[::-1] for code in known]
chosen = None
for length in range(1, 8):
    level = []
    for i in range(2 ** length):
        code = f"{{i:0{{length}}b}}"
        if all(not conflicts(code, old) for old in rev):
            level.append(code)
    if level:
        chosen = max(level, key=lambda code: int(code[::-1], 2))
        break
# Печатаем код в обычном порядке, не перевёрнутый.
print(chosen[::-1])
"""


def program_one(known: list[str], prefer: str) -> str:
    shown = ", ".join(repr(item) for item in known)
    pick = "max" if prefer == "max" else "min"
    comment = "наибольшее число" if prefer == "max" else "наименьшее число"
    return f"""def conflicts(a, b):
    return a.startswith(b) or b.startswith(a)

known = [{shown}]  # МЕНЯТЬ
chosen = None
for length in range(1, 8):
    level = []
    for i in range(2 ** length):
        code = f"{{i:0{{length}}b}}"
        if all(not conflicts(code, old) for old in known):
            level.append(code)
    if level:
        # Несколько кодов одной длины: берём {comment}.
        chosen = {pick}(level, key=lambda code: int(code, 2))
        break
print(chosen)
"""


def theory_sum(demo_pairs, demo_codes, demo_sum) -> str:
    steps = []
    for letter, code in demo_pairs:
        steps.append(
            f"<li>Буква {esc(letter)}, код <code>{esc(code)}</code>. "
            f"От корня: {esc(path_words(code))}. Этот лист закрыт, ниже него букв больше нет.</li>"
        )
    codes = ", ".join(f"<code>{esc(item)}</code>" for item in demo_codes)
    lengths = " + ".join(str(len(item)) for item in demo_codes)
    return f"""
<h2>Что просят в задании 4</h2>
<p>По каналу передают буквы. У каждой своё кодовое слово из нулей и единиц. Код должен подчиняться <strong>условию Фано</strong>: ни одно слово не является началом другого. Тогда сообщение читается однозначно, слева направо.</p>
<p>Удобно рисовать дерево. От корня шаг <strong>влево — это 0</strong>, шаг <strong>вправо — это 1</strong>. Буква стоит только на листе: из этой точки больше никуда не идём.</p>
<h2>Как искать сумму длин</h2>
<p>Часть кодов уже дана. Оставшиеся буквы надо посадить в свободные места так, чтобы сумма длин новых кодов была самой маленькой.</p>
<ol>
<li>Нарисуйте известные коды и закройте их ветки.</li>
<li>Свободное место — вершина, которая сама не занята и не лежит на пути к занятой букве.</li>
<li>Сначала смотрите короткие места. Длинное берите, только если коротких не хватает на все новые буквы.</li>
<li>В ответ пишут сумму длин новых кодов, не сами слова. Если в условии просят сумму всех кодов, прибавьте ещё длины известных.</li>
</ol>
<h2>Пример по шагам</h2>
<p>Известны пять кодов. Нужны ещё три буквы, сумма длин минимальная.</p>
<ol>{''.join(steps)}</ol>
<figure class="shot"><img src="images/n4-a-demo.svg" alt="Дерево примера: известные буквы закрывают ветки"></figure>
<p>Короткие свободные коды для трёх новых букв: {codes}. Длины {lengths} = <strong>{demo_sum}</strong>. Глубже спускаться не нужно: более длинный набор даст большую сумму.</p>
<p>Частая ошибка: посадить все новые буквы на одной глубине, хотя два коротких кода и один чуть длиннее дают меньшую сумму.</p>
"""


def theory_one(letter: str, answer: str, pairs) -> str:
    steps = "".join(
        f"<li>{esc(name)} = <code>{esc(code)}</code>, путь: {esc(path_words(code))}.</li>"
        for name, code in pairs
    )
    return f"""
<h2>Один самый короткий код</h2>
<p>В этом приёме неизвестна одна буква. Нужен самый короткий код, который не начинается с чужого и сам не является началом чужого.</p>
<p>Если таких коротких кодов несколько, в условии написано, какой взять: с <strong>наибольшим</strong> или с <strong>наименьшим</strong> числом. Число считают как обычное двоичное: 110 это 6, 100 это 4. Не угадывайте правило, прочитайте последнюю фразу условия.</p>
<h2>Пример</h2>
<p>Нужен код буквы {esc(letter)}. Если кодов одной длины несколько, берём наибольшее число.</p>
<ol>{steps}</ol>
<figure class="shot"><img src="images/n4-b-demo.svg" alt="Дерево: куда можно поставить одну новую букву"></figure>
<p>Самое короткое свободное место — <code>{esc(answer)}</code>. Это и есть ответ.</p>
<p>Не берите код длиннее, если на дереве уже есть свободный лист выше. И не ставьте букву на ветку, которая ведёт к уже занятой букве: тогда одно слово станет началом другого.</p>
"""


def theory_word(word: str, known: dict[str, str], total: int, assign: dict[str, str]) -> str:
    rows = "".join(
        f"<tr><td>{esc(letter)}</td><td>{count}</td><td><code>{esc(assign[letter])}</code></td></tr>"
        for letter, count in Counter(word).most_common()
    )
    known_text = ", ".join(f"{esc(letter)} = <code>{esc(code)}</code>" for letter, code in known.items())
    return f"""
<h2>Сколько знаков уйдёт на слово</h2>
<p>Просят не сумму длин алфавита, а длину одного слова. Частая буква должна получить короткий код: она встретится много раз, и каждый лишний знак повторится.</p>
<p>Сначала закрывают известные коды. Потом свободные места раздают: самый короткий код — самой частой ещё не закодированной букве, следующий — следующей по частоте.</p>
<h2>Пример. Слово «{esc(word)}»</h2>
<p>Уже известны: {known_text}.</p>
<figure class="shot"><img src="images/n4-c-demo.svg" alt="Дерево для кодирования слова"></figure>
<table>
<tr><th>буква</th><th>сколько раз в слове</th><th>код</th></tr>
{rows}
</table>
<p>Длина закодированного слова: каждая буква добавляет длину своего кода столько раз, сколько она встретилась. Получается <strong>{total}</strong>.</p>
<p>Если отдать короткий код редкой букве, а частую усадить глубоко, сумма станет больше. Это уже не минимум.</p>
"""


def theory_reverse(answer: str, pairs) -> str:
    steps = "".join(
        f"<li>{esc(name)} = <code>{esc(code)}</code>. Конец этого слова — «{esc(code[-1])}», целиком окончание нельзя занимать.</li>"
        for name, code in pairs
    )
    return f"""
<h2>Обратное условие Фано</h2>
<p>Иногда в условии сказано: ни одно кодовое слово не является <strong>окончанием</strong> другого. Сообщение тогда однозначно читается с конца, а не с начала.</p>
<p>Дерево строят так же, но путь читают с последнего знака. Проще перевернуть каждый известный код задом наперёд, решить как обычное Фано и перевернуть ответ обратно.</p>
<h2>Пример</h2>
<ol>{steps}</ol>
<figure class="shot"><img src="images/n4-d-demo.svg" alt="Коды для обратного условия Фано"></figure>
<p>Самый короткий новый код, который не является окончанием чужого и сам не оканчивается чужим: <code>{esc(answer)}</code>. Если таких несколько, в этом примере берём наибольшее число.</p>
<p>Прямое дерево здесь обманывает: место, свободное слева направо, может быть занято, если смотреть с конца.</p>
"""


def lesson_theory(title: str, body: str, images: list[str]) -> dict:
    return {
        "type": "theory",
        "title": title,
        "content": body,
        "comment": title,
        "images": images,
    }


def lesson_short(title: str, question: str, answer: str, solution: str, image: str) -> dict:
    return {
        "type": "short_answer",
        "title": title,
        "question_text": question,
        "correct_answer": str(answer),
        "answer_normalize": "strip_casefold",
        "points": 3,
        "solution_text": solution,
        "images": [image],
    }


def lesson_code(title: str, src: str) -> dict:
    body = (
        "<h2>Программа</h2>"
        "<p>Нажмите «В интерпретатор» под кодом. Список known и число need можно заменить на свои из условия.</p>"
        + code_block(src)
    )
    return lesson_theory(title, body, [])


def unit(prefix: str, name: str, theory_html: str, theory_images: list[str], questions: list[dict], src: str) -> list[dict]:
    lessons = [lesson_theory(f"{prefix} Теория. {name}", theory_html, theory_images)]
    lessons.extend(questions)
    lessons.append(lesson_code(f"{prefix} Код", src))
    if len(lessons) > 10:
        raise SystemExit(f"{prefix}: {len(lessons)} квадратиков")
    return lessons


def build() -> tuple[list[dict], dict[str, str]]:
    files: dict[str, str] = {}
    lessons: list[dict] = []

    demo_a = [("Г", "11"), ("Д", "1000"), ("Е", "010"), ("Ж", "1001"), ("З", "011")]
    codes_a = best_codes([code for _n, code in demo_a], 3)
    sum_a = sum(len(item) for item in codes_a)
    if sum_a != 9:
        raise SystemExit(f"пример суммы дал {sum_a}, ждали 9, коды {codes_a}")
    files["n4-a-demo.svg"] = tree_svg(demo_a, "Пример: известные буквы")
    questions = []
    bank_a = [
        ([("А", "0"), ("Б", "10")], 2),
        ([("А", "11"), ("Б", "011"), ("В", "010")], 2),
        ([("А", "00"), ("Б", "010"), ("В", "011")], 3),
        ([("А", "1"), ("Б", "000")], 3),
        ([("А", "111"), ("Б", "110"), ("В", "10")], 2),
        ([("А", "000"), ("Б", "001"), ("В", "10")], 2),
        ([("А", "01"), ("Б", "100"), ("В", "101"), ("Г", "111")], 2),
    ]
    for index, (pairs, need) in enumerate(bank_a, start=1):
        known = [code for _n, code in pairs]
        got = best_codes(known, need)
        answer = sum(len(item) for item in got)
        image = f"n4-a-q{index}.svg"
        files[image] = tree_svg(pairs, f"Вопрос {index}")
        known_text = ", ".join(f"{name} = {code}" for name, code in pairs)
        shown = ", ".join(got)
        questions.append(
            lesson_short(
                f"4.1 Вопрос {index}",
                f"На рисунке известные коды: {known_text}. "
                f"Нужно закодировать ещё {need} буквы так, чтобы выполнялось условие Фано. "
                "Какова минимальная сумма длин новых кодов? Только число.",
                answer,
                f"<p>Новые коды, например: {esc(shown)}. Сумма длин <strong>{answer}</strong>.</p>",
                image,
            )
        )
    lessons.extend(
        unit(
            "4.1",
            "Сумма длин",
            theory_sum(demo_a, codes_a, sum_a),
            ["n4-a-demo.svg"],
            questions,
            program_sum([code for _n, code in demo_a], 3),
        )
    )

    demo_b = [("В", "11110"), ("Е", "000"), ("Ч", "01"), ("Н", "100"), ("О", "101"), ("Т", "1110"), ("Ь", "001")]
    answer_b = shortest_one([code for _n, code in demo_b], "max")
    if answer_b != "110":
        raise SystemExit(f"пример одного кода дал {answer_b}, ждали 110")
    files["n4-b-demo.svg"] = tree_svg(demo_b, "Куда поставить букву С")
    questions = []
    bank_b = [
        ([("А", "1"), ("Б", "010"), ("В", "000")], "max"),
        ([("А", "0"), ("Б", "111")], "max"),
        ([("А", "10"), ("Б", "110"), ("В", "111")], "min"),
        ([("А", "00"), ("Б", "011"), ("В", "010")], "max"),
        ([("А", "111"), ("Б", "110"), ("В", "01")], "min"),
        ([("А", "100"), ("Б", "101"), ("В", "11")], "max"),
        ([("А", "000"), ("Б", "001"), ("В", "10")], "min"),
    ]
    for index, (pairs, prefer) in enumerate(bank_b, start=1):
        known = [code for _n, code in pairs]
        answer = shortest_one(known, prefer)
        image = f"n4-b-q{index}.svg"
        files[image] = tree_svg(pairs, f"Вопрос {index}")
        rule = "наибольшим" if prefer == "max" else "наименьшим"
        known_text = ", ".join(f"{name} = {code}" for name, code in pairs)
        questions.append(
            lesson_short(
                f"4.2 Вопрос {index}",
                f"Известные коды: {known_text}. "
                f"Найдите самый короткий код для новой буквы. "
                f"Если таких кодов несколько, выберите с {rule} числовым значением. "
                "В ответе только нули и единицы.",
                answer,
                f"<p>Подходит <strong>{esc(answer)}</strong>.</p>",
                image,
            )
        )
    lessons.extend(
        unit(
            "4.2",
            "Один код",
            theory_one("С", answer_b, demo_b),
            ["n4-b-demo.svg"],
            questions,
            program_one([code for _n, code in demo_b], "max"),
        )
    )

    word = "КОЛОКОЛ"
    known_c = {"Н": "11", "З": "100"}
    total_c, assign_c = encode_length(word, known_c)
    files["n4-c-demo.svg"] = tree_svg(
        [(letter, code) for letter, code in sorted(assign_c.items())],
        "Коды для слова КОЛОКОЛ",
    )
    questions = []
    bank_c = [
        ("МАМА", {"Б": "11"}),
        ("ТОПОТ", {"А": "00"}),
        ("КАКАО", {"Н": "11"}),
        ("БАРАБАН", {"Н": "000"}),
        ("МОЛОКО", {"К": "10"}),
        ("АНАНАС", {"К": "111"}),
        ("ПОПОЛ", {"М": "01"}),
    ]
    for index, (text, known_map) in enumerate(bank_c, start=1):
        total, assign = encode_length(text, known_map)
        image = f"n4-c-q{index}.svg"
        files[image] = tree_svg(list(known_map.items()), f"Уже занято, слово {text}")
        known_text = ", ".join(f"{name} = {code}" for name, code in known_map.items())
        rows = ", ".join(f"{letter}→{assign[letter]}" for letter in sorted(assign))
        questions.append(
            lesson_short(
                f"4.3 Вопрос {index}",
                f"Слово «{text}». Уже известны коды: {known_text}. "
                "Остальные буквы слова закодируйте условием Фано так, "
                "чтобы на всё слово ушло как можно меньше двоичных знаков. "
                "В ответе это количество. Только число.",
                total,
                f"<p>Один из минимальных наборов: {esc(rows)}. Длина слова <strong>{total}</strong>.</p>",
                image,
            )
        )
    lessons.extend(
        unit(
            "4.3",
            "Длина слова",
            theory_word(word, known_c, total_c, assign_c),
            ["n4-c-demo.svg"],
            questions,
            (
                f"word = {word!r}\n"
                f"codes = {assign_c!r}  # МЕНЯТЬ: коды, которые выбрали по дереву\n"
                "total = 0\n"
                "for ch in word:\n"
                "    total += len(codes[ch])\n"
                "print(total)\n"
            ),
        )
    )

    demo_d = [("А", "10"), ("Б", "11"), ("В", "01")]
    answer_d = shortest_reverse([code for _n, code in demo_d], "max")
    files["n4-d-demo.svg"] = tree_svg(demo_d, "Обратное Фано")
    questions = []
    bank_d = [
        ([("А", "100"), ("Б", "110"), ("В", "010")], "max"),
        ([("А", "00"), ("Б", "11")], "min"),
        ([("А", "101"), ("Б", "011")], "max"),
        ([("А", "111"), ("Б", "001"), ("В", "10")], "min"),
        ([("А", "000"), ("Б", "100")], "max"),
        ([("А", "01"), ("Б", "001")], "max"),
        ([("А", "110"), ("Б", "010"), ("В", "00")], "min"),
    ]
    for index, (pairs, prefer) in enumerate(bank_d, start=1):
        known = [code for _n, code in pairs]
        answer = shortest_reverse(known, prefer)
        image = f"n4-d-q{index}.svg"
        files[image] = tree_svg(pairs, f"Вопрос {index}, с конца")
        rule = "наибольшим" if prefer == "max" else "наименьшим"
        known_text = ", ".join(f"{name} = {code}" for name, code in pairs)
        questions.append(
            lesson_short(
                f"4.4 Вопрос {index}",
                f"Обратное условие Фано: ни один код не окончание другого. "
                f"Известны: {known_text}. "
                f"Самый короткий код новой буквы, при равенстве — с {rule} числом. "
                "Только нули и единицы.",
                answer,
                f"<p>Ответ <strong>{esc(answer)}</strong>. Проверка: переверните коды, решите прямое Фано и переверните результат.</p>",
                image,
            )
        )
    lessons.extend(
        unit(
            "4.4",
            "Обратное Фано",
            theory_reverse(answer_d, demo_d),
            ["n4-d-demo.svg"],
            questions,
            program_reverse([code for _n, code in demo_d]),
        )
    )
    return lessons, files


def main() -> None:
    # контрольные ответы из старого разбора
    if sum(len(item) for item in best_codes(["1100", "1011", "100"], 4)) != 11:
        raise SystemExit("задача со знаками должна давать 11")
    known3 = ["1001", "00", "011", "01010"]
    extra = best_codes(known3, 4)
    total3 = sum(len(item) for item in known3) + sum(len(item) for item in extra)
    if total3 != 27:
        raise SystemExit(f"БЛОКЧЕЙН дал {total3}, коды {extra}")

    lessons, files = build()
    titles = [lesson["title"] for lesson in lessons]
    if len(titles) != len(set(titles)):
        raise SystemExit("одинаковые названия")
    units: dict[str, int] = {}
    for lesson in lessons:
        key = lesson["title"].split()[0]
        units[key] = units.get(key, 0) + 1
    too_big = [f"{key}={count}" for key, count in units.items() if count > 10]
    if too_big:
        raise SystemExit("больше 10 квадратиков: " + ", ".join(too_big))

    PACK.mkdir(parents=True, exist_ok=True)
    img = PACK / "images"
    img.mkdir(parents=True, exist_ok=True)
    for old in img.glob("n4-*.svg"):
        old.unlink()
    for name, text in files.items():
        (img / name).write_text(text, encoding="utf-8")
    manifest = {
        "pack_id": "ege-n4-questions",
        "course_slug": "ege-informatika",
        "module_title": "2-й урок ЕГЭ: Кодирование и поиск",
        "create_module": True,
        "replace_missing": True,
        "module_description": (
            "Задание 4. Четыре урока: сумма длин, один код, длина слова, обратное Фано. "
            "В каждом теория, вопросы и программа."
        ),
    }
    (PACK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {"meta": {"topic": manifest["module_title"], "images_dir": "images/"}, "lessons": lessons}
    (PACK / "questions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    body = "\n".join(lesson["content"] for lesson in lessons if lesson["type"] == "theory")
    page = f"<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'><title>Задание 4</title></head><body>{body}</body></html>"
    (PACK / "theory.html").write_text(page, encoding="utf-8")
    (PACK / "preview.html").write_text(page, encoding="utf-8")
    zip_path = ROOT / "ege-n4-import.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(PACK / "manifest.json", "manifest.json")
        zf.write(PACK / "questions.json", "questions.json")
        for name in sorted(files):
            zf.write(img / name, f"images/{name}")
    READY.mkdir(parents=True, exist_ok=True)
    target = READY / "04-ege-n4-import.zip"
    target.write_bytes(zip_path.read_bytes())
    print("units", units, "images", len(files))
    print("zip", zip_path)


if __name__ == "__main__":
    main()
