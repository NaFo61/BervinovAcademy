# -*- coding: utf-8 -*-
"""Уроки 1, 2 и 3 по прототипам: схемы SVG, практика, домашка, контрольная.

Ответы считает этот скрипт. Если сопоставление графа не однозначно, задача не попадает в пакет.
"""

from __future__ import annotations

import html
import itertools
import json
import random
import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READY = ROOT / "к-импорту"


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def ol(steps: list[str]) -> str:
    return "<ol>" + "".join(f"<li>{step}</li>" for step in steps) + "</ol>"


def fig(name: str, alt: str) -> str:
    return f'<figure class="shot"><img src="images/{name}" alt="{esc(alt)}"></figure>'


def h2_parts(body: str) -> list[str]:
    chunks = re.split(r"(?=<h2>)", body)
    return [chunk.strip() for chunk in chunks if chunk.strip().startswith("<h2>")]


def pack_unit(prefix: str, name: str, theory_html: str, questions: list[dict], code_src: str) -> list[dict]:
    """Один урок прототипа: теория, вопросы, программа. Не больше 10 квадратиков."""
    if len(questions) > 8:
        raise SystemExit(f"{prefix}: вопросов {len(questions)}, вместе с теорией и кодом больше 10")
    lessons = [theory_only(f"{prefix} Теория. {name}", theory_html)]
    for index, item in enumerate(questions, start=1):
        titled = dict(item)
        titled["title"] = f"{prefix} Вопрос {index}"
        lessons.append(titled)
    code_html = (
        "<h2>Программа</h2>"
        "<p>Нажмите «В интерпретатор» под кодом. Программу можно менять и запускать заново.</p>"
        + code(code_src)
    )
    lessons.append(theory_only(f"{prefix} Код", code_html))
    return lessons


def theory_only(title: str, html: str) -> dict:
    names: list[str] = []
    for name in re.findall(r"images/([^\"']+)", html):
        if name not in names:
            names.append(name)
    return {
        "type": "theory",
        "title": title,
        "content": html,
        "comment": title,
        "images": names,
    }


def spoil(question: str, solution: str) -> str:
    return (
        f"<p>{question}</p>"
        "<details><summary>Показать ответ и разбор</summary>"
        + solution
        + "</details>"
    )


def code(src: str) -> str:
    return "<pre><code>" + html.escape(src.strip("\n"), quote=False) + "</code></pre>"


def wrap_page(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<style>
body {{ font-family: "Times New Roman", Times, serif; max-width: 820px; margin: 24px auto; padding: 0 16px; line-height: 1.45; color: #1c1917; }}
img {{ max-width: 100%; height: auto; }}
table {{ border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #d6d3d1; padding: 4px 8px; }}
pre {{ background: #0f172a; color: #e2e8f0; padding: 12px; overflow: auto; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def short(title, question, correct, solution, images, points=3) -> dict:
    return {
        "type": "short_answer",
        "title": title,
        "question_text": question,
        "correct_answer": str(correct),
        "answer_normalize": "strip_casefold",
        "points": points,
        "solution_text": solution,
        "images": images,
    }


def check(title, question, answers, solution) -> dict:
    return {
        "type": "checkbox",
        "title": title,
        "question_text": question,
        "points": 4,
        "answers": answers,
        "solution_text": solution,
    }


def radio(title, question, answers, solution) -> dict:
    return {
        "type": "radio",
        "title": title,
        "question_text": question,
        "points": 3,
        "answers": answers,
        "solution_text": solution,
    }


def ek(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def adjacency(letters: str, edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    adj = {ch: [] for ch in letters}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def is_connected(letters: str, edges: list[tuple[str, str]]) -> bool:
    adj = adjacency(letters, edges)
    seen = set()
    stack = [letters[0]]
    while stack:
        v = stack.pop()
        if v in seen:
            continue
        seen.add(v)
        stack.extend(adj[v])
    return len(seen) == len(letters)


def degrees(letters: str, edges: list[tuple[str, str]]) -> dict[str, int]:
    adj = adjacency(letters, edges)
    return {ch: len(adj[ch]) for ch in letters}


def perm_maps(letters: str) -> list[dict[str, int]]:
    n = len(letters)
    nums = list(range(1, n + 1))
    patterns = [
        nums,
        list(reversed(nums)),
        nums[n // 2 :] + nums[: n // 2],
        nums[1:] + nums[:1],
        nums[2:] + nums[:2],
    ]
    swapped = nums[:]
    swapped[0], swapped[-1] = swapped[-1], swapped[0]
    patterns.append(swapped)
    out = []
    for pattern in patterns:
        if sorted(pattern) != nums:
            continue
        out.append({ch: pattern[i] for i, ch in enumerate(letters)})
    return out


def deduce(letters: str, edges: list[tuple[str, str]], perm: dict[str, int]):
    """Вернуть сопоставление буква→номер, шаги и номер круга, либо None."""
    nums = list(range(1, len(letters) + 1))
    adj = adjacency(letters, edges)
    cell = {(i, j): False for i in nums for j in nums}
    for a, b in edges:
        cell[(perm[a], perm[b])] = True
        cell[(perm[b], perm[a])] = True
    neigh_n = {i: {j for j in nums if i != j and cell[(i, j)]} for i in nums}
    assigned: dict[str, int] = {}
    rounds: dict[str, int] = {}
    steps: list[str] = []
    guard = 0
    while len(assigned) < len(letters) and guard < 12:
        guard += 1
        free_l = [ch for ch in letters if ch not in assigned]
        free_n = [i for i in nums if i not in assigned.values()]

        def sig_l(ch: str):
            known = tuple(sorted(assigned[x] for x in adj[ch] if x in assigned))
            free = sum(1 for x in adj[ch] if x not in assigned)
            return (len(adj[ch]), known, free)

        def sig_n(i: int):
            known = tuple(sorted(j for j in neigh_n[i] if j in assigned.values()))
            free = sum(1 for j in neigh_n[i] if j not in assigned.values())
            return (len(neigh_n[i]), known, free)

        groups_l: dict[tuple, list[str]] = {}
        groups_n: dict[tuple, list[int]] = {}
        for ch in free_l:
            groups_l.setdefault(sig_l(ch), []).append(ch)
        for i in free_n:
            groups_n.setdefault(sig_n(i), []).append(i)
        found = []
        for sig, names in groups_l.items():
            rows = groups_n.get(sig, [])
            if len(names) == 1 and len(rows) == 1:
                found.append((names[0], rows[0], sig))
        if not found:
            break
        found.sort()
        for ch, num, sig in found:
            assigned[ch] = num
            rounds[ch] = guard
            if not sig[1]:
                steps.append(
                    f"У пункта {ch} дорог {sig[0]}, и такое число на схеме одно. "
                    f"В таблице столько же только у пункта {num}. Значит {ch} = {num}."
                )
            else:
                known = ", ".join(str(x) for x in sig[1])
                steps.append(
                    f"Из уже найденных соседей пункта {ch} есть номера {known}. "
                    f"Так же связан только пункт {num}. Значит {ch} = {num}."
                )
    if len(assigned) != len(letters) or any(assigned[ch] != perm[ch] for ch in letters):
        return None
    return assigned, steps, rounds


def graph_svg(letters: str, edges, weights, badges: dict[str, int] | None, title: str) -> str:
    n = len(letters)
    cx, cy, radius = 260, 250, 148
    pos = {}
    for i, ch in enumerate(letters):
        ang = -3.14159265 / 2 + 2 * 3.14159265 * i / n
        pos[ch] = (cx + radius * __import__("math").cos(ang), cy + radius * __import__("math").sin(ang))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 470" width="520" height="470">',
        '<rect width="520" height="470" fill="#ffffff"/>',
        f'<text x="260" y="28" text-anchor="middle" font-size="18" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(title)}</text>',
    ]
    for a, b in edges:
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#334155" stroke-width="2.5"/>'
        )
        if weights is not None:
            key = ek(a, b)
            label = str(weights[key])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            parts.append(
                f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" font-size="14" font-weight="700" fill="#9a3412" stroke="#ffffff" stroke-width="4" paint-order="stroke" font-family="Segoe UI, Arial, sans-serif">{esc(label)}</text>'
            )
    for ch in letters:
        x, y = pos[ch]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="24" fill="#eef2ff" stroke="#3730a3" stroke-width="2.5"/>')
        parts.append(
            f'<text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(ch)}</text>'
        )
        if badges and ch in badges:
            bx, by = x + 20, y - 20
            parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="12" fill="#f59e0b" stroke="#ffffff" stroke-width="2"/>')
            parts.append(
                f'<text x="{bx:.1f}" y="{by + 4:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#1c1917" font-family="Segoe UI, Arial, sans-serif">{badges[ch]}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def table_svg(letters: str, edges, perm: dict[str, int], weights, title: str) -> str:
    n = len(letters)
    cell = {(i, j): None for i in range(1, n + 1) for j in range(1, n + 1)}
    for a, b in edges:
        i, j = perm[a], perm[b]
        value = "*" if weights is None else str(weights[ek(a, b)])
        cell[(i, j)] = value
        cell[(j, i)] = value
    size = 46
    left, top = 36, 64
    width = left + (n + 1) * size + 24
    height = top + (n + 1) * size + 36
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.0f}" y="28" text-anchor="middle" font-size="18" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(title)}</text>',
    ]

    def box(c, r, text, fill, bold=False):
        x = left + c * size
        y = top + r * size
        weight = "700" if bold else "500"
        parts.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{fill}" stroke="#cbd5e1"/>')
        if text:
            parts.append(
                f'<text x="{x + size / 2}" y="{y + 29}" text-anchor="middle" font-size="16" font-weight="{weight}" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(text)}</text>'
            )

    box(0, 0, "", "#e0e7ff", True)
    for i in range(1, n + 1):
        box(i, 0, str(i), "#e0e7ff", True)
        box(0, i, str(i), "#e0e7ff", True)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i == j:
                box(j, i, "", "#f1f5f9")
            else:
                box(j, i, cell[(i, j)] or "", "#ffffff")
    note = "Число — длина дороги. Пусто — дороги нет." if weights else "Звёздочка — дорога есть. Пусто — дороги нет."
    parts.append(
        f'<text x="{left}" y="{height - 12}" font-size="13" fill="#57534e" font-family="Segoe UI, Arial, sans-serif">{esc(note)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def legend_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 180" width="520" height="180">
<rect width="520" height="180" fill="#ffffff"/>
<text x="260" y="28" text-anchor="middle" font-size="18" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Как считать дороги</text>
<circle cx="90" cy="100" r="24" fill="#eef2ff" stroke="#3730a3" stroke-width="2.5"/>
<text x="90" y="106" text-anchor="middle" font-size="18" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">A</text>
<line x1="112" y1="88" x2="180" y2="60" stroke="#334155" stroke-width="2.5"/>
<line x1="114" y1="100" x2="190" y2="100" stroke="#334155" stroke-width="2.5"/>
<line x1="112" y1="112" x2="180" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="180" cy="60" r="8" fill="#3730a3"/>
<circle cx="190" cy="100" r="8" fill="#3730a3"/>
<circle cx="180" cy="140" r="8" fill="#3730a3"/>
<text x="220" y="96" font-size="16" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Из A выходят три линии. Значит у A три дороги.</text>
<text x="220" y="122" font-size="16" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Линии просто пересеклись, а буквы нет — это не город.</text>
</svg>"""


def answer_format_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="520" height="120">
<rect width="520" height="120" fill="#ffffff"/>
<text x="20" y="36" font-size="16" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Спросили два номера, 2 и 5. Пишем по возрастанию:</text>
<rect x="20" y="52" width="90" height="44" rx="8" fill="#ecfdf5" stroke="#059669"/>
<text x="65" y="81" text-anchor="middle" font-size="22" font-weight="700" fill="#065f46" font-family="Segoe UI, Arial, sans-serif">25</text>
<text x="130" y="80" font-size="16" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Не 52 и не «2 5».</text>
</svg>"""


def search_graphs() -> list[dict]:
    found = []
    for n, k_edges in ((5, 5), (5, 6), (5, 7), (6, 6), (6, 7)):
        letters = "ABCDEF"[:n]
        possible = list(itertools.combinations(letters, 2))
        combs = list(itertools.combinations(possible, k_edges))
        if len(combs) > 700:
            step = max(1, len(combs) // 700)
            combs = combs[::step]
        for comb in combs:
            edges = [(a, b) for a, b in comb]
            if not is_connected(letters, edges):
                continue
            deg = degrees(letters, edges)
            counts = Counter(deg.values())
            if not any(v == 1 for v in counts.values()):
                continue
            if any(v == 0 for v in deg.values()):
                continue
            for perm in perm_maps(letters):
                result = deduce(letters, edges, perm)
                if result is None:
                    continue
                _assigned, steps, rounds = result
                found.append(
                    {
                        "letters": letters,
                        "edges": edges,
                        "perm": perm,
                        "steps": steps,
                        "rounds": rounds,
                        "deg": deg,
                        "shape": tuple(sorted(ek(a, b) for a, b in edges)),
                    }
                )
    return found


def classify(found: list[dict]) -> dict[str, list[dict]]:
    pools = {"A": [], "B": [], "C": []}
    seen = {"A": set(), "B": set(), "C": set()}
    for item in found:
        letters = item["letters"]
        edges = item["edges"]
        perm = item["perm"]
        rounds = item["rounds"]
        deg = item["deg"]
        adj = adjacency(letters, edges)
        weights = {ek(a, b): 5 + i * 2 for i, (a, b) in enumerate(edges)}
        base = {
            "letters": letters,
            "edges": edges,
            "perm": perm,
            "steps": item["steps"],
            "rounds": rounds,
            "deg": deg,
            "weights": weights,
            "shape": item["shape"],
        }
        for a, b in itertools.combinations(letters, 2):
            n1, n2 = perm[a], perm[b]
            answer = f"{min(n1, n2)}{max(n1, n2)}"
            key = (item["shape"], tuple(sorted((a, b))), answer)
            if key in seen["A"]:
                continue
            seen["A"].add(key)
            hard = max(rounds[a], rounds[b])
            pools["A"].append(
                {
                    **base,
                    "proto": "A",
                    "answer": answer,
                    "hard": hard,
                    "ask": (a, b),
                    "question": (
                        f"Какие номера у пунктов {a} и {b}? "
                        "Запишите две цифры по возрастанию, без пробела."
                    ),
                    "tail": (
                        f"Пункт {a} — это номер {n1}. Пункт {b} — это номер {n2}. "
                        f"По возрастанию получается {answer}."
                    ),
                }
            )
        leafs = [ch for ch in letters if deg[ch] == 1 and rounds[ch] == 1]
        for leaf in leafs:
            neighbor = adj[leaf][0]
            if rounds[neighbor] == 1:
                continue
            for other in adj[neighbor]:
                if other == leaf:
                    continue
                w1 = weights[ek(leaf, neighbor)]
                w2 = weights[ek(neighbor, other)]
                answer = str(w1 + w2)
                key = (item["shape"], leaf, neighbor, other, answer)
                if key in seen["C"]:
                    continue
                seen["C"].add(key)
                pools["C"].append(
                    {
                        **base,
                        "proto": "C",
                        "answer": answer,
                        "hard": max(rounds[neighbor], rounds[other]),
                        "ask": ((leaf, neighbor), (neighbor, other)),
                        "question": (
                            f"Найдите сумму длин дорог {leaf}—{neighbor} и {neighbor}—{other}. "
                            "Только число."
                        ),
                        "tail": (
                            f"Дорога {leaf}—{neighbor} стоит между пунктами {perm[leaf]} и {perm[neighbor]}: это {w1}. "
                            f"Дорога {neighbor}—{other} стоит между пунктами {perm[neighbor]} и {perm[other]}: это {w2}. "
                            f"Сумма {w1} + {w2} = {answer}."
                        ),
                    }
                )
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            verts = {a, b, c, d}
            if any(rounds[v] > 1 for v in verts):
                continue
            w1 = weights[ek(a, b)]
            w2 = weights[ek(c, d)]
            answer = str(w1 + w2)
            key = (item["shape"], ek(a, b), ek(c, d), answer)
            if key in seen["B"]:
                continue
            seen["B"].add(key)
            pools["B"].append(
                {
                    **base,
                    "proto": "B",
                    "answer": answer,
                    "hard": 1,
                    "ask": ((a, b), (c, d)),
                    "question": (
                        f"Найдите сумму длин дорог {a}—{b} и {c}—{d}. Только число."
                    ),
                    "tail": (
                        f"Дорога {a}—{b} стоит между пунктами {perm[a]} и {perm[b]}: это {w1}. "
                        f"Дорога {c}—{d} стоит между пунктами {perm[c]} и {perm[d]}: это {w2}. "
                        f"Сумма {w1} + {w2} = {answer}."
                    ),
                }
            )
    for key in pools:
        pools[key].sort(key=lambda row: (row["hard"], row["shape"], str(row["ask"]), row["answer"]))
    return pools


def take_diverse(rows: list[dict], count: int, used_shapes: set) -> list[dict]:
    picked = []
    used_answers = Counter()
    for row in rows:
        if row["shape"] in used_shapes:
            continue
        if used_answers[row["answer"]] >= 2:
            continue
        used_shapes.add(row["shape"])
        used_answers[row["answer"]] += 1
        picked.append(row)
        if len(picked) == count:
            break
    if len(picked) < count:
        for row in rows:
            if row in picked or row["shape"] in used_shapes:
                continue
            used_shapes.add(row["shape"])
            picked.append(row)
            if len(picked) == count:
                break
    if len(picked) < count:
        raise SystemExit(f"не хватило задач: нужно {count}, есть {len(picked)}")
    return picked


def task_images(row: dict, prefix: str, store: dict[str, str], with_badges: bool) -> list[str]:
    g_name = f"{prefix}-graph.svg"
    t_name = f"{prefix}-table.svg"
    weights = None if row["proto"] == "A" else row["weights"]
    store[g_name] = graph_svg(row["letters"], row["edges"], weights, row["deg"] if with_badges else None, "Схема дорог")
    store[t_name] = table_svg(row["letters"], row["edges"], row["perm"], weights, "Таблица")
    names = [g_name, t_name]
    if with_badges:
        b_name = f"{prefix}-degrees.svg"
        store[b_name] = graph_svg(row["letters"], row["edges"], weights, row["deg"], "Сколько дорог у каждой буквы")
        names.insert(1, b_name)
    return names


def solution_graph(row: dict) -> str:
    return (
        "<p><strong>Разбор по шагам.</strong></p>"
        + ol(row["steps"] + [row["tail"]])
        + f"<p>Ответ: <strong>{esc(row['answer'])}</strong>.</p>"
    )


def anchor_program(demo: dict) -> str:
    letters = demo["deg"]
    rows = {num: demo["deg"][ch] for ch, num in demo["perm"].items()}
    src = (
        "from collections import Counter\n"
        f"letters = {letters!r}  # МЕНЯТЬ: сколько дорог у буквы\n"
        f"rows = {rows!r}  # МЕНЯТЬ: сколько отметок в строке таблицы\n"
        "once = {deg for deg, cnt in Counter(letters.values()).items() if cnt == 1}\n"
        "for name, deg in letters.items():\n"
        "    if deg not in once:\n"
        "        continue\n"
        "    nums = [num for num, got in rows.items() if got == deg]\n"
        "    print(name, nums[0])\n"
    )
    if demo["proto"] == "A":
        left, right = demo["ask"]
        src += (
            f"\n# Редкие степени печатаются как «буква номер».\n"
            f"# Номера пунктов {left} и {right} запишите двумя цифрами по возрастанию.\n"
        )
        return src
    if demo["proto"] == "B":
        (a, b), (c, d) = demo["ask"]
        w1 = demo["weights"][ek(a, b)]
        w2 = demo["weights"][ek(c, d)]
    else:
        (leaf, neighbor), (_, other) = demo["ask"]
        w1 = demo["weights"][ek(leaf, neighbor)]
        w2 = demo["weights"][ek(neighbor, other)]
    src += (
        "\n# Когда номера найдены, длины берут из таблицы. Подставьте свои.\n"
        f"first = {w1}\n"
        f"second = {w2}\n"
        "print(first + second)\n"
    )
    return src


def build_task1(store: dict[str, str]):
    found = search_graphs()
    pools = classify(found)
    print("graph pools", {k: len(v) for k, v in pools.items()}, "shapes", len(found))
    used = set()
    demos = {}
    groups = {}
    for proto, need in (("A", 10), ("B", 10), ("C", 10)):
        chunk = take_diverse(pools[proto], need, used)
        demos[proto] = chunk[0]
        rest = chunk[1:]
        groups[proto] = {
            "practice": rest[:4],
            "homework": rest[4:7],
            "control": rest[7:9],
        }
    names = {
        "A": "Два номера",
        "B": "Сумма длин",
        "C": "Сосед тупика",
    }
    demo_imgs = {}
    for proto in "ABC":
        demo = demos[proto]
        demo_imgs[proto] = task_images(demo, f"n1-demo-{proto.lower()}", store, True)
        for key in ("practice", "homework"):
            for index, row in enumerate(groups[proto][key], start=1):
                task_images(row, f"n1-{proto.lower()}-{key[0]}{index}", store, False)
    body = theory_task1(demos, demo_imgs)
    store["n1-legend.svg"] = legend_svg()
    store["n1-answer.svg"] = answer_format_svg()
    sections = h2_parts(body)
    if len(sections) != 5:
        raise SystemExit(f"теория 1: частей {len(sections)}")
    contents = [
        "\n".join((sections[0], sections[1])),
        sections[2],
        sections[3],
    ]
    lessons = []
    for proto, html in zip("ABC", contents):
        questions = []
        for key, points in (("practice", 3), ("homework", 3)):
            for index, row in enumerate(groups[proto][key], start=1):
                imgs = [
                    f"n1-{proto.lower()}-{key[0]}{index}-graph.svg",
                    f"n1-{proto.lower()}-{key[0]}{index}-table.svg",
                ]
                questions.append(
                    short(
                        "черновик",
                        "Схема и таблица стоят над вопросом. " + row["question"],
                        row["answer"],
                        solution_graph(row),
                        imgs,
                        points,
                    )
                )
        lessons.extend(pack_unit(f"1.{'ABC'.index(proto) + 1}", names[proto], html, questions, anchor_program(demos[proto])))
    return lessons, "\n".join(item["content"] for item in lessons if item["type"] == "theory")


def checks_for(proto: str):
    common_true = [
        ["Точка с буквой — город, линия — дорога в обе стороны", True],
        ["Редкое число дорог — зацепка: такая буква и есть такой номер", True],
    ]
    if proto == "A":
        return common_true + [
            ["Два номера пишут двумя цифрами по возрастанию, без пробела", True],
            ["Номер 5 и номер 2 записывают как 52", False],
        ]
    if proto == "B":
        return common_true + [
            ["Длину дороги из таблицы берут один раз, хотя клетка есть в двух местах", True],
            ["В сумму входят все числа строки, даже чужие дороги", False],
        ]
    return common_true + [
        ["Если у тупика одна дорога, его сосед — тот единственный пункт, с которым он связан", True],
        ["Тупик можно не искать: у всех пунктов число дорог всегда разное", False],
    ]


def theory_task1(demos: dict, imgs: dict) -> str:
    a, b, c = demos["A"], demos["B"], demos["C"]
    letters = a["deg"]
    rows = {}
    for ch, num in a["perm"].items():
        rows[num] = a["deg"][ch]
    src = (
        "from collections import Counter\n"
        f"letters = {letters!r}  # МЕНЯТЬ: сколько дорог у буквы\n"
        f"rows = {rows!r}  # МЕНЯТЬ: сколько отметок в строке таблицы\n"
        "once = {deg for deg, cnt in Counter(letters.values()).items() if cnt == 1}\n"
        "for name, deg in letters.items():\n"
        "    if deg not in once:\n"
        "        continue\n"
        "    nums = [num for num, got in rows.items() if got == deg]\n"
        "    print(name, nums[0])\n"
    )
    parts = [
        "<h2>Что дают на экзамене</h2>",
        "<p>Рядом две вещи. Слева схема: города буквами, между ними дороги. Справа таблица: те же города, но под номерами. Какая буква какому номеру равна, не подписано. Это и надо восстановить.</p>",
        fig("n1-legend.svg", "Как считать дороги у точки"),
        "<p>Число линий из точки называют степенью. На экзамене слово можно не писать. Ищем не «центральную» точку, а точку с редким числом дорог. Если число встретилось один раз, это якорь: буква и номер — одна и та же вершина.</p>",
        "<p>В таблице звёздочка или число значит, что дорога есть. Пустая клетка — дороги нет. По диагонали всегда пусто. Дорога 2—4 и дорога 4—2 — одна и та же, в сумму её берут один раз.</p>",
        fig("n1-answer.svg", "Как записать два номера"),
        "<h2>Приём 1. Два номера</h2>",
        "<p>Спрашивают номера двух букв. В ответе две цифры по возрастанию. Сначала якоря, потом соседи, если букв с одинаковым числом несколько.</p>",
        f"<p><strong>Пример.</strong> {esc(a['question'])}</p>",
        fig(imgs["A"][0], "Схема примера с двумя номерами"),
        fig(imgs["A"][1], "Число дорог на схеме примера"),
        fig(imgs["A"][2], "Таблица примера с двумя номерами"),
        ol(a["steps"] + [a["tail"]]),
        f"<p>Ответ: <strong>{esc(a['answer'])}</strong>.</p>",
        "<h2>Приём 2. Сумма по якорям</h2>",
        "<p>В таблице уже километры. Нужные буквы видны по редкому числу дорог. Дальше в таблице на пересечении их номеров читают длины и складывают.</p>",
        f"<p><strong>Пример.</strong> {esc(b['question'])}</p>",
        fig(imgs["B"][0], "Схема примера с суммой"),
        fig(imgs["B"][1], "Число дорог на схеме с длинами"),
        fig(imgs["B"][2], "Таблица длин"),
        ol(b["steps"] + [b["tail"]]),
        f"<p>Ответ: <strong>{esc(b['answer'])}</strong>.</p>",
        "<h2>Приём 3. Сначала сосед тупика</h2>",
        "<p>Тупик — пункт с одной дорогой. Его номер часто виден сразу. Сосед тупика среди нескольких похожих пунктов один: в таблице он связан с номером тупика. Потом читают две длины и складывают.</p>",
        f"<p><strong>Пример.</strong> {esc(c['question'])}</p>",
        fig(imgs["C"][0], "Схема примера с тупиком"),
        fig(imgs["C"][1], "Число дорог, тупик отмечен"),
        fig(imgs["C"][2], "Таблица примера с тупиком"),
        ol(c["steps"] + [c["tail"]]),
        f"<p>Ответ: <strong>{esc(c['answer'])}</strong>.</p>",
        "<h2>Программа для якорей</h2>",
        "<p>Рисунок в код не переводят. Сначала глазами считают линии и отметки в строках. Программа ниже только проверяет якоря: редкая степень буквы ищется среди строк. Соседа тупика смотрят по таблице руками. Кнопка «В интерпретатор» откроет этот код.</p>",
        code(src),
        "<p>Дальше схемы без подсказок на рисунке. Разбор откроется после ответа.</p>",
    ]
    return "\n".join(parts)


def mini_op_svg(title: str, headers: list[str], rows: list[list[str]], red_row: int | None) -> str:
    cols = len(headers)
    size_x, size_y = 78, 36
    left, top = 16, 48
    width = left * 2 + cols * size_x
    height = top + (len(rows) + 1) * size_y + 16
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="16" y="28" font-size="16" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(title)}</text>',
    ]
    for c, head in enumerate(headers):
        x = left + c * size_x
        parts.append(f'<rect x="{x}" y="{top}" width="{size_x}" height="{size_y}" fill="#e0e7ff" stroke="#cbd5e1"/>')
        parts.append(
            f'<text x="{x + size_x / 2}" y="{top + 24}" text-anchor="middle" font-size="14" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(head)}</text>'
        )
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            x = left + c * size_x
            y = top + (r + 1) * size_y
            fill = "#fee2e2" if red_row == r else "#ffffff"
            parts.append(f'<rect x="{x}" y="{y}" width="{size_x}" height="{size_y}" fill="{fill}" stroke="#cbd5e1"/>')
            parts.append(
                f'<text x="{x + size_x / 2}" y="{y + 24}" text-anchor="middle" font-size="15" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(value)}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def truth_svg(headers: list[str], rows: list[list[str]], title: str) -> str:
    return mini_op_svg(title, headers, rows, None)


FORMULAS = [
    ("(A ∨ B) ∧ ¬C", lambda e: (e["A"] or e["B"]) and (not e["C"]), False),
    ("¬A ∧ (B ∨ C)", lambda e: (not e["A"]) and (e["B"] or e["C"]), False),
    ("(A ∧ ¬B) ∨ C", lambda e: (e["A"] and not e["B"]) or e["C"], False),
    ("¬(A ∧ B) ∧ C", lambda e: (not (e["A"] and e["B"])) and e["C"], False),
    ("(A ∨ C) ∧ (¬B ∨ C)", lambda e: (e["A"] or e["C"]) and ((not e["B"]) or e["C"]), False),
    ("(¬A ∨ B) ∧ ¬C", lambda e: ((not e["A"]) or e["B"]) and (not e["C"]), False),
    ("A ∧ (B ∨ ¬C)", lambda e: e["A"] and (e["B"] or not e["C"]), False),
    ("¬A ∨ ¬B ∨ C", lambda e: (not e["A"]) or (not e["B"]) or e["C"], False),
    ("(A → B) ∧ C", lambda e: ((not e["A"]) or e["B"]) and e["C"], True),
    ("A → (B ∧ C)", lambda e: (not e["A"]) or (e["B"] and e["C"]), True),
    ("¬(A → B)", lambda e: e["A"] and (not e["B"]), True),
    ("(A → B) ∨ ¬C", lambda e: ((not e["A"]) or e["B"]) or (not e["C"]), True),
    ("(A → ¬B) ∧ (B → C)", lambda e: ((not e["A"]) or (not e["B"])) and ((not e["B"]) or e["C"]), True),
    ("¬A → (B ∨ C)", lambda e: e["A"] or e["B"] or e["C"], True),
    ("(A ∧ B) → C", lambda e: (not (e["A"] and e["B"])) or e["C"], True),
    ("(A → B) ∧ (C → A)", lambda e: ((not e["A"]) or e["B"]) and ((not e["C"]) or e["A"]), True),
    ("(A ∨ B) ∧ (A ∨ ¬C)", lambda e: (e["A"] or e["B"]) and (e["A"] or (not e["C"])), False),
    ("(¬A ∧ B) ∨ (¬B ∧ C)", lambda e: ((not e["A"]) and e["B"]) or ((not e["B"]) and e["C"]), False),
    ("(¬A → B) ∧ C", lambda e: (e["A"] or e["B"]) and e["C"], True),
    ("(A → B) ∧ (B → C)", lambda e: ((not e["A"]) or e["B"]) and ((not e["B"]) or e["C"]), True),
]


def all_rows(fn):
    rows = []
    for bits in itertools.product((0, 1), repeat=3):
        env = {"A": bits[0], "B": bits[1], "C": bits[2]}
        rows.append((bits, 1 if fn(env) else 0))
    return rows


def blank_table(expr: str) -> tuple[list[str], list[list[str]]]:
    headers = ["A", "B", "C", "F"]
    rows = []
    for bits in itertools.product((0, 1), repeat=3):
        rows.append([str(bits[0]), str(bits[1]), str(bits[2]), ""])
    return headers, rows


def filled_table(expr: str, fn) -> str:
    head = "<table><thead><tr><th>A</th><th>B</th><th>C</th><th>F</th></tr></thead><tbody>"
    body = []
    total = 0
    for bits, value in all_rows(fn):
        total += value
        body.append(
            "<tr>"
            + "".join(f"<td>{bit}</td>" for bit in bits)
            + f"<td><strong>{value}</strong></td></tr>"
        )
    return head + "".join(body) + f"</tbody></table><p>Единиц в столбце F: <strong>{total}</strong>.</p>"


def count_answer(fn) -> int:
    return sum(value for _bits, value in all_rows(fn))


def py_count(expr_py: str) -> str:
    return f"""def F(A, B, C):
    return 1 if ({expr_py}) else 0

count = 0
for A in (0, 1):
    for B in (0, 1):
        for C in (0, 1):
            if F(A, B, C):
                count += 1
print(count)
"""


def expr_py(shown: str) -> str:
    text = shown
    repl = (
        ("¬A", "(not A)"),
        ("¬B", "(not B)"),
        ("¬C", "(not C)"),
        ("∧", " and "),
        ("∨", " or "),
        ("→", " , "),
    )
    # Стрелку раскрываем отдельно, скобки в формулах уже стоят.
    return shown


def to_python(shown: str) -> str:
    """Формула со скобками, ¬, ∧, ∨ и → в выражение Python."""
    src = shown.replace(" ", "")
    if "→" in src:
        src = implication_to_python(src)
    src = src.replace("¬", " not ")
    src = src.replace("∧", " and ").replace("∨", " or ")
    return src


def implication_to_python(shown: str) -> str:
    """A → B это (not A) or B. В формулах стрелка стоит между скобками или буквами."""
    src = shown.replace(" ", "")
    while "→" in src:
        i = src.index("→")
        left, left_span = take_left(src, i)
        right, right_span = take_right(src, i + 1)
        src = src[: left_span[0]] + "((not " + left + ") or " + right + ")" + src[right_span[1] :]
    return src


def take_left(src: str, i: int):
    if src[i - 1] != ")":
        if i >= 2 and src[i - 2] == "¬":
            return src[i - 2 : i], (i - 2, i)
        return src[i - 1], (i - 1, i)
    depth = 0
    j = i - 1
    while j >= 0:
        if src[j] == ")":
            depth += 1
        elif src[j] == "(":
            depth -= 1
            if depth == 0:
                return src[j:i], (j, i)
        j -= 1
    raise ValueError(src)


def take_right(src: str, i: int):
    if src[i] == "¬":
        return src[i : i + 2], (i, i + 2)
    if src[i] != "(":
        return src[i], (i, i + 1)
    depth = 0
    j = i
    while j < len(src):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                return src[i : j + 1], (i, j + 1)
        j += 1
    raise ValueError(src)


def fragment_task(fn, shown: str, col_order: tuple[str, str, str]):
    rows = all_rows(fn)
    names = ("A", "B", "C")
    displayed = []
    for bits, value in rows:
        env = {"A": bits[0], "B": bits[1], "C": bits[2]}
        shown_bits = tuple(env[name] for name in col_order)
        displayed.append((shown_bits, value))
    for size in (3, 4):
        for subset in itertools.combinations(range(len(displayed)), size):
            fragment = [displayed[i] for i in subset]
            if len({bits for bits, _value in fragment}) < len(fragment):
                continue
            good = []
            for cand in itertools.permutations(names):
                ok = True
                for bits, value in fragment:
                    env = {cand[k]: bits[k] for k in range(3)}
                    got = 1 if fn(env) else 0
                    if got != value:
                        ok = False
                        break
                if ok:
                    good.append("".join(cand))
            if len(good) == 1 and good[0] == "".join(col_order):
                return {
                    "expr": shown,
                    "fn": fn,
                    "cols": "".join(col_order),
                    "fragment": sorted(fragment),
                    "answer": good[0].lower(),
                }
    return None


def fragment_svg(task: dict) -> str:
    headers = ["столбец 1", "столбец 2", "столбец 3", "F"]
    rows = [[str(b) for b in bits] + [str(value)] for bits, value in task["fragment"]]
    return mini_op_svg("Фрагмент таблицы. Буквы столбцов неизвестны", headers, rows, None)


def fragment_code(task: dict) -> str:
    rows = ",\n    ".join(f"({bits}, {value})" for bits, value in task["fragment"])
    py = to_python(task["expr"])
    return f"""import itertools

def F(A, B, C):
    return 1 if ({py}) else 0

fragment = [
    {rows}
]
good = []
for perm in itertools.permutations("ABC"):
    ok = True
    for shown, value in fragment:
        env = dict(zip(perm, shown))
        if F(env["A"], env["B"], env["C"]) != value:
            ok = False
            break
    if ok:
        good.append("".join(perm).lower())
print(good[0])
"""


def build_task2(store: dict[str, str]):
    plain = [row for row in FORMULAS if not row[2]]
    impl = [row for row in FORMULAS if row[2]]
    if len(plain) < 10 or len(impl) < 10:
        raise SystemExit("мало формул")
    frags = []
    seen_answers = Counter()
    seen_expr = set()
    for col_order in itertools.permutations("ABC"):
        if col_order == ("A", "B", "C"):
            continue
        for shown, fn, _flag in FORMULAS:
            if shown in seen_expr or seen_answers["".join(col_order).lower()] >= 2:
                continue
            made = fragment_task(fn, shown, col_order)
            if not made:
                continue
            frags.append(made)
            seen_expr.add(shown)
            seen_answers[made["answer"]] += 1
            if len(frags) == 10:
                break
        if len(frags) == 10:
            break
    if len(frags) < 10:
        raise SystemExit(f"фрагментов {len(frags)}")
    store["n2-and.svg"] = mini_op_svg(
        "И: единица только когда оба условия да",
        ["A", "B", "A И B"],
        [["0", "0", "0"], ["0", "1", "0"], ["1", "0", "0"], ["1", "1", "1"]],
        None,
    )
    store["n2-or.svg"] = mini_op_svg(
        "ИЛИ: единица, если хотя бы одно да",
        ["A", "B", "A ИЛИ B"],
        [["0", "0", "0"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "1"]],
        None,
    )
    store["n2-not.svg"] = mini_op_svg(
        "НЕ меняет 0 и 1 местами",
        ["A", "НЕ A"],
        [["0", "1"], ["1", "0"]],
        None,
    )
    store["n2-impl.svg"] = mini_op_svg(
        "Если A, то B. Ложь только в одной строке",
        ["A", "B", "A → B"],
        [["0", "0", "1"], ["0", "1", "1"], ["1", "0", "0"], ["1", "1", "1"]],
        2,
    )
    groups = {
        "A": pack_counts(plain, "A", store),
        "B": pack_counts(impl, "B", store),
        "C": pack_frags(frags, store),
    }
    full = theory_lesson_2(groups, store)
    sections = h2_parts(full["content"])
    if len(sections) != 4:
        raise SystemExit(f"теория 2: частей {len(sections)}")
    contents = [sections[0] + "\n" + sections[1], sections[2], sections[3]]
    names = {
        "A": "Сколько единиц",
        "B": "Стрелка «если, то»",
        "C": "Буквы столбцов",
    }
    lessons = []
    for proto, html in zip("ABC", contents):
        questions = []
        for key, points in (("practice", 3), ("homework", 3)):
            for index, row in enumerate(groups[proto][key], start=1):
                questions.append(row_lesson(proto, "Задача", index, row, points, key))
        demo = groups[proto]["demo"]
        src = fragment_code(demo) if demo["kind"] == "frag" else py_count(demo["py"])
        lessons.extend(pack_unit(f"2.{'ABC'.index(proto) + 1}", names[proto], html, questions, src))
    return lessons, "\n".join(item["content"] for item in lessons if item["type"] == "theory")


def pack_counts(formulas, proto, store):
    rows = []
    for index, (shown, fn, _flag) in enumerate(formulas[:10], start=1):
        answer = count_answer(fn)
        if answer <= 0:
            raise SystemExit(f"пустая формула {shown}")
        name = f"n2-{proto.lower()}-{index}.svg"
        headers, grid = blank_table(shown)
        store[name] = truth_svg(headers, grid, "Заполните столбец F")
        py = to_python(shown)
        rows.append(
            {
                "expr": shown,
                "fn": fn,
                "answer": str(answer),
                "image": name,
                "py": py,
                "kind": "count",
            }
        )
    return {
        "demo": rows[0],
        "practice": rows[1:5],
        "homework": rows[5:8],
        "control": rows[8:10],
    }


def pack_frags(frags, store):
    rows = []
    for index, task in enumerate(frags[:10], start=1):
        name = f"n2-c-{index}.svg"
        store[name] = fragment_svg(task)
        task = dict(task)
        task["image"] = name
        task["kind"] = "frag"
        task["answer"] = task["answer"]
        rows.append(task)
    return {
        "demo": rows[0],
        "practice": rows[1:5],
        "homework": rows[5:8],
        "control": rows[8:10],
    }


def row_lesson(proto, label, index, row, points, name):
    if row["kind"] == "count":
        question = (
            "Таблица всех комбинаций стоит над вопросом, столбец F пустой. "
            f"Выражение: {row['expr']}. Сколько строк, где F равно 1? Только число."
        )
        solution = (
            f"<p>Выражение: {esc(row['expr'])}.</p>"
            + filled_table(row["expr"], row["fn"])
            + "<p>Та же программа печатает ответ. Её можно открыть в интерпретаторе.</p>"
            + code(py_count(row["py"]))
        )
    else:
        question = (
            "Над вопросом фрагмент таблицы. Столбцы 1, 2 и 3 — это буквы A, B и C в неизвестном порядке. "
            f"Выражение: {row['expr']}. "
            "Запишите три буквы подряд в порядке столбцов, например abc."
        )
        solution = (
            f"<p>Выражение: {esc(row['expr'])}.</p>"
            + ol(explain_fragment(row))
            + "<p>Программа перебирает шесть перестановок и печатает подходящую.</p>"
            + code(fragment_code(row))
        )
    title = f"{label} 2.{proto} {name}, вариант {index}"
    return short(title, question, row["answer"], solution, [row["image"]], points)


def explain_fragment(row) -> list[str]:
    cols = row["cols"]
    steps = [
        f"Подставляем буквы {cols[0]}, {cols[1]}, {cols[2]} в столбцы 1, 2 и 3.",
        "В каждой строке фрагмента выражение даёт ту же F, что написана справа.",
    ]
    wrong = None
    for cand in itertools.permutations("ABC"):
        text = "".join(cand)
        if text == cols:
            continue
        for bits, value in row["fragment"]:
            env = {cand[k]: bits[k] for k in range(3)}
            got = 1 if row["fn"](env) else 0
            if got != value:
                wrong = (
                    f"Порядок {text.lower()} не подходит: в строке {' '.join(map(str, bits))} "
                    f"получается {got}, а в фрагменте стоит {value}."
                )
                break
        if wrong:
            break
    if wrong:
        steps.append(wrong)
    steps.append(f"Подходит один порядок. Ответ: {row['answer']}.")
    return steps


def check2(proto, name):
    if proto == "A":
        answers = [
            ["И истинно только когда оба значения равны 1", True],
            ["ИЛИ истинно, если хотя бы одно значение равно 1", True],
            ["Для трёх букв в полной таблице восемь строк", True],
            ["НЕ оставляет единицу единицей", False],
        ]
    elif proto == "B":
        answers = [
            ["Стрелка A → B ложна только когда A равно 1, а B равно 0", True],
            ["В остальных трёх строках стрелка истинна", True],
            ["Скобки считают раньше стрелки", True],
            ["Стрелка ложна во всех строках, где A равно 0", False],
        ]
    else:
        answers = [
            ["В фрагменте буквы над столбцами не подписаны, их надо восстановить", True],
            ["Подходит тот порядок букв, при котором F совпадает во всех строках фрагмента", True],
            ["В ответе три буквы подряд, в порядке столбцов слева направо", True],
            ["Порядок букв можно писать любой, проверка смотрит только набор", False],
        ]
    return check(
        f"Проверка 2.{proto} Что правда про приём «{name}»",
        f"Отметьте всё верное про приём «{name}».",
        answers,
        "<p>Лишний пункт противоречит таблице из теории. Остальные три верные.</p>",
    )


def radios2():
    items = [
        ("A", "Нужно заполнить всю таблицу и посчитать единицы. Стрелки в выражении нет.", "В выражении есть стрелка «если, то».", "Даны несколько строк, буквы столбцов перепутаны."),
        ("B", "В выражении есть стрелка «если, то». Считают, в скольких строках получилась единица.", "Буквы столбцов скрыты, дан только фрагмент.", "Стрелки нет, считают единицы обычного И и ИЛИ."),
        ("C", "Дан фрагмент, столбцы без букв. В ответе три буквы в порядке столбцов.", "Нужно только число единиц по полной таблице.", "Спрашивают сумму оценок из двух таблиц."),
    ]
    out = []
    for index, (proto, text, w1, w2) in enumerate(items, start=1):
        out.append(
            radio(
                f"Какой приём 2.{index}",
                "Какой приём из теории здесь главный?",
                [[text, True], [w1, False], [w2, False]],
                f"<p>Это приём {proto}.</p>",
            )
        )
    return out


def theory_lesson_2(groups, store) -> dict:
    demo_a = groups["A"]["demo"]
    demo_b = groups["B"]["demo"]
    demo_c = groups["C"]["demo"]
    store["n2-demo-a.svg"] = truth_svg(*blank_table(demo_a["expr"]), "Пример: столбец F пока пустой")
    store["n2-demo-b.svg"] = truth_svg(*blank_table(demo_b["expr"]), "Пример со стрелкой: столбец F пустой")
    store["n2-demo-c.svg"] = fragment_svg(demo_c)
    body = "\n".join(
        [
            "<h2>Что дают в задании 2</h2>",
            "<p>Дают логическое выражение. Буквы A, B и C принимают 0 или 1. Иногда на экзамене те же буквы называют x, y и z: считать нужно так же.</p>",
            "<p>Три действия и одна стрелка.</p>",
            "<ul><li><strong>И</strong>, знак ∧. Истина, только если оба условия да.</li><li><strong>ИЛИ</strong>, знак ∨. Истина, если хотя бы одно да.</li><li><strong>НЕ</strong>, знак ¬. Меняет 0 и 1 местами.</li><li><strong>Если A, то B</strong>, знак →. Ложь только в одном случае: A да, а B нет.</li></ul>",
            fig("n2-and.svg", "Таблица для И"),
            fig("n2-or.svg", "Таблица для ИЛИ"),
            fig("n2-not.svg", "Таблица для НЕ"),
            fig("n2-impl.svg", "Таблица для стрелки, ложная строка выделена"),
            "<p>Для двух букв строк четыре. Для трёх букв строк восемь: каждый новый разряд удваивает таблицу. Скобки считают первыми, потом НЕ, потом И, потом ИЛИ. Стрелку удобно сразу заменить: A → B это то же самое, что ¬A ∨ B.</p>",
            "<h2>Приём 1. Сколько единиц</h2>",
            "<p>Строят все восемь строк и считают, где результат равен 1. На картинке столбец F пустой: его заполняют сами.</p>",
            f"<p><strong>Пример.</strong> {esc(demo_a['expr'])}.</p>",
            fig("n2-demo-a.svg", "Пустая таблица примера"),
            filled_table(demo_a["expr"], demo_a["fn"]),
            "<p>Программа делает те же восемь строк. Кнопка «В интерпретатор» откроет её.</p>",
            code(py_count(demo_a["py"])),
            "<h2>Приём 2. Есть стрелка</h2>",
            "<p>Сначала вспоминают единственную ложную строку стрелки: 1 и 0. Потом считают её вместе с остальным выражением, снова по восьми строкам.</p>",
            f"<p><strong>Пример.</strong> {esc(demo_b['expr'])}.</p>",
            fig("n2-demo-b.svg", "Пустая таблица примера со стрелкой"),
            filled_table(demo_b["expr"], demo_b["fn"]),
            code(py_count(demo_b["py"])),
            "<h2>Приём 3. Буквы столбцов</h2>",
            "<p>Дают не всю таблицу, а несколько строк. Столбцы подписаны номерами, а не буквами. Нужно понять, где A, где B и где C. В ответе три буквы подряд, слева направо. Подходит только тот порядок, при котором выражение даёт написанную F в каждой строке фрагмента.</p>",
            f"<p><strong>Пример.</strong> {esc(demo_c['expr'])}. Столбцы на рисунке.</p>",
            fig("n2-demo-c.svg", "Фрагмент с неизвестными буквами"),
            ol(explain_fragment(demo_c)),
            f"<p>Ответ: <strong>{esc(demo_c['answer'])}</strong>.</p>",
            code(fragment_code(demo_c)),
            "<p>Дальше в заданиях картинка над вопросом, разбор открывается после ответа.</p>",
        ]
    )
    images = [
        "n2-and.svg",
        "n2-or.svg",
        "n2-not.svg",
        "n2-impl.svg",
        "n2-demo-a.svg",
        "n2-demo-b.svg",
        "n2-demo-c.svg",
    ]
    return {
        "type": "theory",
        "title": "Задание 2 ЕГЭ: логика",
        "content": body,
        "comment": "Три приёма: сколько единиц, стрелка, буквы столбцов.",
        "images": images,
    }


def school_svg(students, grades, title_left, title_right, highlight) -> str:
    def table_block(x, title, headers, data_rows, marked):
        col_w = [70, 150, 120]
        row_h = 32
        width = sum(col_w)
        parts = [
            f'<text x="{x}" y="28" font-size="16" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(title)}</text>'
        ]
        y0 = 40
        xx = x
        for c, head in enumerate(headers):
            parts.append(f'<rect x="{xx}" y="{y0}" width="{col_w[c]}" height="{row_h}" fill="#e0e7ff" stroke="#cbd5e1"/>')
            parts.append(
                f'<text x="{xx + 8}" y="{y0 + 21}" font-size="13" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(head)}</text>'
            )
            xx += col_w[c]
        for r, row in enumerate(data_rows):
            xx = x
            fill = "#dcfce7" if r in marked else "#ffffff"
            for c, value in enumerate(row):
                y = y0 + (r + 1) * row_h
                parts.append(f'<rect x="{xx}" y="{y}" width="{col_w[c]}" height="{row_h}" fill="{fill}" stroke="#cbd5e1"/>')
                parts.append(
                    f'<text x="{xx + 8}" y="{y + 21}" font-size="14" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">{esc(value)}</text>'
                )
                xx += col_w[c]
        return parts, width, y0 + (len(data_rows) + 1) * row_h

    left_rows = [[str(s["id"]), s["name"], f'{s["cls"]} класс'] for s in students]
    right_rows = []
    names = {s["id"]: s["name"] for s in students}
    marked_right = set()
    for i, g in enumerate(grades):
        right_rows.append([str(g["id"]), g["sub"], str(g["g"])])
        if highlight and (g["id"], g["sub"], g["g"]) in highlight:
            marked_right.add(i)
    left, w1, h1 = table_block(16, title_left, ["Номер", "Имя", "Класс"], left_rows, set())
    right, w2, h2 = table_block(16 + w1 + 28, title_right, ["Номер", "Предмет", "Оценка"], right_rows, marked_right)
    width = 16 + w1 + 28 + w2 + 16
    height = max(h1, h2) + 24
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
        + f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
        + "".join(left + right)
        + "</svg>"
    )


def link_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 150" width="520" height="150">
<rect width="520" height="150" fill="#ffffff"/>
<rect x="30" y="40" width="160" height="70" rx="10" fill="#eef2ff" stroke="#3730a3" stroke-width="2"/>
<text x="110" y="80" text-anchor="middle" font-size="16" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Ученики</text>
<rect x="330" y="40" width="160" height="70" rx="10" fill="#fff7ed" stroke="#c2410c" stroke-width="2"/>
<text x="410" y="80" text-anchor="middle" font-size="16" font-weight="700" fill="#1e1b4b" font-family="Segoe UI, Arial, sans-serif">Оценки</text>
<line x1="190" y1="75" x2="330" y2="75" stroke="#334155" stroke-width="2.5"/>
<polygon points="330,75 318,69 318,81" fill="#334155"/>
<text x="260" y="64" text-anchor="middle" font-size="13" fill="#57534e" font-family="Segoe UI, Arial, sans-serif">один номер</text>
</svg>"""


def make_schools():
    names = ["Аня", "Боря", "Ваня", "Галя", "Даша", "Егор"]
    schools = []
    for seed in range(1, 50):
        rng = random.Random(seed)
        students = [{"id": i, "name": name, "cls": rng.choice((9, 10, 11))} for i, name in enumerate(names, start=1)]
        grades = []
        for st in students:
            for sub in ("математика", "физика"):
                grades.append({"id": st["id"], "sub": sub, "g": rng.choice((3, 4, 5))})
        schools.append((students, grades))
    return schools


def count_marks(students, grades, cls, sub, mark) -> int:
    ids = {s["id"] for s in students if s["cls"] == cls}
    return sum(1 for g in grades if g["id"] in ids and g["sub"] == sub and g["g"] == mark)


def sum_marks(students, grades, cls, sub) -> int:
    ids = {s["id"] for s in students if s["cls"] == cls}
    return sum(g["g"] for g in grades if g["id"] in ids and g["sub"] == sub)


def lookup_grade(students, grades, name, sub):
    ids = [s["id"] for s in students if s["name"] == name]
    if len(ids) != 1:
        return None
    got = [g["g"] for g in grades if g["id"] == ids[0] and g["sub"] == sub]
    if len(got) != 1:
        return None
    return got[0]


def explain_count(students, grades, cls, sub, mark) -> str:
    rows = []
    for st in students:
        if st["cls"] != cls:
            continue
        for g in grades:
            if g["id"] == st["id"] and g["sub"] == sub and g["g"] == mark:
                rows.append(f"{st['name']} (номер {st['id']})")
    if not rows:
        return "Под условия не подошёл никто."
    return "Подошли: " + ", ".join(rows) + "."


def explain_sum(students, grades, cls, sub) -> str:
    parts = []
    for st in students:
        if st["cls"] != cls:
            continue
        for g in grades:
            if g["id"] == st["id"] and g["sub"] == sub:
                parts.append(f"{st['name']} — {g['g']}")
    return "Оценки: " + ", ".join(parts) + "."


def py_school(students, grades, body_lines: str) -> str:
    st = ",\n    ".join(repr((s["id"], s["name"], s["cls"])) for s in students)
    gr = ",\n    ".join(repr((g["id"], g["sub"], g["g"])) for g in grades)
    return (
        "students = [\n    "
        + st
        + "\n]\ngrades = [\n    "
        + gr
        + "\n]\n"
        + body_lines
    )


def build_task3(store: dict[str, str]):
    store["n3-link.svg"] = link_svg()
    pools = {"A": [], "B": [], "C": []}
    for students, grades in make_schools():
        for cls, sub, mark in itertools.product((9, 10, 11), ("математика", "физика"), (3, 4, 5)):
            answer = count_marks(students, grades, cls, sub, mark)
            if answer <= 0:
                continue
            pools["A"].append(
                {
                    "students": students,
                    "grades": grades,
                    "answer": str(answer),
                    "question": f"Сколько учеников {cls} класса имеют по предмету «{sub}» оценку {mark}? Только число.",
                    "solution": (
                        f"<p>Берём учеников {cls} класса и смотрим у них предмет «{sub}».</p><p>{esc(explain_count(students, grades, cls, sub, mark))}</p>"
                        f"<p>Ответ: <strong>{answer}</strong>.</p>"
                    ),
                    "py": py_school(
                        students,
                        grades,
                        "ids = {num for num, name, cls in students if cls == "
                        + str(cls)
                        + "}\n"
                        + f"print(sum(1 for num, sub, g in grades if num in ids and sub == {sub!r} and g == {mark}))\n",
                    ),
                }
            )
        for cls, sub in itertools.product((9, 10, 11), ("математика", "физика")):
            answer = sum_marks(students, grades, cls, sub)
            if answer <= 0:
                continue
            pools["B"].append(
                {
                    "students": students,
                    "grades": grades,
                    "answer": str(answer),
                    "question": f"Чему равна сумма оценок по предмету «{sub}» у учеников {cls} класса? Только число.",
                    "solution": (
                        f"<p>{esc(explain_sum(students, grades, cls, sub))}</p><p>Ответ: <strong>{answer}</strong>.</p>"
                    ),
                    "py": py_school(
                        students,
                        grades,
                        "ids = {num for num, name, cls in students if cls == "
                        + str(cls)
                        + "}\n"
                        + f"print(sum(g for num, sub, g in grades if num in ids and sub == {sub!r}))\n",
                    ),
                }
            )
        for st in students:
            for sub in ("математика", "физика"):
                answer = lookup_grade(students, grades, st["name"], sub)
                if answer is None:
                    continue
                pools["C"].append(
                    {
                        "students": students,
                        "grades": grades,
                        "answer": str(answer),
                        "question": f"Какая оценка по предмету «{sub}» у ученика {st['name']}? Только число.",
                        "solution": (
                            f"<p>У {esc(st['name'])} номер {st['id']}. "
                            f"В таблице оценок в строке этого номера и предмета «{sub}» стоит {answer}.</p>"
                            f"<p>Ответ: <strong>{answer}</strong>.</p>"
                        ),
                        "py": py_school(
                            students,
                            grades,
                            f"num = [n for n, name, cls in students if name == {st['name']!r}][0]\n"
                            + f"print([g for n, sub, g in grades if n == num and sub == {sub!r}][0])\n",
                        ),
                    }
                )
    picked = {}
    used_tables = set()
    for proto in "ABC":
        chosen = []
        seen_answers = Counter()
        for row in pools[proto]:
            key = tuple((s["id"], s["cls"]) for s in row["students"]) + tuple(
                (g["id"], g["sub"], g["g"]) for g in row["grades"]
            )
            if key in used_tables or seen_answers[row["answer"]] >= 4:
                continue
            used_tables.add(key)
            seen_answers[row["answer"]] += 1
            chosen.append(row)
            if len(chosen) == 10:
                break
        if len(chosen) < 10:
            raise SystemExit(f"задача 3, приём {proto}: только {len(chosen)}")
        picked[proto] = {
            "demo": chosen[0],
            "practice": chosen[1:5],
            "homework": chosen[5:8],
            "control": chosen[8:10],
        }
    demo_images = []
    for proto in "ABC":
        demo = picked[proto]["demo"]
        name = f"n3-demo-{proto.lower()}.svg"
        marked = mark_set(demo) if proto == "A" else None
        store[name] = school_svg(demo["students"], demo["grades"], "Ученики", "Оценки", marked)
        demo_images.append(name)
        demo["image"] = name
    body = theory_task3(picked)
    sections = h2_parts(body)
    if len(sections) != 4:
        raise SystemExit(f"теория 3: частей {len(sections)}")
    contents = [sections[0] + "\n" + sections[1], sections[2], sections[3]]
    names = {
        "A": "Сколько строк",
        "B": "Сумма оценок",
        "C": "Одна оценка",
    }
    lessons = []
    for proto, html in zip("ABC", contents):
        questions = []
        for key, points in (("practice", 3), ("homework", 3)):
            for index, row in enumerate(picked[proto][key], start=1):
                questions.append(school_lesson(proto, key, index, row, points, key, store))
        lessons.extend(
            pack_unit(
                f"3.{'ABC'.index(proto) + 1}",
                names[proto],
                html,
                questions,
                picked[proto]["demo"]["py"],
            )
        )
    return lessons, "\n".join(item["content"] for item in lessons if item["type"] == "theory")


def mark_set(row):
    return None


def school_lesson(proto, label, index, row, points, name, store):
    image = f"n3-{proto.lower()}-{label[:1].lower()}{index}.svg"
    store[image] = school_svg(row["students"], row["grades"], "Ученики", "Оценки", None)
    solution = row["solution"] + "<p>Программа ниже печатает тот же ответ.</p>" + code(row["py"])
    return short(
        f"{label} 3.{proto} {name}, вариант {index}",
        "Две таблицы стоят над вопросом. Связь по номеру ученика. " + row["question"],
        row["answer"],
        solution,
        [image],
        points,
    )


def check3(proto, name):
    if proto == "A":
        answers = [
            ["Сначала отбирают учеников нужного класса по левой таблице", True],
            ["Потом у этих номеров смотрят предмет и оценку справа", True],
            ["В ответ пишут, сколько таких строк нашлось", True],
            ["Считают всех учеников школы, фильтр не нужен", False],
        ]
    elif proto == "B":
        answers = [
            ["Складывают сами оценки, а не число учеников", True],
            ["Чужой предмет в сумму не входит", True],
            ["Номер связывает имя в левой таблице и оценку в правой", True],
            ["В сумму берут лучшую оценку по всей школе", False],
        ]
    else:
        answers = [
            ["По имени находят номер ученика", True],
            ["По этому номеру и предмету читают одну оценку", True],
            ["Если предмет другой, строку пропускают", True],
            ["Оценка написана прямо рядом с именем, номер не нужен", False],
        ]
    return check(
        f"Проверка 3.{proto} Что правда про приём «{name}»",
        f"Отметьте всё верное про приём «{name}».",
        answers,
        "<p>Три пункта совпадают со связью таблиц в теории. Четвёртый — нет.</p>",
    )


def radios3():
    items = [
        (
            "Спросили, сколько учеников 9 класса имеют пятёрку по математике.",
            "Сколько строк подходят под условия",
            "Сумма оценок",
            "Одна оценка по имени",
        ),
        (
            "Спросили, чему равна сумма оценок по физике у десятиклассников.",
            "Сумма оценок",
            "Сколько таких учеников",
            "Одна оценка по имени",
        ),
        (
            "Спросили, какая оценка по физике у Даши.",
            "Одна оценка по имени",
            "Сколько человек получило пятёрку",
            "Сумма всех оценок класса",
        ),
    ]
    out = []
    for index, (situation, good, w1, w2) in enumerate(items, start=1):
        out.append(
            radio(
                f"Какой приём 3.{index}",
                situation + " Какой это приём?",
                [[good, True], [w1, False], [w2, False]],
                "<p>Смотрите, что просят в ответ: число строк, сумму или одну оценку.</p>",
            )
        )
    return out


def theory_task3(picked) -> str:
    a = picked["A"]["demo"]
    b = picked["B"]["demo"]
    c = picked["C"]["demo"]
    return "\n".join(
        [
            "<h2>Что дают в задании 3</h2>",
            "<p>Две таблицы про одну школу. В первой ученик, его номер и класс. Во второй номер, предмет и оценка. Имени во второй таблице нет. Связь одна: номер ученика.</p>",
            fig("n3-link.svg", "Две таблицы связаны номером"),
            "<p>Чужой номер не смотрят. Если спрашивают девятый класс и математику, строка десятого класса не считается, даже если оценка та же.</p>",
            "<h2>Приём 1. Сколько строк</h2>",
            "<p>Нужно число учеников, у которых совпали и класс, и предмет, и оценка.</p>",
            f"<p><strong>Пример.</strong> {esc(a['question'])}</p>",
            fig(a["image"], "Таблицы примера: сколько строк"),
            a["solution"],
            code(a["py"]),
            "<h2>Приём 2. Сумма оценок</h2>",
            "<p>Тех же учеников отбирают по классу, но в ответ складывают оценки, а не считают людей. Две пятёрки дают 10, а не 2.</p>",
            f"<p><strong>Пример.</strong> {esc(b['question'])}</p>",
            fig(b["image"], "Таблицы примера: сумма"),
            b["solution"],
            code(b["py"]),
            "<h2>Приём 3. Одна оценка</h2>",
            "<p>Имя ищут слева и запоминают номер. Справа оставляют строку с этим номером и нужным предметом. В ответе одна цифра.</p>",
            f"<p><strong>Пример.</strong> {esc(c['question'])}</p>",
            fig(c["image"], "Таблицы примера: одна оценка"),
            c["solution"],
            code(c["py"]),
            "<p>Кнопка «В интерпретатор» над программой откроет код. Дальше таблицы стоят над вопросом, разбор — после ответа.</p>",
        ]
    )


def dump_pack(folder: str, zip_name: str, ready_name: str, manifest: dict, lessons: list[dict], files: dict[str, str], body: str):
    titles = [lesson["title"] for lesson in lessons]
    if len(titles) != len(set(titles)):
        raise SystemExit(f"{folder}: одинаковые названия")
    units: dict[str, int] = {}
    for lesson in lessons:
        match = re.match(r"^(\d+\.\d+)\b", lesson["title"])
        key = match.group(1) if match else lesson["title"]
        units[key] = units.get(key, 0) + 1
    too_big = [f"{key}={count}" for key, count in units.items() if count > 10]
    if too_big:
        raise SystemExit(f"{folder}: в уроке больше 10 квадратиков: {', '.join(too_big)}")
    referenced: list[str] = []
    for lesson in lessons:
        for name in lesson.get("images") or []:
            if name not in referenced:
                referenced.append(name)
    missing = [name for name in referenced if name not in files]
    if missing:
        raise SystemExit(f"{folder}: нет файлов {missing[:6]}")
    files = {name: files[name] for name in referenced}
    pack = ROOT / folder
    img = pack / "images"
    img.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        if not name.startswith(folder.replace("ege-", "")[:0]):
            pass
        (img / name).write_text(text, encoding="utf-8")
    (pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {
        "meta": {
            "topic": manifest["module_title"],
            "images_dir": "images/",
            "scheme": {
                "theory": sum(1 for x in lessons if x["type"] == "theory"),
                "checkbox": sum(1 for x in lessons if x["type"] == "checkbox"),
                "radio": sum(1 for x in lessons if x["type"] == "radio"),
                "short_answer": sum(1 for x in lessons if x["type"] == "short_answer"),
                "total": len(lessons),
            },
        },
        "lessons": lessons,
    }
    (pack / "questions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = wrap_page(body, manifest["module_title"])
    (pack / "theory.html").write_text(page, encoding="utf-8")
    (pack / "preview.html").write_text(page, encoding="utf-8")
    zip_path = ROOT / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(pack / "manifest.json", "manifest.json")
        zf.write(pack / "questions.json", "questions.json")
        for name in sorted(files):
            zf.write(img / name, f"images/{name}")
    READY.mkdir(parents=True, exist_ok=True)
    target = READY / ready_name
    target.write_bytes(zip_path.read_bytes())
    print(folder, payload["meta"]["scheme"], "images", len(files), "zip", zip_name)


def self_check():
    letters = "ABC"
    edges = [("A", "B"), ("B", "C")]
    perm = {"A": 2, "B": 1, "C": 3}
    if deduce(letters, edges, perm) is not None:
        raise SystemExit("симметричный путь не должен сходиться однозначно")
    py = to_python("(A → B) ∧ C")
    if not eval(py, {}, {"A": 1, "B": 1, "C": 1}):
        raise SystemExit(f"стрелка не считается: {py}")
    if eval(py, {}, {"A": 1, "B": 0, "C": 1}):
        raise SystemExit(f"ложная стрелка прошла: {py}")
    py_or = to_python("¬A → (B ∨ C)")
    if eval(py_or, {}, {"A": 0, "B": 0, "C": 0}):
        raise SystemExit(py_or)
    if not eval(py_or, {}, {"A": 1, "B": 0, "C": 0}):
        raise SystemExit(py_or)
    assert count_marks(
        [{"id": 1, "cls": 9}, {"id": 2, "cls": 10}],
        [{"id": 1, "sub": "математика", "g": 5}, {"id": 2, "sub": "математика", "g": 5}],
        9,
        "математика",
        5,
    ) == 1


def main():
    self_check()
    store1: dict[str, str] = {}
    lessons1, body1 = build_task1(store1)
    dump_pack(
        "ege-n1",
        "ege-n1-import.zip",
        "01-ege-n1-import.zip",
        {
            "pack_id": "ege-n1-questions",
            "course_slug": "ege-informatika",
            "module_title": "1-й урок ЕГЭ: Графы",
            "create_module": True,
            "replace_missing": True,
            "module_description": "Три урока: 1.1 два номера, 1.2 сумма длин, 1.3 сосед тупика.",
        },
        lessons1,
        {k: v for k, v in store1.items() if k.startswith("n1-")},
        body1,
    )
    store2: dict[str, str] = {}
    lessons2, body2 = build_task2(store2)
    for row in lessons2:
        if row["type"] != "short_answer":
            continue
        if row["images"] and row["images"][0].startswith("n2-c"):
            src = row["solution_text"]
            if "<pre><code>" not in src:
                raise SystemExit("нет программы во фрагменте")
        printed_ok = True
    dump_pack(
        "ege-n2",
        "ege-n2-import.zip",
        "02-ege-n2-import.zip",
        {
            "pack_id": "ege-n2-questions",
            "course_slug": "ege-informatika",
            "module_title": "Задание 2 ЕГЭ: Логика",
            "create_module": True,
            "replace_missing": True,
            "module_description": "Три урока: 2.1 сколько единиц, 2.2 стрелка, 2.3 буквы столбцов.",
        },
        lessons2,
        store2,
        body2,
    )
    store3: dict[str, str] = {}
    lessons3, body3 = build_task3(store3)
    dump_pack(
        "ege-n3",
        "ege-n3-import.zip",
        "03-ege-n3-import.zip",
        {
            "pack_id": "ege-n3-questions",
            "course_slug": "ege-informatika",
            "module_title": "Задание 3 ЕГЭ: Базы данных",
            "create_module": True,
            "replace_missing": True,
            "module_description": "Три урока: 3.1 сколько строк, 3.2 сумма оценок, 3.3 одна оценка.",
        },
        lessons3,
        store3,
        body3,
    )
    verify_programs(lessons2, lessons3)


def verify_programs(lessons2, lessons3):
    import contextlib
    import io
    import re

    def run(src: str) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(src, "<lesson>", "exec"), {})
        return buf.getvalue().strip()

    for lesson in lessons2 + lessons3:
        if lesson["type"] != "short_answer":
            continue
        match = re.search(r"<pre><code>(.*)</code></pre>", lesson["solution_text"], re.S)
        if not match:
            raise SystemExit(f"нет кода: {lesson['title']}")
        src = html.unescape(match.group(1))
        got = run(src)
        if got != str(lesson["correct_answer"]):
            raise SystemExit(f"{lesson['title']}: программа {got}, ответ {lesson['correct_answer']}")


if __name__ == "__main__":
    main()
