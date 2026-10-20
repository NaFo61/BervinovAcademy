# -*- coding: utf-8 -*-
"""Собрать урок 24: шесть прототипов, практика, домашка, контрольная.

Каждый числовой ответ считается программой прототипа и ещё раз полным перебором.
Если два способа разошлись, файл не записывается.
"""

from __future__ import annotations

import html
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK = ROOT / "ege-n24"
READY = ROOT / "к-импорту"

ODD = set("13579")
EVEN = set("02468")
DIGITS = set("0123456789")


def esc(text) -> str:
    return html.escape(str(text), quote=False)


def code(src: str) -> str:
    return "<pre><code>" + esc(src.strip("\n")) + "</code></pre>"


def answer_box(text: str) -> str:
    return f'<div class="answer">{text}</div>'


# --- прототипы ----------------------------------------------------------------


def marker_max(s: str, marker: str, need: int, pred) -> int:
    best = 0
    for part in s.split(marker)[1:]:
        got = 0
        for i, ch in enumerate(part):
            if pred(ch):
                got += 1
            if got == need + 1:
                best = max(best, i + 1)
                break
        else:
            if got == need:
                best = max(best, len(part) + 1)
    return best


def even_start_max(s: str, letter: str, need: int) -> int:
    best = 0
    i = 0
    n = len(s)
    while i < n:
        if s[i] in EVEN:
            got = 0
            j = i + 1
            while j < n and s[j] not in EVEN:
                if s[j] == letter:
                    got += 1
                    if got == need + 1:
                        break
                j += 1
            if got >= need:
                best = max(best, j - i)
            i = j if j > i else i + 1
        else:
            i += 1
    return best


def _pref_pat(s: str, pat: str) -> list[int]:
    pref = [0]
    plen = len(pat)
    for i in range(len(s)):
        pref.append(pref[-1] + (s[i : i + plen] == pat))
    return pref


def window_max(s, letter, need_letter, pat, need_pat) -> int:
    pos = [i for i, ch in enumerate(s) if ch == letter]
    if len(pos) < need_letter:
        return 0
    pref = _pref_pat(s, pat)
    plen = len(pat)
    best = 0
    n = len(s)
    for i in range(len(pos) - need_letter + 1):
        left = 0 if i == 0 else pos[i - 1] + 1
        right = n - 1 if i + need_letter >= len(pos) else pos[i + need_letter] - 1
        hi = right - plen + 1
        count = pref[hi + 1] - pref[left] if hi >= left else 0
        if count >= need_pat:
            best = max(best, right - left + 1)
    return best


def window_min(s, letter, need_letter, pat, need_pat) -> int:
    pos = [i for i, ch in enumerate(s) if ch == letter]
    if len(pos) < need_letter or need_pat < 1:
        return 0
    n = len(s)
    plen = len(pat)
    pats = [i for i in range(n - plen + 1) if s[i : i + plen] == pat]
    best = None
    for i in range(len(pos) - need_letter + 1):
        left_bound = 0 if i == 0 else pos[i - 1] + 1
        right_bound = (
            n - 1 if i + need_letter >= len(pos) else pos[i + need_letter] - 1
        )
        core_l = pos[i]
        core_r = pos[i + need_letter - 1]
        inside = [
            p for p in pats if left_bound <= p and p + plen - 1 <= right_bound
        ]
        if len(inside) < need_pat:
            continue
        for a in range(len(inside) - need_pat + 1):
            b = a + need_pat - 1
            left = min(core_l, inside[a])
            right = max(core_r, inside[b] + plen - 1)
            if left < left_bound or right > right_bound:
                continue
            length = right - left + 1
            best = length if best is None else min(best, length)
    return 0 if best is None else best


def end_with_max(s, pat, need_pat, letter, need_letter) -> int:
    plen = len(pat)
    pos = [i for i in range(len(s) - plen + 1) if s[i : i + plen] == pat]
    if len(pos) < need_pat:
        return 0
    pref = [0]
    for ch in s:
        pref.append(pref[-1] + (ch == letter))
    best = 0
    for j in range(need_pat - 1, len(pos)):
        right = pos[j] + plen - 1
        first = j - need_pat + 1
        left = 0 if first == 0 else pos[first - 1] + plen
        if pref[right + 1] - pref[left] >= need_letter:
            best = max(best, right - left + 1)
    return best


def base_len(s: str, alphabet: str = "0123456789ABCD") -> int:
    allowed = set(alphabet)
    even_last = set("02468AC") & allowed
    cleaned = "".join(ch if ch in allowed else " " for ch in s)
    best = 0
    for tok in cleaned.split():
        while tok and tok[-1] not in even_last:
            tok = tok[:-1]
        tok = tok.lstrip("0")
        best = max(best, len(tok))
    return best


def alt_max(s: str, letters: str, digits: str) -> int:
    if not s:
        return 0
    letters, digits = set(letters), set(digits)
    best = cur = 1
    for i in range(1, len(s)):
        a, b = s[i - 1], s[i]
        ok = (a in letters and b in digits) or (a in digits and b in letters)
        if ok:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _pair_pos(s: str, pair: str) -> list[int]:
    return [i for i in range(len(s) - 1) if s[i : i + 2] == pair]


def pair_max(s: str, pair: str, k: int, exactly: bool) -> int:
    pos = _pair_pos(s, pair)
    if len(pos) < k:
        return 0 if exactly else len(s)
    if not exactly and len(pos) <= k:
        return len(s)
    best = 0
    for i in range(len(pos) - k + 1):
        left = 0 if i == 0 else pos[i - 1] + 1
        right = len(s) - 1 if i + k >= len(pos) else pos[i + k]
        best = max(best, right - left + 1)
    return best


def pair_min(s: str, pair: str, k: int) -> int:
    pos = _pair_pos(s, pair)
    if len(pos) < k:
        return 0
    return min(pos[i + k - 1] + 2 - pos[i] for i in range(len(pos) - k + 1))


def expr_max(s: str, digits: str) -> int:
    import re

    nz = "".join(d for d in digits if d != "0")
    num = rf"(?:0|[{nz}][{digits}]*)"
    expr = rf"{num}(?:[-*]{num})*"
    found = [len(m.group()) for m in re.finditer(expr, s)]
    return max(found, default=0)


# --- полный перебор, короткие учебные строки ---------------------------------


def brute_marker(s, marker, need, pred) -> int:
    best = 0
    for i, ch in enumerate(s):
        if ch != marker:
            continue
        got = 0
        for j in range(i + 1, len(s) + 1):
            if marker in s[i + 1 : j]:
                break
            if pred(s[j - 1]):
                got += 1
            if got > need:
                break
            if got == need:
                best = max(best, j - i)
    return best


def brute_even(s, letter, need) -> int:
    best = 0
    for i, ch in enumerate(s):
        if ch not in EVEN:
            continue
        got = 0
        ok = True
        for j in range(i + 1, len(s) + 1):
            cur = s[j - 1]
            if j - 1 != i and cur in EVEN:
                break
            if cur == letter:
                got += 1
            if got > need:
                break
            if got == need and ok:
                best = max(best, j - i)
    return best


def _pat_count(frag: str, pat: str) -> int:
    plen = len(pat)
    return sum(1 for i in range(len(frag) - plen + 1) if frag[i : i + plen] == pat)


def brute_window(s, letter, need_letter, pat, need_pat, mode) -> int:
    best = None
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n + 1):
            frag = s[i:j]
            if frag.count(letter) != need_letter:
                continue
            if _pat_count(frag, pat) < need_pat:
                continue
            length = j - i
            if mode == "max":
                best = length if best is None else max(best, length)
            else:
                best = length if best is None else min(best, length)
    return 0 if best is None else best


def brute_end(s, pat, need_pat, letter, need_letter) -> int:
    plen = len(pat)
    best = 0
    for right in range(plen, len(s) + 1):
        if s[right - plen : right] != pat:
            continue
        for left in range(right):
            frag = s[left:right]
            if _pat_count(frag, pat) == need_pat and frag.count(letter) >= need_letter:
                best = max(best, right - left)
    return best


def brute_base(s, alphabet="0123456789ABCD") -> int:
    allowed = set(alphabet)
    even_last = set("02468AC") & allowed
    cleaned = "".join(ch if ch in allowed else " " for ch in s)
    best_val = -1
    best_len = 0
    for tok in cleaned.split():
        t = tok
        while t and t[-1] not in even_last:
            t = t[:-1]
        if not t:
            continue
        t = t.lstrip("0") or "0"
        val = int(t, 14)
        length = len(t)
        if val > best_val:
            best_val = val
            best_len = length
    return best_len


def brute_alt(s, letters, digits) -> int:
    letters, digits = set(letters), set(digits)
    best = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            frag = s[i:j]
            ok = True
            for k in range(len(frag) - 1):
                a, b = frag[k], frag[k + 1]
                good = (a in letters and b in digits) or (a in digits and b in letters)
                if not good:
                    ok = False
                    break
            if ok:
                best = max(best, len(frag))
    return best


def brute_pair(s, pair, k, mode) -> int:
    best = None
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n + 1):
            frag = s[i:j]
            count = sum(1 for t in range(len(frag) - 1) if frag[t : t + 2] == pair)
            good = count == k if mode != "atmost" else count <= k
            if not good:
                continue
            length = j - i
            if mode == "min":
                best = length if best is None else min(best, length)
            else:
                best = length if best is None else max(best, length)
    return 0 if best is None else best


def brute_expr(s, digits) -> int:
    import re

    digs = set(digits)
    nz = {d for d in digits if d != "0"}

    def is_num(tok: str) -> bool:
        if not tok or any(c not in digs for c in tok):
            return False
        if tok == "0":
            return True
        return tok[0] in nz

    best = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            frag = s[i:j]
            if frag[0] in "-*" or frag[-1] in "-*":
                continue
            parts = re.split(r"([-*])", frag)
            if len(parts) % 2 == 0:
                continue
            ok = True
            for idx, part in enumerate(parts):
                if idx % 2 == 0:
                    ok = is_num(part)
                else:
                    ok = part in "-*"
                if not ok:
                    break
            if ok:
                best = max(best, len(frag))
    return best


PREDS = {
    "odd": (lambda ch: ch in ODD, "нечётная цифра"),
    "even": (lambda ch: ch in EVEN, "чётная цифра"),
    "digit": (lambda ch: ch in DIGITS, "цифра"),
}


def solve(task: dict) -> int:
    kind = task["kind"]
    s = task["s"]
    if kind == "marker":
        pred = PREDS[task["pred"]][0]
        return marker_max(s, task["marker"], task["need"], pred)
    if kind == "even_start":
        return even_start_max(s, task["letter"], task["need"])
    if kind == "win_max":
        return window_max(s, task["letter"], task["need_l"], task["pat"], task["need_p"])
    if kind == "win_min":
        return window_min(s, task["letter"], task["need_l"], task["pat"], task["need_p"])
    if kind == "endpat":
        return end_with_max(s, task["pat"], task["need_p"], task["letter"], task["need_l"])
    if kind == "base":
        return base_len(s)
    if kind == "alt":
        return alt_max(s, task["letters"], task["digits"])
    if kind == "pair_max":
        return pair_max(s, task["pair"], task["k"], task["exactly"])
    if kind == "pair_min":
        return pair_min(s, task["pair"], task["k"])
    if kind == "expr":
        return expr_max(s, task["digits"])
    raise KeyError(kind)


def brute(task: dict) -> int:
    kind = task["kind"]
    s = task["s"]
    if kind == "marker":
        return brute_marker(s, task["marker"], task["need"], PREDS[task["pred"]][0])
    if kind == "even_start":
        return brute_even(s, task["letter"], task["need"])
    if kind == "win_max":
        return brute_window(s, task["letter"], task["need_l"], task["pat"], task["need_p"], "max")
    if kind == "win_min":
        return brute_window(s, task["letter"], task["need_l"], task["pat"], task["need_p"], "min")
    if kind == "endpat":
        return brute_end(s, task["pat"], task["need_p"], task["letter"], task["need_l"])
    if kind == "base":
        return brute_base(s)
    if kind == "alt":
        return brute_alt(s, task["letters"], task["digits"])
    if kind == "pair_max":
        mode = "exact" if task["exactly"] else "atmost"
        return brute_pair(s, task["pair"], task["k"], mode)
    if kind == "pair_min":
        return brute_pair(s, task["pair"], task["k"], "min")
    if kind == "expr":
        return brute_expr(s, task["digits"])
    raise KeyError(kind)


def positions_table(s: str) -> str:
    heads = "".join(f"<th>{esc(ch)}</th>" for ch in s)
    nums = "".join(f"<td>{i}</td>" for i in range(1, len(s) + 1))
    return (
        '<div class="table-scroll"><table class="code-table">'
        f"<tr><th class='left'>символ</th>{heads}</tr>"
        f"<tr><th class='left'>номер</th>{nums}</tr>"
        "</table></div>"
        "<p>Номера здесь с единицы, как пальцем по строке. "
        "В программе первый символ имеет номер 0. На ответ это не влияет: "
        "мы считаем длину, а не номер.</p>"
    )


def ol(items: list[str]) -> str:
    body = "".join(f"<li>{item}</li>" for item in items)
    return f"<ol>{body}</ol>"


def short(title, question, correct, solution, points=3) -> dict:
    return {
        "type": "short_answer",
        "title": title,
        "question_text": question,
        "correct_answer": str(correct),
        "answer_normalize": "strip_casefold",
        "points": points,
        "solution_text": solution,
    }


def check(title, question, answers, solution, points=4) -> dict:
    return {
        "type": "checkbox",
        "title": title,
        "question_text": question,
        "points": points,
        "answers": answers,
        "solution_text": solution,
    }


def radio(title, question, answers, solution, points=3) -> dict:
    return {
        "type": "radio",
        "title": title,
        "question_text": question,
        "points": points,
        "answers": answers,
        "solution_text": solution,
    }


FILE_HINT = (
    "Скачайте файл к заданию в блоке «Материалы». "
    "В файле одна строка, как 24.txt на экзамене. "
    "Кнопка под файлом открывает интерпретатор и подставляет эту строку в программу. "
)


def ask_text(task: dict) -> str:
    kind = task["kind"]
    if kind == "marker":
        what = PREDS[task["pred"]][1]
        return (
            f"Найдите самый длинный кусок, который начинается с {task['marker']}, "
            f"других букв {task['marker']} в нём нет, а символов «{what}» ровно {task['need']}. "
            "В ответе длина этого куска. Только число."
        )
    if kind == "even_start":
        return (
            f"Найдите самый длинный кусок. Он начинается с чётной цифры, "
            f"других чётных цифр в нём нет, букв {task['letter']} ровно {task['need']}. "
            "В ответе длина. Только число."
        )
    if kind == "win_max":
        return (
            f"Найдите самый длинный кусок, в котором буква {task['letter']} встречается "
            f"ровно {task['need_l']} раз, а подстрока {task['pat']} — не меньше {task['need_p']} раз. "
            "В ответе длина. Только число."
        )
    if kind == "win_min":
        return (
            f"Найдите самый короткий кусок, в котором буква {task['letter']} встречается "
            f"ровно {task['need_l']} раз, а подстрока {task['pat']} — не меньше {task['need_p']} раз. "
            "В ответе длина. Только число."
        )
    if kind == "endpat":
        return (
            f"Найдите самый длинный кусок, который заканчивается на {task['pat']}, "
            f"эта подстрока встречается в нём ровно {task['need_p']} раз, "
            f"а буква {task['letter']} — не меньше {task['need_l']} раз. "
            "В ответе длина. Только число."
        )
    if kind == "base":
        return (
            "Найдите запись самого большого чётного 14-ричного числа. "
            "Цифры: 0–9 и A, B, C, D. Чётное кончается на 0, 2, 4, 6, 8, A или C. "
            "Нули впереди не считаются. В ответе количество цифр. Только число."
        )
    if kind == "alt":
        return (
            f"Буквы: {task['letters']}. Цифры: {task['digits']}. "
            "Найдите самый длинный кусок, где буква не стоит рядом с буквой, "
            "а цифра — рядом с цифрой. В ответе длина. Только число."
        )
    if kind == "pair_max":
        how = "ровно" if task["exactly"] else "не больше"
        return (
            f"Найдите самый длинный кусок, в котором пара {task['pair']} "
            f"(именно в этом порядке) встречается {how} {task['k']} раз. "
            "В ответе длина. Только число."
        )
    if kind == "pair_min":
        return (
            f"Найдите самый короткий кусок, в котором пара {task['pair']} "
            f"встречается ровно {task['k']} раз. В ответе длина. Только число."
        )
    if kind == "expr":
        shown = ", ".join(task["digits"])
        return (
            f"Символы: цифры {shown} и знаки «−» и «*». "
            "Найдите самый длинный правильный пример: числа без нулей впереди, "
            "ноль только как 0, знаки только между числами, два знака подряд нельзя. "
            "В ответе длина. Только число."
        )
    raise KeyError(kind)


def trace(task: dict, value: int) -> list[str]:
    s = task["s"]
    kind = task["kind"]
    steps = [f"Строка <strong>{esc(s)}</strong>, в ней {len(s)} символов."]
    if kind == "marker":
        name = PREDS[task["pred"]][1]
        pred = PREDS[task["pred"]][0]
        parts = s.split(task["marker"])
        steps.append(
            f"Режем по букве {esc(task['marker'])}. "
            f"Куски: {esc(str(parts))}."
        )
        steps.append(
            f"Кусок до первой {esc(task['marker'])} не начинается с неё, его пропускаем."
        )
        best = 0
        best_piece = ""
        for index, part in enumerate(parts[1:], start=1):
            got = 0
            cut = None
            for i, ch in enumerate(part):
                if pred(ch):
                    got += 1
                if got == task["need"] + 1:
                    cut = i
                    break
            if cut is not None:
                length = cut + 1
                piece = task["marker"] + part[:cut]
                steps.append(
                    f"Кусок {index}: «{esc(task['marker'] + part)}». "
                    f"Символов «{esc(name)}» стало {task['need'] + 1} "
                    f"на «{esc(part[cut])}». Лишний не берём. "
                    f"Остаётся «{esc(piece)}», длина {length}."
                )
            elif got == task["need"]:
                length = len(part) + 1
                piece = task["marker"] + part
                steps.append(
                    f"Кусок {index}: «{esc(piece)}» содержит ровно {task['need']}. "
                    f"Длина {length}."
                )
            else:
                length = 0
                piece = ""
                steps.append(
                    f"Кусок {index}: «{esc(task['marker'] + part)}» содержит {got}. "
                    f"Нужно {task['need']}. Этот кусок не подходит."
                )
            if length > best:
                best = length
                best_piece = piece
        steps.append(
            f"Рекорд {best}. Кусок «{esc(best_piece)}»."
        )
    elif kind == "even_start":
        steps.append(
            f"Ищем куски с чётной цифры. Внутри ровно {task['need']} букв "
            f"{esc(task['letter'])} и больше ни одной чётной цифры."
        )
        i = 0
        best = 0
        while i < len(s):
            if s[i] in EVEN:
                got = 0
                j = i + 1
                while j < len(s) and s[j] not in EVEN:
                    if s[j] == task["letter"]:
                        got += 1
                        if got == task["need"] + 1:
                            break
                    j += 1
                piece = s[i:j]
                if got >= task["need"]:
                    best = max(best, j - i)
                    steps.append(
                        f"Старт на «{esc(s[i])}» (номер {i + 1}). "
                        f"Кусок «{esc(piece)}», букв {esc(task['letter'])} "
                        f"в зачёт пошло {min(got, task['need'])}, длина {j - i}."
                    )
                else:
                    steps.append(
                        f"Старт на «{esc(s[i])}»: букв {esc(task['letter'])} только {got}. Мало."
                    )
                i = j if j > i else i + 1
            else:
                i += 1
        steps.append(f"Самая большая длина {best}.")
    elif kind in ("win_max", "win_min"):
        pos = [i for i, ch in enumerate(s) if ch == task["letter"]]
        human = [p + 1 for p in pos]
        steps.append(
            f"Буква {esc(task['letter'])} стоит на номерах {human}. "
            f"Нужно ровно {task['need_l']} таких букв."
        )
        plen = len(task["pat"])
        n = len(s)
        best = None
        for i in range(len(pos) - task["need_l"] + 1):
            group = pos[i : i + task["need_l"]]
            group_h = [p + 1 for p in group]
            if kind == "win_max":
                left = 0 if i == 0 else pos[i - 1] + 1
                right = n - 1 if i + task["need_l"] >= len(pos) else pos[i + task["need_l"]] - 1
                hi = right - plen + 1
                count = 0 if hi < left else sum(
                    1 for t in range(left, hi + 1) if s[t : t + plen] == task["pat"]
                )
                length = right - left + 1
                piece = s[left : right + 1]
                ok = count >= task["need_p"]
                steps.append(
                    f"Буквы на номерах {group_h}. Кусок «{esc(piece)}», длина {length}, "
                    f"подстрок {esc(task['pat'])} внутри {count}. "
                    + ("Подходит." if ok else "Подстрок мало, не берём.")
                )
                if ok:
                    best = length if best is None else max(best, length)
            else:
                left_bound = 0 if i == 0 else pos[i - 1] + 1
                right_bound = n - 1 if i + task["need_l"] >= len(pos) else pos[i + task["need_l"]] - 1
                core_l, core_r = group[0], group[-1]
                pats = [
                    t for t in range(left_bound, right_bound - plen + 2)
                    if s[t : t + plen] == task["pat"]
                ]
                if len(pats) < task["need_p"]:
                    steps.append(
                        f"Буквы на номерах {group_h}: рядом меньше {task['need_p']} подстрок. Пропуск."
                    )
                    continue
                local = None
                local_piece = ""
                for a in range(len(pats) - task["need_p"] + 1):
                    b = a + task["need_p"] - 1
                    left = min(core_l, pats[a])
                    right = max(core_r, pats[b] + plen - 1)
                    if left < left_bound or right > right_bound:
                        continue
                    length = right - left + 1
                    if local is None or length < local:
                        local = length
                        local_piece = s[left : right + 1]
                if local is not None:
                    steps.append(
                        f"Буквы на номерах {group_h}. Самый короткий кусок вокруг них имеет длину {local}: "
                        f"«{esc(local_piece)}»."
                    )
                    best = local if best is None else min(best, local)
        word = "самая большая" if kind == "win_max" else "самая маленькая"
        if best != value:
            raise SystemExit(f"{task['id']}: разбор окна {best}, ответ {value}")
        steps.append(f"Среди подходящих {word} длина {best}.")
    elif kind == "endpat":
        plen = len(task["pat"])
        pos = [i for i in range(len(s) - plen + 1) if s[i : i + plen] == task["pat"]]
        human = [p + 1 for p in pos]
        steps.append(
            f"Подстрока {esc(task['pat'])} начинается на номерах {human}. "
            f"Кусок обязан кончаться на неё, внутри таких подстрок ровно {task['need_p']}, "
            f"букв {esc(task['letter'])} не меньше {task['need_l']}."
        )
        best = 0
        for j in range(task["need_p"] - 1, len(pos)):
            right = pos[j] + plen - 1
            first = j - task["need_p"] + 1
            left = 0 if first == 0 else pos[first - 1] + plen
            letters = s[left : right + 1].count(task["letter"])
            length = right - left + 1
            ok = letters >= task["need_l"]
            steps.append(
                f"Правый край на номере {right + 1}, кусок «{esc(s[left:right + 1])}», "
                f"длина {length}, букв {esc(task['letter'])} {letters}. "
                + ("Подходит." if ok else "Букв мало.")
            )
            if ok:
                best = max(best, length)
        if best != value:
            raise SystemExit(f"{task['id']}: разбор конца {best}, ответ {value}")
        steps.append(f"Самая большая подходящая длина {best}.")
    elif kind == "base":
        allowed = set("0123456789ABCD")
        even_last = set("02468AC")
        cleaned = "".join(ch if ch in allowed else " " for ch in s)
        steps.append(
            "Чужие буквы заменяем пробелом и режем строку. "
            f"Куски-числа: {esc(str(cleaned.split()))}."
        )
        best_show = ""
        for tok in cleaned.split():
            raw = tok
            while tok and tok[-1] not in even_last:
                tok = tok[:-1]
            shown = tok
            tok = tok.lstrip("0")
            steps.append(
                f"«{esc(raw)}»: с конца убираем нечётные цифры, остаётся «{esc(shown) or 'пусто'}». "
                f"Нули спереди убираем, остаётся «{esc(tok) or 'пусто'}», длина {len(tok)}."
            )
            if len(tok) > len(best_show):
                best_show = tok
        steps.append(
            f"Длиннее число всегда больше короткого. Берём «{esc(best_show)}», длина {value}."
        )
    elif kind == "alt":
        letters, digits = set(task["letters"]), set(task["digits"])
        steps.append(
            f"Буквы {esc(task['letters'])}, цифры {esc(task['digits'])}. "
            "Сосед подходит, только если один из них буква, а другой цифра."
        )
        cur = 1
        best = 1
        start = 1
        for i in range(1, len(s)):
            a, b = s[i - 1], s[i]
            ok = (a in letters and b in digits) or (a in digits and b in letters)
            if ok:
                cur += 1
                if cur > best:
                    best = cur
            else:
                steps.append(
                    f"На номерах {start}–{start + cur - 1} кусок шёл {cur} символов, "
                    f"потом «{esc(a)}{esc(b)}» ломает чередование."
                )
                cur = 1
                start = i + 1
        steps.append(f"Хвост тоже смотрим. Самая большая длина {best}.")
    elif kind in ("pair_max", "pair_min"):
        pos = _pair_pos(s, task["pair"])
        human = [p + 1 for p in pos]
        steps.append(
            f"Пара {esc(task['pair'])} начинается на номерах {human or 'нигде'}."
        )
        if kind == "pair_min":
            steps.append(
                f"Для минимума берём {task['k']} соседних пар: "
                "от первой буквы первой пары до второй буквы последней."
            )
            best = None
            for i in range(len(pos) - task["k"] + 1):
                length = pos[i + task["k"] - 1] + 2 - pos[i]
                piece = s[pos[i] : pos[i + task["k"] - 1] + 2]
                steps.append(
                    f"Пары с номеров {[p + 1 for p in pos[i:i + task['k']]]}: "
                    f"кусок «{esc(piece)}», длина {length}."
                )
                best = length if best is None else min(best, length)
            if best != value:
                raise SystemExit(f"{task['id']}: разбор минимума пары {best}, ответ {value}")
            steps.append(f"Самая короткая длина {best}.")
        else:
            how = "ровно" if task["exactly"] else "не больше"
            steps.append(
                f"Нужно {how} {task['k']} пар. "
                "Окно растягиваем, пока не упрёмся в лишнюю пару."
            )
            if (not task["exactly"] and len(pos) <= task["k"]) or len(pos) == task["k"]:
                if len(s) != value:
                    raise SystemExit(f"{task['id']}: вся строка {len(s)}, ответ {value}")
                steps.append(
                    f"Пар в строке {len(pos)}, это уже подходит под условие. "
                    f"Берём всю строку, длина {len(s)}."
                )
            else:
                best = 0
                for i in range(len(pos) - task["k"] + 1):
                    left = 0 if i == 0 else pos[i - 1] + 1
                    right = len(s) - 1 if i + task["k"] >= len(pos) else pos[i + task["k"]]
                    piece = s[left : right + 1]
                    steps.append(
                        f"Пары с номеров {[p + 1 for p in pos[i:i + task['k']]]}: "
                        f"кусок «{esc(piece)}», длина {right - left + 1}."
                    )
                    best = max(best, right - left + 1)
                if best != value:
                    raise SystemExit(f"{task['id']}: разбор пары {best}, ответ {value}")
                steps.append(f"Самая большая длина {best}.")
    elif kind == "expr":
        steps.append(
            f"Цифры {esc(task['digits'])}. Число — это 0 или цифра не ноль и дальше любые разрешённые цифры. "
            "Знак стоит только между числами."
        )
        steps.append(f"Самый длинный правильный кусок имеет длину {value}.")
    steps.append(f"Ответ: <strong>{value}</strong>.")
    if steps[-2].endswith(str(value) + ".") and kind in ("win_max", "win_min", "endpat", "pair_max", "pair_min", "expr"):
        pass
    return steps


def program(task: dict) -> str:
    """Короткая программа к разбору. Печатает ответ, строка уже внутри."""
    s = json.dumps(task["s"], ensure_ascii=False)
    kind = task["kind"]
    head = (
        f"s = {s}\n"
        "# На экзамене файл длинный, строку берут так:\n"
        "# s = open('24.txt').read().strip()\n"
    )
    if kind == "marker":
        bag = {"odd": "13579", "even": "02468", "digit": "0123456789"}[task["pred"]]
        body = f"""
marker = {json.dumps(task["marker"])}
need = {task["need"]}
good = set({json.dumps(bag)})
best = 0
for i, ch in enumerate(s):
    if ch != marker:
        continue
    got = 0
    for j in range(i + 1, len(s) + 1):
        if marker in s[i + 1:j]:
            break
        if s[j - 1] in good:
            got += 1
        if got > need:
            break
        if got == need:
            best = max(best, j - i)
print(best)
"""
    elif kind == "even_start":
        body = f"""
need = {task["need"]}
letter = {json.dumps(task["letter"])}
even = set("02468")
best = 0
i = 0
while i < len(s):
    if s[i] not in even:
        i += 1
        continue
    got = 0
    j = i + 1
    while j < len(s) and s[j] not in even:
        if s[j] == letter:
            got += 1
            if got == need + 1:
                break
        j += 1
    if got >= need:
        best = max(best, j - i)
    i = j if j > i else i + 1
print(best)
"""
    elif kind in ("win_max", "win_min"):
        mode = "max" if kind == "win_max" else "min"
        body = f"""
letter = {json.dumps(task["letter"])}
need_l = {task["need_l"]}
pat = {json.dumps(task["pat"])}
need_p = {task["need_p"]}
best = None
for i in range(len(s)):
    for j in range(i + 1, len(s) + 1):
        frag = s[i:j]
        if frag.count(letter) != need_l:
            continue
        got = sum(1 for t in range(len(frag) - len(pat) + 1) if frag[t:t + len(pat)] == pat)
        if got < need_p:
            continue
        length = j - i
        best = length if best is None else {mode}(best, length)
print(0 if best is None else best)
"""
    elif kind == "endpat":
        body = f"""
pat = {json.dumps(task["pat"])}
need_p = {task["need_p"]}
letter = {json.dumps(task["letter"])}
need_l = {task["need_l"]}
best = 0
plen = len(pat)
for right in range(plen, len(s) + 1):
    if s[right - plen:right] != pat:
        continue
    for left in range(right):
        frag = s[left:right]
        got = sum(1 for t in range(len(frag) - plen + 1) if frag[t:t + plen] == pat)
        if got == need_p and frag.count(letter) >= need_l:
            best = max(best, right - left)
print(best)
"""
    elif kind == "base":
        body = """
allowed = set("0123456789ABCD")
even_last = set("02468AC")
best_val = -1
best_len = 0
tok = ""
parts = []
for ch in s + " ":
    if ch in allowed:
        tok += ch
    elif tok:
        parts.append(tok)
        tok = ""
for tok in parts:
    t = tok
    while t and t[-1] not in even_last:
        t = t[:-1]
    if not t:
        continue
    t = t.lstrip("0") or "0"
    val = int(t, 14)
    if val > best_val:
        best_val = val
        best_len = len(t)
print(best_len)
"""
    elif kind == "alt":
        body = f"""
letters = set({json.dumps(task["letters"])})
digits = set({json.dumps(task["digits"])})
best = cur = 1
for i in range(1, len(s)):
    a, b = s[i - 1], s[i]
    ok = (a in letters and b in digits) or (a in digits and b in letters)
    if ok:
        cur += 1
        best = max(best, cur)
    else:
        cur = 1
print(best if s else 0)
"""
    elif kind == "pair_max":
        mode = "exact" if task["exactly"] else "atmost"
        body = f"""
pair = {json.dumps(task["pair"])}
k = {task["k"]}
mode = {json.dumps(mode)}
best = None
for i in range(len(s)):
    for j in range(i + 1, len(s) + 1):
        frag = s[i:j]
        count = sum(1 for t in range(len(frag) - 1) if frag[t:t + 2] == pair)
        good = count == k if mode != "atmost" else count <= k
        if not good:
            continue
        length = j - i
        best = length if best is None else max(best, length)
print(0 if best is None else best)
"""
    elif kind == "pair_min":
        body = f"""
pair = {json.dumps(task["pair"])}
k = {task["k"]}
best = None
for i in range(len(s)):
    for j in range(i + 1, len(s) + 1):
        frag = s[i:j]
        count = sum(1 for t in range(len(frag) - 1) if frag[t:t + 2] == pair)
        if count != k:
            continue
        length = j - i
        best = length if best is None else min(best, length)
print(0 if best is None else best)
"""
    elif kind == "expr":
        digits = task["digits"]
        nz = "".join(d for d in digits if d != "0")
        body = f"""
import re
digits = {json.dumps(digits)}
nz = {json.dumps(nz)}
num = rf"(?:0|[{{nz}}][{{digits}}]*)"
expr = rf"{{num}}(?:[-*]{{num}})*"
found = [len(m.group()) for m in re.finditer(expr, s)]
print(max(found, default=0))
"""
    else:
        raise KeyError(kind)
    return head + body.strip("\n") + "\n"


def run_printed(src: str) -> str:
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(src, "<solution>", "exec"), {})
    return buf.getvalue().strip()


def solution_html(task: dict, value: int) -> str:
    return (
        "<p><strong>Разбор по шагам.</strong></p>"
        + positions_table(task["s"])
        + ol(trace(task, value))
        + "<p>Тот же ответ даёт полный перебор всех кусков строки. "
        "Два способа сошлись, число можно сдавать.</p>"
        + "<p>Программа ниже печатает ответ. Кнопка «В интерпретатор» открывает её на сайте.</p>"
        + code(program(task))
    )


# Задачи. Ответы подставит проверка, здесь их нет нарочно.
TASKS: list[dict] = [
    # прототип 1, практика
    {"id": "p1a", "group": "practice", "proto": 1, "kind": "marker", "s": "xG135G19aG13579", "marker": "G", "need": 3, "pred": "odd"},
    {"id": "p1b", "group": "practice", "proto": 1, "kind": "marker", "s": "aN12xbN1234cN99", "marker": "N", "need": 2, "pred": "digit"},
    {"id": "p1c", "group": "practice", "proto": 1, "kind": "marker", "s": "Q2Q2468Q13579Q24", "marker": "Q", "need": 2, "pred": "even"},
    {"id": "p1d", "group": "practice", "proto": 1, "kind": "even_start", "s": "a2WWWb4WWc2WWW", "letter": "W", "need": 3},
    {"id": "p1e", "group": "practice", "proto": 1, "kind": "even_start", "s": "x4AAa6AAAAy8AA", "letter": "A", "need": 2},
    # прототип 1, домашка
    {"id": "h1a", "group": "homework", "proto": 1, "kind": "marker", "s": "zA12A3331A90A7", "marker": "A", "need": 3, "pred": "digit"},
    {"id": "h1b", "group": "homework", "proto": 1, "kind": "marker", "s": "kM5aM1357bM9M246", "marker": "M", "need": 2, "pred": "odd"},
    {"id": "h1c", "group": "homework", "proto": 1, "kind": "even_start", "s": "b0RRc2RRRx4RR", "letter": "R", "need": 2},
    {"id": "h1d", "group": "homework", "proto": 1, "kind": "marker", "s": "tH11aH222H4bH13", "marker": "H", "need": 2, "pred": "odd"},
    # прототип 2
    {"id": "p2a", "group": "practice", "proto": 2, "kind": "win_max", "s": "aY2025YYbY2025YY", "letter": "Y", "need_l": 2, "pat": "2025", "need_p": 1},
    {"id": "p2b", "group": "practice", "proto": 2, "kind": "win_max", "s": "xWAByWWzWABqWW", "letter": "W", "need_l": 2, "pat": "AB", "need_p": 1},
    {"id": "p2c", "group": "practice", "proto": 2, "kind": "win_min", "s": "zzWxxAByyWqqAB", "letter": "W", "need_l": 2, "pat": "AB", "need_p": 1},
    {"id": "p2d", "group": "practice", "proto": 2, "kind": "endpat", "s": "xx2025YY2025", "pat": "2025", "need_p": 2, "letter": "Y", "need_l": 1},
    {"id": "p2e", "group": "practice", "proto": 2, "kind": "win_max", "s": "AxxKKAAyyKKAz", "letter": "A", "need_l": 2, "pat": "KK", "need_p": 1},
    {"id": "h2a", "group": "homework", "proto": 2, "kind": "win_max", "s": "Y2025YxY2025Y", "letter": "Y", "need_l": 3, "pat": "2025", "need_p": 1},
    {"id": "h2b", "group": "homework", "proto": 2, "kind": "win_min", "s": "qCDWCDxxCDyyCD", "letter": "W", "need_l": 1, "pat": "CD", "need_p": 2},
    {"id": "h2c", "group": "homework", "proto": 2, "kind": "endpat", "s": "abABZzzABcd", "pat": "AB", "need_p": 2, "letter": "Z", "need_l": 1},
    {"id": "h2d", "group": "homework", "proto": 2, "kind": "win_min", "s": "10X1010y10z10", "letter": "X", "need_l": 1, "pat": "10", "need_p": 2},
    # прототип 3
    {"id": "p3a", "group": "practice", "proto": 3, "kind": "base", "s": "zz1B3zz99Azz10"},
    {"id": "p3b", "group": "practice", "proto": 3, "kind": "base", "s": "q246BCq10A2q7D"},
    {"id": "p3c", "group": "practice", "proto": 3, "kind": "base", "s": "mm00Ayy8Czz13B"},
    {"id": "p3d", "group": "practice", "proto": 3, "kind": "base", "s": "k9DDk2468Akk2B"},
    {"id": "h3a", "group": "homework", "proto": 3, "kind": "base", "s": "ab100CDcd3ABef"},
    {"id": "h3b", "group": "homework", "proto": 3, "kind": "base", "s": "x7BBy12DDz90A"},
    {"id": "h3c", "group": "homework", "proto": 3, "kind": "base", "s": "p0008q13CDr4B"},
    # прототип 4
    {"id": "p4a", "group": "practice", "proto": 4, "kind": "alt", "s": "Q1R2WW4Q", "letters": "QRW", "digits": "124"},
    {"id": "p4b", "group": "practice", "proto": 4, "kind": "alt", "s": "1Q2R4WQR1", "letters": "QRW", "digits": "124"},
    {"id": "p4c", "group": "practice", "proto": 4, "kind": "alt", "s": "A3B3AA4B5", "letters": "AB", "digits": "345"},
    {"id": "p4d", "group": "practice", "proto": 4, "kind": "alt", "s": "7X8Y9XY2X", "letters": "XY", "digits": "7892"},
    {"id": "h4a", "group": "homework", "proto": 4, "kind": "alt", "s": "Q1Q2R4W1W", "letters": "QRW", "digits": "124"},
    {"id": "h4b", "group": "homework", "proto": 4, "kind": "alt", "s": "B0C1D22C0", "letters": "BCD", "digits": "012"},
    {"id": "h4c", "group": "homework", "proto": 4, "kind": "alt", "s": "5M6N7MN8", "letters": "MN", "digits": "5678"},
    # прототип 5
    {"id": "p5a", "group": "practice", "proto": 5, "kind": "pair_max", "s": "xxAByyABzz", "pair": "AB", "k": 1, "exactly": False},
    {"id": "p5b", "group": "practice", "proto": 5, "kind": "pair_max", "s": "xxAByyABzzAB", "pair": "AB", "k": 2, "exactly": True},
    {"id": "p5c", "group": "practice", "proto": 5, "kind": "pair_min", "s": "xxAByyABzzAB", "pair": "AB", "k": 2},
    {"id": "p5d", "group": "practice", "proto": 5, "kind": "pair_max", "s": "aCDbCDccCDdd", "pair": "CD", "k": 2, "exactly": False},
    {"id": "p5e", "group": "practice", "proto": 5, "kind": "pair_min", "s": "BC1BC22BC3BC", "pair": "BC", "k": 2},
    {"id": "h5a", "group": "homework", "proto": 5, "kind": "pair_max", "s": "ABABAxxAB", "pair": "AB", "k": 2, "exactly": True},
    {"id": "h5b", "group": "homework", "proto": 5, "kind": "pair_min", "s": "zzCDyCDwwCD", "pair": "CD", "k": 2},
    {"id": "h5c", "group": "homework", "proto": 5, "kind": "pair_max", "s": "mmBCnnBCkkBC", "pair": "BC", "k": 1, "exactly": False},
    {"id": "h5d", "group": "homework", "proto": 5, "kind": "pair_min", "s": "AB0AB1AB2AB", "pair": "AB", "k": 3},
    # прототип 6
    {"id": "p6a", "group": "practice", "proto": 6, "kind": "expr", "s": "00-78*9-0*67", "digits": "06789"},
    {"id": "p6b", "group": "practice", "proto": 6, "kind": "expr", "s": "56-7*0-65", "digits": "0567"},
    {"id": "p6c", "group": "practice", "proto": 6, "kind": "expr", "s": "5--6*07", "digits": "0567"},
    {"id": "p6d", "group": "practice", "proto": 6, "kind": "expr", "s": "9*09-70*6", "digits": "0679"},
    {"id": "h6a", "group": "homework", "proto": 6, "kind": "expr", "s": "12*0-34--5", "digits": "012345"},
    {"id": "h6b", "group": "homework", "proto": 6, "kind": "expr", "s": "80-7*65*0", "digits": "05678"},
    {"id": "h6c", "group": "homework", "proto": 6, "kind": "expr", "s": "-6*7-0*55", "digits": "0567"},
    # контрольная
    {"id": "c1", "group": "control", "proto": 1, "kind": "marker", "s": "bG24G1359G8G12", "marker": "G", "need": 2, "pred": "odd"},
    {"id": "c2", "group": "control", "proto": 2, "kind": "win_max", "s": "nY2025YnY2025", "letter": "Y", "need_l": 2, "pat": "2025", "need_p": 1},
    {"id": "c3", "group": "control", "proto": 3, "kind": "base", "s": "zz24BCyy7Axx9"},
    {"id": "c4", "group": "control", "proto": 4, "kind": "alt", "s": "W4Q1R2WW1", "letters": "QRW", "digits": "124"},
    {"id": "c5", "group": "control", "proto": 5, "kind": "pair_max", "s": "kABmABnnAB", "pair": "AB", "k": 2, "exactly": False},
    {"id": "c6", "group": "control", "proto": 6, "kind": "expr", "s": "70*6--50-7", "digits": "0567"},
]


TITLES = {
    "p1a": "Практика 24.1 Кусок от G, ровно 3 нечётных",
    "p1b": "Практика 24.1 Кусок от N, ровно 2 цифры",
    "p1c": "Практика 24.1 Кусок от Q, ровно 2 чётных",
    "p1d": "Практика 24.1 Старт с чётной, ровно 3 W",
    "p1e": "Практика 24.1 Старт с чётной, ровно 2 A",
    "h1a": "Домашка 24.1 Кусок от A, ровно 3 цифры",
    "h1b": "Домашка 24.1 Кусок от M, ровно 2 нечётных",
    "h1c": "Домашка 24.1 Старт с чётной, ровно 2 R",
    "h1d": "Домашка 24.1 Кусок от H, ровно 2 нечётных",
    "p2a": "Практика 24.2 Максимум, ровно 2 Y и хотя бы одна 2025",
    "p2b": "Практика 24.2 Максимум, ровно 2 W и хотя бы одна AB",
    "p2c": "Практика 24.2 Минимум, ровно 2 W и хотя бы одна AB",
    "p2d": "Практика 24.2 Кусок кончается на 2025, их ровно 2",
    "p2e": "Практика 24.2 Максимум, ровно 2 A и хотя бы одна KK",
    "h2a": "Домашка 24.2 Максимум, ровно 3 Y и хотя бы одна 2025",
    "h2b": "Домашка 24.2 Минимум, ровно 1 W и хотя бы две CD",
    "h2c": "Домашка 24.2 Кусок кончается на AB, их ровно 2",
    "h2d": "Домашка 24.2 Минимум, ровно 1 X и хотя бы две 10",
    "p3a": "Практика 24.3 Чётное 14-ричное, три куска",
    "p3b": "Практика 24.3 Чётное 14-ричное, 246BC",
    "p3c": "Практика 24.3 Чётное 14-ричное, нули спереди",
    "p3d": "Практика 24.3 Чётное 14-ричное, хвост нечётный",
    "h3a": "Домашка 24.3 Чётное 14-ричное, 100CD",
    "h3b": "Домашка 24.3 Чётное 14-ричное, 12DD и 90A",
    "h3c": "Домашка 24.3 Чётное 14-ричное, 0008 и 13CD",
    "p4a": "Практика 24.4 Чередование Q1R2WW4Q",
    "p4b": "Практика 24.4 Чередование с конца",
    "p4c": "Практика 24.4 Чередование букв A B",
    "p4d": "Практика 24.4 Чередование букв X Y",
    "h4a": "Домашка 24.4 Чередование Q и R",
    "h4b": "Домашка 24.4 Чередование B C D",
    "h4c": "Домашка 24.4 Чередование M N",
    "p5a": "Практика 24.5 Пара AB не больше одного раза",
    "p5b": "Практика 24.5 Пара AB ровно 2, максимум",
    "p5c": "Практика 24.5 Пара AB ровно 2, минимум",
    "p5d": "Практика 24.5 Пара CD не больше двух",
    "p5e": "Практика 24.5 Пара BC ровно 2, минимум",
    "h5a": "Домашка 24.5 Пара AB ровно 2, максимум",
    "h5b": "Домашка 24.5 Пара CD ровно 2, минимум",
    "h5c": "Домашка 24.5 Пара BC не больше одного",
    "h5d": "Домашка 24.5 Пара AB ровно 3, минимум",
    "p6a": "Практика 24.6 Пример, цифры 0 6 7 8 9",
    "p6b": "Практика 24.6 Пример без лишних знаков",
    "p6c": "Практика 24.6 Пример, два минуса подряд",
    "p6d": "Практика 24.6 Пример, ноль впереди",
    "h6a": "Домашка 24.6 Пример 12*0-34",
    "h6b": "Домашка 24.6 Пример 80-7*65",
    "h6c": "Домашка 24.6 Пример начинается со знака",
    "c1": "Контрольная 24. Кусок от G",
    "c2": "Контрольная 24. Окно с 2025",
    "c3": "Контрольная 24. Чётное 14-ричное",
    "c4": "Контрольная 24. Чередование",
    "c5": "Контрольная 24. Пара AB",
    "c6": "Контрольная 24. Арифметический пример",
}


def line_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(
        f"<tr><td class='left'><code>{esc(line)}</code></td><td class='left'>{esc(why)}</td></tr>"
        for line, why in rows
    )
    return (
        '<div class="table-scroll"><table class="code-table">'
        "<tr><th class='left'>Строка программы</th><th class='left'>Зачем она</th></tr>"
        f"{body}</table></div>"
    )


def worked(task: dict, value: int, title: str) -> str:
    return (
        f"<h3>{esc(title)}</h3>"
        f"<p class='question'><strong>Вопрос.</strong> {esc(ask_text(task)).replace(chr(10), ' ')}</p>"
        + positions_table(task["s"])
        + ol(trace(task, value))
        + answer_box(f"Ответ: <strong>{value}</strong>")
    )


def theory_body(solved: dict[str, int]) -> str:
    def val(task_id: str) -> int:
        return solved[task_id]

    def by_id(task_id: str) -> dict:
        return next(item for item in TASKS if item["id"] == task_id)

    p1 = """s = "xG135G19aG13579"
marker = "G"
need = 3
best = 0
for part in s.split(marker)[1:]:
    got = 0
    for i, ch in enumerate(part):
        if ch in "13579":
            got += 1
        if got == need + 1:
            best = max(best, i + 1)
            break
    else:
        if got == need:
            best = max(best, len(part) + 1)
print(best)"""

    p1_even = """s = "a2WWWb4WWc2WWW"
letter = "W"
need = 3
even = set("02468")
best = 0
i = 0
while i < len(s):
    if s[i] in even:
        got = 0
        j = i + 1
        while j < len(s) and s[j] not in even:
            if s[j] == letter:
                got += 1
                if got == need + 1:
                    break
            j += 1
        if got >= need:
            best = max(best, j - i)
        i = j
    else:
        i += 1
print(best)"""

    p2 = """s = "aY2025YYbY2025YY"
letter = "Y"
need_letter = 2
pat = "2025"
need_pat = 1
pos = [i for i, ch in enumerate(s) if ch == letter]
pref = [0]
for i in range(len(s)):
    pref.append(pref[-1] + (s[i:i + len(pat)] == pat))
best = 0
for i in range(len(pos) - need_letter + 1):
    left = 0 if i == 0 else pos[i - 1] + 1
    right = len(s) - 1 if i + need_letter >= len(pos) else pos[i + need_letter] - 1
    hi = right - len(pat) + 1
    count = pref[hi + 1] - pref[left] if hi >= left else 0
    if count >= need_pat:
        best = max(best, right - left + 1)
print(best)"""

    p3 = """s = "zz1B3zz99Azz10"
allowed = set("0123456789ABCD")
even_last = set("02468AC")
cleaned = "".join(ch if ch in allowed else " " for ch in s)
best = 0
for tok in cleaned.split():
    while tok and tok[-1] not in even_last:
        tok = tok[:-1]
    tok = tok.lstrip("0")
    best = max(best, len(tok))
print(best)"""

    p4 = """s = "Q1R2WW4Q"
letters = set("QRW")
digits = set("124")
best = 1
cur = 1
for i in range(1, len(s)):
    a, b = s[i - 1], s[i]
    ok = (a in letters and b in digits) or (a in digits and b in letters)
    if ok:
        cur += 1
        best = max(best, cur)
    else:
        cur = 1
print(best)"""

    p5 = """s = "xxAByyABzz"
pair = "AB"
k = 1
pos = [i for i in range(len(s) - 1) if s[i:i + 2] == pair]
if len(pos) <= k:
    print(len(s))
else:
    best = 0
    for i in range(len(pos) - k + 1):
        left = 0 if i == 0 else pos[i - 1] + 1
        right = len(s) - 1 if i + k >= len(pos) else pos[i + k]
        best = max(best, right - left + 1)
    print(best)"""

    p5min = """s = "xxAByyABzzAB"
pair = "AB"
k = 2
pos = [i for i in range(len(s) - 1) if s[i:i + 2] == pair]
best = min(pos[i + k - 1] + 2 - pos[i] for i in range(len(pos) - k + 1))
print(best)"""

    p6 = """import re
s = "00-78*9-0*67"
digits = "06789"
nz = "".join(d for d in digits if d != "0")
num = rf"(?:0|[{nz}][{digits}]*)"
expr = rf"{num}(?:[-*]{num})*"
print(max(len(m.group()) for m in re.finditer(expr, s)))"""

    parts = []
    add = parts.append

    add("<h1>Задание 24 ЕГЭ: строка символов</h1>")
    add("<p class='intro'>На экзамене дают текстовый файл. В нём сотни тысяч символов. Руками его не прочитать. Пишут программу на 15–30 строк и сдают одно число: длину найденного куска.</p>")
    add("<p class='intro'>В банке ФИПИ все такие задачи сходятся к шести приёмам. Меняются буквы и числа, программа остаётся той же. Ниже каждый приём разобран на короткой строке. Программа делает те же шаги, что палец на бумаге.</p>")
    add("<div class='box'><p><strong>Как узнать приём по тексту условия.</strong></p><ol>")
    add("<li>Просят правильный пример со знаками «−» и «*» — приём 6.</li>")
    add("<li>Просят чётное число в системе счисления — приём 3.</li>")
    add("<li>Буква не стоит рядом с буквой, цифра не стоит рядом с цифрой — приём 4.</li>")
    add("<li>Пара из двух букв, например AB, и слова «не больше» или «ровно» — приём 5.</li>")
    add("<li>Подстрока вроде 2025 и отдельно счётчик буквы — приём 2.</li>")
    add("<li>Кусок начинается с заданной буквы или с чётной цифры, и этой метки внутри больше нет — приём 1.</li>")
    add("</ol></div>")

    add("<h2>Приём 1. Кусок от метки</h2>")
    add("<p>Так устроены номера банка 6AB929, C6FBAB и 4FD865.</p>")
    add("<p>Условие звучит так: кусок начинается с буквы G, других G в нём нет, нечётных цифр ровно 45, нужна самая большая длина. На короткой строке ровно 45 не набрать, поэтому тренируемся на «ровно 3». Шаги те же.</p>")
    add("<p>Метка разрезает строку. Всё, что стоит до первой метки, не начинается с неё и в ответ не идёт. Дальше смотрим каждый кусок справа от метки. Считаем нужные символы слева направо. Как только их стало на один больше, чем просили, лишний символ уже не берём. Если их ровно столько и строка куска кончилась, берём кусок целиком, вместе с меткой.</p>")
    add(worked(by_id("p1a"), val("p1a"), "Пример. Ровно 3 нечётные после G"))
    add("<h3>Программа этого примера, строка за строкой</h3>")
    add(code(p1))
    add(line_table([
        ('s = "xG135G19aG13579"', "Кладём учебную строку. На экзамене здесь текст из файла."),
        ('marker = "G"', "Буква, с которой кусок обязан начаться. Её же не должно быть внутри."),
        ("need = 3", "Сколько нечётных цифр нужно. Ровно столько, не меньше и не больше."),
        ("best = 0", "Рекорд длины. Ноль значит: подходящего куска пока нет."),
        ("for part in s.split(marker)[1:]", "Режем строку по G. [1:] выбрасывает кусок до первой G."),
        ("got = 0", "Счётчик нечётных в этом куске. На каждой новой части начинаем с нуля."),
        ("for i, ch in enumerate(part)", "i — номер символа внутри куска, с нуля. ch — сам символ."),
        ('if ch in "13579"', "Нечётные цифры. Чётные и буквы счётчик не увеличивают."),
        ("got += 1", "Нашли ещё одну нечётную."),
        ("if got == need + 1", "Стало на одну больше, чем просили. Этот символ уже лишний."),
        ("best = max(best, i + 1)", "Длина: сама G плюс символы до лишнего. i + 1 как раз это и есть."),
        ("break", "Дальше по этому куску не идём: нечётных станет только больше."),
        ("else у цикла for", "Сюда попадаем, только если break не случился. Кусок кончился раньше."),
        ("if got == need", "Нечётных ровно столько, сколько просили. Весь кусок годится."),
        ("best = max(best, len(part) + 1)", "Плюс один — это буква G, её split из куска вынул."),
        ("print(best)", "Печатаем рекорд. Это число и есть ответ."),
    ]))
    add(f"<p>Программа печатает <strong>{val('p1a')}</strong>. Это кусок G135: буква G и три нечётные 1, 3, 5.</p>")
    add("<div class='box'><p><strong>Похожий номер банка, 4FD865.</strong> Метка там не буква, а любая чётная цифра. Внутри куска других чётных нет, букв W ровно 30. Режут не через split, а ставят старт на каждую чётную и идут вправо, пока не встретят следующую чётную или лишнюю W.</p></div>")
    add(code(p1_even))
    add(line_table([
        ('s = "a2WWWb4WWc2WWW"', "Короткая строка для приёма «старт с чётной цифры»."),
        ('letter = "W"', "Какую букву считаем."),
        ("need = 3", "Ровно три такие буквы."),
        ('even = set("02468")', "Чётные цифры. Set нужен, чтобы проверка «символ чётный?» была короткой."),
        ("best = 0 и i = 0", "Рекорд и палец на первом символе."),
        ("while i < len(s)", "Идём, пока палец не вышел за строку."),
        ("if s[i] in even", "Нашли возможное начало куска."),
        ("j = i + 1", "Второй палец смотрит символы справа от начала."),
        ("while j < len(s) and s[j] not in even", "Внутри куска чётная цифра запрещена. Встретили — стоп."),
        ("if s[j] == letter: got += 1", "Считаем нужную букву."),
        ("if got == need + 1: break", "Лишняя буква. j стоит на ней, в длину она не войдёт."),
        ("if got >= need: best = max(best, j - i)", "Длина куска от старта до j, сам j не включаем."),
        ("i = j", "Следующий старт ищем с того места, где остановились, чтобы не считать одно и то же дважды."),
        ("else: i += 1", "Символ не чётная цифра, просто шагаем дальше."),
        ("print(best)", "Ответ."),
    ]))
    add(worked(by_id("p1d"), val("p1d"), "Тот же приём на строке с W"))
    add(worked(by_id("p1b"), val("p1b"), "Похожий. Метка N, считаем любые цифры"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>Забыли прибавить саму метку. Длина получается на 1 меньше.</li>")
    add("<li>Взяли кусок до первой метки. Он с метки не начинается.</li>")
    add("<li>Остановились ровно на нужной цифре и не дописали буквы после неё. После третьей нечётной могут идти буквы, они длину увеличивают.</li>")
    add("</ul></div>")

    add("<h2>Приём 2. Окно: подстрока и буква</h2>")
    add("<p>Так устроены номера D6DFE2, 5605A0 и 79DEC1. В файле ищут кусок, где подстрока 2025 встречается сколько сказано, и отдельно буква Y или W.</p>")
    add("<p>Сначала выписывают номера нужной буквы. Ровно K букв — это K соседних номеров из списка. Кусок можно растянуть влево и вправо, но только до соседней такой же буквы, саму соседнюю не включая. Иначе букв станет K+1.</p>")
    add("<p>Подстрока считается, только если она целиком внутри куска. Кусок 202 и потом конец строки — это не 2025.</p>")
    add("<p>Три варианта одного окна:</p><ul>")
    add("<li>Максимум длины, буква ровно K, подстрока не меньше M.</li>")
    add("<li>Минимум длины, те же условия. Окно не растягивают, а сжимают до букв и добирают подстроку.</li>")
    add("<li>Кусок обязан закончиться этой подстрокой. Правый край ставят на конец очередной подстроки.</li>")
    add("</ul>")
    add(code(p2))
    add(line_table([
        ('s = "aY2025YYbY2025YY"', "Учебная строка. Буква Y и подстрока 2025 не содержат друг друга, так считать проще."),
        ('letter = "Y"', "Букву, которой должно быть ровно столько-то."),
        ("need_letter = 2", "Ровно две Y."),
        ('pat = "2025"', "Подстрока, которую считаем отдельно."),
        ("need_pat = 1", "Таких подстрок нужно не меньше одной."),
        ("pos = [...]", "Список номеров всех Y. Нумерация программы с нуля."),
        ("pref = [0]", "Префиксные суммы: сколько раз 2025 началась на отрезке от начала строки до этого места."),
        ("pref.append(...)", "На каждом символе прибавляем 1, если с него начинается 2025."),
        ("for i in range(len(pos) - need_letter + 1)", "Перебираем группы из ровно двух соседних Y."),
        ("left = ...", "Левый край: сразу после предыдущей Y. Если предыдущей нет, край строки."),
        ("right = ...", "Правый край: сразу перед следующей Y. Если её нет, конец строки."),
        ("hi = right - len(pat) + 1", "Последнее место, где 2025 ещё помещается целиком."),
        ("count = pref[hi + 1] - pref[left]", "Сколько 2025 начинается внутри окна и не вылезает наружу."),
        ("if count >= need_pat", "Подстрок хватает. Длину сравниваем с рекордом."),
        ("print(best)", "Самая большая длина."),
    ]))
    add(worked(by_id("p2a"), val("p2a"), "Пример. Ровно две Y и хотя бы одна 2025"))
    add(worked(by_id("p2c"), val("p2c"), "Похожий. Теперь просят минимум"))
    add(worked(by_id("p2d"), val("p2d"), "Похожий. Кусок кончается на 2025"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>Посчитали 2025, которая только задевает кусок и торчит наружу.</li>")
    add("<li>Включили лишнюю Y и получили 3 вместо ровно 2.</li>")
    add("<li>Для минимума растянули окно, как для максимума.</li>")
    add("</ul></div>")

    add("<h2>Приём 3. Самое большое чётное число</h2>")
    add("<p>Номер банка 931D9C. В строке спрятаны 14-ричные числа. Цифры: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D. Остальные буквы число обрывают.</p>")
    add("<p>Чётное в этой системе кончается на чётную цифру: 0, 2, 4, 6, 8, A, C. B это 11, D это 13, они нечётные. Если число кончается на B или D, эти цифры с конца стирают, пока не останется чётная или ничего.</p>")
    add("<p>Нули впереди не считаются: 00A это то же число, что A. В ответ просят не само число, а сколько в нём цифр после очистки.</p>")
    add("<p>Почему достаточно выбрать самое длинное. Самое маленькое число из 4 цифр больше самого большого из 3 цифр. Поэтому победитель — самый длинный кусок после очистки. Среди одной длины уже не выбирают: длина у них одинаковая.</p>")
    add(code(p3))
    add(line_table([
        ('s = "zz1B3zz99Azz10"', "Учебная строка. Буквы z числом не являются."),
        ('allowed = set("0123456789ABCD")', "Алфавит 14-ричной системы."),
        ('even_last = set("02468AC")', "На что может кончаться чётное число."),
        ('cleaned = "".join(...)', "Чужая буква становится пробелом. Числа распадаются на куски."),
        ("for tok in cleaned.split()", "Каждый кусок — кандидат в число."),
        ("while tok and tok[-1] not in even_last", "С конца стираем нечётную цифру."),
        ('tok = tok.lstrip("0")', "Спереди стираем незначащие нули."),
        ("best = max(best, len(tok))", "Сравниваем длины. Пустой кусок имеет длину 0 и рекорд не обновляет."),
        ("print(best)", "Длина самого большого числа."),
    ]))
    add(worked(by_id("p3a"), val("p3a"), "Пример. Три куска"))
    add(worked(by_id("p3b"), val("p3b"), "Похожий. Длинный кусок 246BC"))
    add(worked(by_id("p3c"), val("p3c"), "Похожий. Нули впереди"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>Оставили B или D на конце. Число стало нечётным.</li>")
    add("<li>Посчитали нули впереди. 00A это одна значащая цифра.</li>")
    add("<li>Сравнивали числа как текст, не отрезав хвост.</li>")
    add("</ul></div>")

    add("<h2>Приём 4. Буква и цифра по очереди</h2>")
    add("<p>Номер банка E74424. Буквы Q, R, W и цифры 1, 2, 4. Нужен самый длинный кусок, где буква не стоит рядом с буквой, а цифра не стоит рядом с цифрой. Значит, они строго чередуются: буква, цифра, буква, цифра или с цифры.</p>")
    add("<p>Один проход. Палец на втором символе. Если пара с предыдущим подходит, длину текущей серии увеличиваем. Если не подходит, серия умерла: запоминаем рекорд и начинаем новую с длины 1. Хвост закрывается сам, потому что сравнение идёт на каждой паре, а последняя длина остаётся в cur.</p>")
    add(code(p4))
    add(line_table([
        ('s = "Q1R2WW4Q"', "Учебная строка."),
        ('letters = set("QRW")', "Какие символы считаем буквами."),
        ('digits = set("124")', "Какие символы считаем цифрами."),
        ("best = 1 и cur = 1", "Один символ всегда подходит. Серия и рекорд начинают с единицы."),
        ("for i in range(1, len(s))", "Смотрим пары: символ i и символ слева от него."),
        ("a, b = s[i - 1], s[i]", "a — левый, b — правый."),
        ("ok = (a in letters and b in digits) or ...", "Подходит только смена типа: буква-цифра или цифра-буква."),
        ("cur += 1", "Пара хорошая, серия стала длиннее."),
        ("best = max(best, cur)", "Может, это новый рекорд."),
        ("else: cur = 1", "Пара плохая. Новая серия начинается с символа b, длина 1."),
        ("print(best)", "Ответ."),
    ]))
    add(worked(by_id("p4a"), val("p4a"), "Пример. Q1R2 и потом две W"))
    add(worked(by_id("p4b"), val("p4b"), "Похожий. Чередование рвётся в середине"))
    add(worked(by_id("p4c"), val("p4c"), "Похожий. Другой алфавит, те же шаги"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>После двух букв подряд обнулили длину в ноль. Новый символ уже начинает серию длины 1.</li>")
    add("<li>Потребовали, чтобы кусок начинался только с буквы. С цифры тоже можно.</li>")
    add("<li>Склеили два куска через плохое место.</li>")
    add("</ul></div>")

    add("<h2>Приём 5. Пара букв</h2>")
    add("<p>Номера 2AB916, C2DB39, 3380E0, 361E52, 199381 и 88B226. Строка из букв A–F. Считают пару AB, CD или BC именно в этом порядке.</p>")
    add("<p>Сначала список: на каких номерах пара начинается. Дальше окно по этому списку.</p>")
    add("<ul>")
    add("<li>«Не больше K» и «ровно K», просят максимум. Если пар во всей строке не больше K, для «не больше» годится вся строка. Если пар больше, берут K соседних пар и растягивают окно до следующей пары, саму следующую не захватывая.</li>")
    add("<li>«Ровно K», просят минимум. Окно сжимают: от первой буквы первой пары до второй буквы K-й пары.</li>")
    add("</ul>")
    add("<h3>Максимум, пара не больше одного раза</h3>")
    add(code(p5))
    add(line_table([
        ('s = "xxAByyABzz"', "Учебная строка, две пары AB."),
        ('pair = "AB"', "Какую пару ищем. Порядок важен: BA это не AB."),
        ("k = 1", "Сколько пар разрешено."),
        ("pos = [...]", "Номера, где пара начинается. Нумерация с нуля."),
        ("if len(pos) <= k", "Пар и так не больше разрешённого. Подходит вся строка."),
        ("print(len(s))", "Ответ в этом лёгком случае."),
        ("for i in range(...)", "Группы из k соседних пар."),
        ("left = ...", "Следующий символ после предыдущей лишней пары. Саму лишнюю пару не берём."),
        ("right = pos[i + k]", "Первая буква следующей лишней пары. Вторая буква пары уже снаружи, значит пара в кусок не вошла."),
        ("best = max(best, right - left + 1)", "Длина включая оба края."),
        ("print(best)", "Самая большая длина."),
    ]))
    add(worked(by_id("p5a"), val("p5a"), "Пример. Не больше одной AB"))
    add("<h3>Минимум, пара ровно два раза</h3>")
    add(code(p5min))
    add(line_table([
        ("pos = [...]", "Те же номера начал пар."),
        ("pos[i + k - 1] + 2 - pos[i]", "От начала первой пары до конца последней. Плюс 2, потому что пара занимает два символа."),
        ("min(...)", "Среди всех групп из k пар берём самую короткую."),
    ]))
    add(worked(by_id("p5b"), val("p5b"), "Похожий. Ровно две AB, самая большая длина"))
    add(worked(by_id("p5c"), val("p5c"), "Похожий. Ровно две AB, самая маленькая длина"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>Посчитали BA как AB.</li>")
    add("<li>Включили обе буквы лишней пары. Пар стало на одну больше.</li>")
    add("<li>Для минимума растянули окно в стороны. Минимум как раз без пустых краёв.</li>")
    add("</ul></div>")

    add("<h2>Приём 6. Правильный пример</h2>")
    add("<p>Демоверсия 2026, номер 7DBA1e: цифры 0, 5, 6, 7 и знаки «−», «*». В банке есть те же задачи с другими цифрами: 2B1F8E, CF38C4 и ещё несколько. Правила одни.</p>")
    add("<div class='box'><ol>")
    add("<li>Числа целые, от нуля и больше.</li>")
    add("<li>Ноль пишется одной цифрой 0. Запись 07 не число: ноль впереди.</li>")
    add("<li>Минус и звёздочка стоят только между числами. Это не знак перед числом.</li>")
    add("<li>Два знака подряд нельзя. Пример не начинается и не кончается знаком.</li>")
    add("</ol></div>")
    add("<p>Шаблон числа: либо один 0, либо цифра не ноль и за ней любые разрешённые цифры. Шаблон примера: число, и потом сколько угодно раз «знак и число». Программа находит все такие куски и берёт самый длинный.</p>")
    add(code(p6))
    add(line_table([
        ("import re", "Берём готовый поиск по шаблону. Свой цикл тоже можно, шаблон короче."),
        ('s = "00-78*9-0*67"', "Учебная строка."),
        ('digits = "06789"', "Какие цифры разрешены. На экзамене набор меняют."),
        ('nz = "".join(...)', "Те же цифры, но без нуля. С них может начинаться число больше нуля."),
        ('num = rf"(?:0|[{nz}][{digits}]*)"', "Число: один ноль или ненулевая цифра и хвост из разрешённых цифр."),
        ('expr = rf"{num}(?:[-*]{num})*"', "Число и дальше группы «знак и число». Звёздочка в скобках значит «таких групп сколько угодно, можно ноль»."),
        ("re.finditer(expr, s)", "Находит куски, которые шаблону подходят, и не склеивает их через плохое место."),
        ("max(len(...))", "Самая большая длина."),
    ]))
    add("<p>На строке 00-78*9-0*67 первый ноль стоит отдельно: запись 00 не число. Со второго нуля идёт пример 0-78*9-0*67. Его длина и есть ответ.</p>")
    add(worked(by_id("p6a"), val("p6a"), "Пример. Нули и знаки"))
    add(worked(by_id("p6b"), val("p6b"), "Похожий. Пример целиком правильный"))
    add(worked(by_id("p6c"), val("p6c"), "Похожий. Два минуса подряд режут строку"))
    add("<div class='box'><p><strong>Частые ошибки.</strong></p><ul>")
    add("<li>Приняли 07 за число. Ноль впереди запрещён.</li>")
    add("<li>Приняли 5--6 за пример. Два знака подряд нельзя.</li>")
    add("<li>Начали пример с минуса. Минус здесь не унарный знак, а действие между числами.</li>")
    add("</ul></div>")

    add("<h2>Что решать после теории</h2>")
    add("<p>Дальше три слоя.</p><ol>")
    add("<li>Практика. Короткие строки, тот же приём, другие буквы и числа. Ответ — одно число, как на экзамене.</li>")
    add("<li>Домашка. Те же приёмы, строки новые. Разбор откроется после ответа.</li>")
    add("<li>Контрольная. Шесть задач, по одной на приём, без подсказки в заголовке условия.</li>")
    add("</ol>")
    add("<p>У каждой числовой задачи ответ проверен дважды: программой приёма и полным перебором всех кусков. Числа в разборе с этим совпадают.</p>")
    add("<table class='code-table summary-table'><tr><th>Приём</th><th>Когда узнаёте</th><th>Что сдаёте</th></tr>")
    add("<tr><td>1. Метка</td><td>кусок с буквы или с чётной цифры</td><td>длина</td></tr>")
    add("<tr><td>2. Окно</td><td>подстрока и отдельно буква</td><td>длина</td></tr>")
    add("<tr><td>3. Число</td><td>чётное в системе счисления</td><td>сколько цифр</td></tr>")
    add("<tr><td>4. Очередь</td><td>буква и цифра строго по очереди</td><td>длина</td></tr>")
    add("<tr><td>5. Пара</td><td>AB, CD или BC, не больше или ровно</td><td>длина</td></tr>")
    add("<tr><td>6. Пример</td><td>числа и знаки − *</td><td>длина</td></tr>")
    add("</table>")
    return "\n".join(parts)


def checkbox_block() -> list[dict]:
    return [
        check(
            "Практика 24.1 Что правда про метку",
            "Отметьте всё верное про приём «кусок от метки».",
            [
                ["Кусок обязан начинаться с метки", True],
                ["Длину считают вместе с самой меткой", True],
                ["Кусок до первой метки тоже всегда берём", False],
                ["Лишний нужный символ в длину не входит", True],
            ],
            ol([
                "Да. Иначе это другой кусок.",
                "Да. Split вынимает метку, её прибавляют отдельно.",
                "Нет. Он с метки не начинается.",
                "Да. Как только счётчик стал на один больше, этот символ отбрасывают.",
            ]) + "<p>Ответ: <strong>первый, второй и четвёртый пункты</strong>.</p>",
        ),
        check(
            "Практика 24.2 Что правда про окно",
            "Отметьте всё верное про приём «окно».",
            [
                ["Подстрока 2025 обязана целиком лежать внутри куска", True],
                ["Ровно 2 буквы Y значит, что 3 уже не подходит", True],
                ["Буквы Y обязаны стоять подряд, без чужих символов", False],
                ["Для максимума кусок тянут до соседней Y, но саму её не берут", True],
            ],
            ol([
                "Да. Торчащий хвост подстроки не считается.",
                "Да. Слово «ровно» режет и недобор, и перебор.",
                "Нет. Между ними могут быть другие символы.",
                "Да. Иначе букв станет на одну больше.",
            ]) + "<p>Ответ: <strong>первый, второй и четвёртый пункты</strong>.</p>",
        ),
        check(
            "Практика 24.3 Что правда про чётное число",
            "Отметьте всё верное про 14-ричное чётное число.",
            [
                ["A и C на конце оставляют: это чётные цифры", True],
                ["B и D на конце стирают", True],
                ["Нули впереди входят в ответ", False],
                ["Более длинное число больше более короткого", True],
            ],
            ol([
                "Да. A это 10, C это 12.",
                "Да. B это 11, D это 13.",
                "Нет. 00A это одна значащая цифра.",
                "Да. Поэтому в ответ идёт длина самого длинного после очистки.",
            ]) + "<p>Ответ: <strong>первый, второй и четвёртый пункты</strong>.</p>",
        ),
        check(
            "Практика 24.4 Что правда про чередование",
            "Отметьте всё верное про чередование буквы и цифры.",
            [
                ["Кусок может начаться и с буквы, и с цифры", True],
                ["Две буквы подряд кусок обрывают", True],
                ["После обрыва длина новой серии равна нулю", False],
                ["Один символ — уже подходящий кусок длины 1", True],
            ],
            ol([
                "Да. Оба старта чередуются.",
                "Да. Буква с буквой запрещена, цифра с цифрой тоже.",
                "Нет. Символ, на котором встали, начинает серию длины 1.",
                "Да. У него нет плохой пары.",
            ]) + "<p>Ответ: <strong>первый, второй и четвёртый пункты</strong>.</p>",
        ),
        check(
            "Практика 24.5 Что правда про пару букв",
            "Отметьте всё верное про пару AB.",
            [
                ["BA считается за AB", False],
                ["Для «не больше 1» вся строка подходит, если пара всего одна", True],
                ["Лишнюю пару в кусок не берут целиком", True],
                ["Минимум растягивают до краёв строки", False],
            ],
            ol([
                "Нет. Порядок в паре задан.",
                "Да. Условие «не больше» уже выполнено.",
                "Да. Иначе пар станет больше, чем просили.",
                "Нет. Минимум — это плотный кусок от первой пары до последней нужной.",
            ]) + "<p>Ответ: <strong>второй и третий пункты</strong>.</p>",
        ),
        check(
            "Практика 24.6 Что правда про пример",
            "Отметьте всё верное про арифметический пример.",
            [
                ["07 — нормальное число", False],
                ["0 — нормальное число", True],
                ["Два знака подряд пример обрывают", True],
                ["Минус может стоять в самом начале", False],
            ],
            ol([
                "Нет. Ноль впереди запрещён.",
                "Да. Ноль пишется одной цифрой.",
                "Да. Между знаками нет числа.",
                "Нет. Знак стоит только между числами.",
            ]) + "<p>Ответ: <strong>второй и третий пункты</strong>.</p>",
        ),
    ]


def which_proto_block() -> list[dict]:
    options = [
        "1. Кусок от метки",
        "2. Окно: подстрока и буква",
        "3. Чётное число в системе счисления",
        "4. Буква и цифра по очереди",
        "5. Пара букв",
        "6. Правильный пример",
    ]

    def row(right_index: int) -> list:
        return [[text, i == right_index] for i, text in enumerate(options)]

    items = [
        (0, "Кусок начинается с G, других G нет, нечётных цифр ровно 45."),
        (1, "В куске подстрока 2025 не меньше 90 раз и ровно 80 букв Y."),
        (2, "Найти самое большое чётное 14-ричное число и сдать число его цифр."),
        (3, "Буква не стоит рядом с буквой, цифра не стоит рядом с цифрой."),
        (4, "Пара CD встречается не больше 140 раз, нужна самая большая длина."),
        (5, "Цифры 0, 5, 6, 7 и знаки минус и умножение, нужен правильный пример."),
    ]
    out = []
    for index, (right, text) in enumerate(items, start=1):
        out.append(
            radio(
                f"Проверка 24. Какой приём {index}",
                "Каким приёмом решается такая задача?\n" + text,
                row(right),
                f"<p>{esc(text)}</p><p>Это приём <strong>{options[right]}</strong>.</p>",
            )
        )
    return out


PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Задание 24 ЕГЭ: строка</title>
<style>
  * { background: rgb(255, 255, 255) !important; }
  body {
    font-family: "Times New Roman", Times, serif;
    max-width: 820px;
    margin: 0 auto;
    padding: 32px 20px 80px;
    color: #1a1a1a;
    line-height: 1.55;
    background: rgb(255, 255, 255);
    font-style: italic;
  }
  h1 { font-size: 24px; margin: 0 0 6px; }
  h2 {
    font-size: 19px;
    margin: 40px 0 12px;
    padding-top: 16px;
    border-top: 1px solid #ddd;
  }
  h3 { font-size: 16px; margin: 18px 0 8px; }
  p, li { font-size: 16px; }
  p { margin: 0 0 12px; }
  ul, ol { margin: 0 0 12px; padding-left: 22px; }
  li { margin-bottom: 4px; }
  .intro { font-size: 16px; color: #333; }
  table.code-table {
    border-collapse: collapse;
    background: #ffffff;
    margin: 14px auto;
  }
  table.code-table td, table.code-table th {
    border: 1px solid #333;
    padding: 6px 14px;
    text-align: center;
    font-size: 16px;
    background: #ffffff;
  }
  table.code-table th { font-weight: bold; }
  table.code-table td.left, table.code-table th.left { text-align: left; }
  pre, code { font-style: normal; font-family: Consolas, monospace; }
  pre {
    white-space: pre-wrap;
    border: 1px solid #ddd;
    padding: 12px 14px;
    font-size: 14px;
  }
  .mark { color: #2f6fbd; font-weight: bold; }
  .table-scroll { overflow-x: auto; max-width: 100%; }
  .box {
    margin: 16px 0;
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 6px;
    padding: 16px 20px;
  }
  .box p:last-child { margin-bottom: 0; }
  .question { font-size: 16px; }
  .answer {
    margin-top: 14px;
    padding: 10px 18px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: #ffffff;
    font-size: 16px;
  }
  .answer strong { font-size: 18px; }
  .summary-table { margin-top: 8px; }
</style>
</head>
<body>
{body}
</body>
</html>
"""


LESSON_TITLES = {
    1: "24.1 Кусок от метки",
    2: "24.2 Окно",
    3: "24.3 Чётное число",
    4: "24.4 Буква и цифра",
    5: "24.5 Пара букв",
    6: "24.6 Правильный пример",
}
WALKED = {
    "p1a", "p1d", "p1b", "p2a", "p2c", "p2d", "p3a", "p3b", "p3c",
    "p4a", "p4b", "p4c", "p5a", "p5b", "p5c", "p6a", "p6b", "p6c",
}


def _sections(body: str) -> tuple[str, list[str]]:
    import re

    chunks = re.split(r"(?=<h2>)", body)
    preamble = chunks[0].strip()
    sections = [chunk.strip() for chunk in chunks[1:] if chunk.strip().startswith("<h2>")]
    return preamble, sections


def _images_in(html: str) -> list[str]:
    import re

    names = []
    for name in re.findall(r"images/([^\"']+)", html):
        if name not in names:
            names.append(name)
    return names


def _self_tasks(proto: int) -> list[dict]:
    pool = [
        task for task in TASKS
        if task["proto"] == proto and task["id"] not in WALKED and task["group"] != "control"
    ]
    return pool[:2]


def _question_tasks(proto: int) -> list[dict]:
    own = [
        task for task in TASKS
        if task["proto"] == proto and task["group"] != "control"
    ]
    fresh = [task for task in own if task["id"] not in WALKED]
    walked = [task for task in own if task["id"] in WALKED]
    # теория + вопросы + код ≤ 10 квадратиков
    return (fresh + walked)[:8]


def build_lessons(solved: dict[str, int]) -> tuple[list[dict], str]:
    preamble, sections = _sections(theory_body(solved))
    sections = [part for part in sections if "Что решать после теории" not in part[:90]]
    if len(sections) != 6:
        raise SystemExit(f"в теории 24 ожидалось 6 приёмов, получилось {len(sections)}")
    chunks = [preamble + "\n" + sections[0]] + sections[1:]
    lessons = []
    for proto, chunk in enumerate(chunks, start=1):
        name = LESSON_TITLES[proto].split(" ", 1)[1]
        prefix = f"24.{proto}"
        theory = {
            "type": "theory",
            "title": f"{prefix} Теория. {name}",
            "content": chunk,
            "comment": f"{prefix} Теория. {name}",
            "images": _images_in(chunk),
        }
        lessons.append(theory)
        questions = _question_tasks(proto)
        if not questions:
            raise SystemExit(f"{prefix}: нет вопросов")
        for index, task in enumerate(questions, start=1):
            value = solved[task["id"]]
            fname = f"{task['id']}.txt"
            item = short(
                f"{prefix} Вопрос {index}",
                FILE_HINT + ask_text(task),
                value,
                solution_html(task, value),
            )
            item["images"] = [fname]
            lessons.append(item)
        code_html = (
            f"<h2>Программа к уроку {prefix}</h2>"
            "<p>Нажмите «В интерпретатор» под кодом. "
            "На экзамене строку берут из файла, здесь она уже лежит в программе, "
            "её можно менять и запускать снова.</p>"
            + code(program(questions[0]))
        )
        lessons.append(
            {
                "type": "theory",
                "title": f"{prefix} Код",
                "content": code_html,
                "comment": f"{prefix} Код",
                "images": [],
            }
        )
        count = 2 + len(questions)
        if count > 10:
            raise SystemExit(f"{prefix}: {count} квадратиков, максимум 10")
    body = "\n".join(
        lesson["content"] for lesson in lessons if lesson["type"] == "theory"
    )
    return lessons, body


def write_pack(lessons: list[dict], body: str) -> None:
    PACK.mkdir(parents=True, exist_ok=True)
    page = PAGE.replace("{body}", body)
    (PACK / "theory.html").write_text(page, encoding="utf-8")
    (PACK / "preview.html").write_text(page, encoding="utf-8")
    manifest = {
        "pack_id": "ege-n24-questions",
        "course_slug": "ege-informatika",
        "module_title": "Задание 24 ЕГЭ: строка символов",
        "create_module": True,
        "replace_missing": True,
        "module_description": (
            "Шесть уроков: кусок от метки, окно, чётное число, "
            "чередование, пара букв, арифметический пример. "
            "В каждом уроке теория, вопросы с файлом и программа."
        ),
    }
    (PACK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = {
        "meta": {
            "topic": "ЕГЭ информатика, задание 24",
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
    (PACK / "questions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    images_dir = PACK / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    for old in images_dir.glob("*.txt"):
        old.unlink()
    needed = {
        name
        for lesson in lessons
        for name in lesson.get("images") or []
        if str(name).endswith(".txt")
    }
    by_file = {f"{task['id']}.txt": task for task in TASKS}
    for name in sorted(needed):
        (images_dir / name).write_text(by_file[name]["s"] + "\n", encoding="utf-8")
    zip_path = ROOT / "ege-n24-import.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ("manifest.json", "questions.json"):
            zf.write(PACK / name, name)
        for path in sorted(images_dir.glob("*.txt")):
            zf.write(path, f"images/{path.name}")
    READY.mkdir(parents=True, exist_ok=True)
    target = READY / "24-ege-n24-import.zip"
    target.write_bytes(zip_path.read_bytes())
    print("zip", zip_path)
    print("ready", target)


def main() -> None:
    solved = {}
    for task in TASKS:
        if len(task["s"]) > 40:
            raise SystemExit(f"{task['id']}: строка длиннее 40, перебор будет тяжёлым")
        left = solve(task)
        right = brute(task)
        if left != right:
            raise SystemExit(f"{task['id']}: приём дал {left}, перебор дал {right}")
        if left <= 0:
            raise SystemExit(f"{task['id']}: ответ {left}, задача пустая")
        printed = run_printed(program(task))
        if printed != str(left):
            raise SystemExit(f"{task['id']}: программа напечатала {printed}, ответ {left}")
        solved[task["id"]] = left
        print(f"{task['id']}: {left}")
    lessons, body = build_lessons(solved)
    titles = [lesson["title"] for lesson in lessons]
    if len(titles) != len(set(titles)):
        raise SystemExit("есть одинаковые названия вопросов")
    # теория сама содержит ответы разобранных примеров — сверяем, что число на месте
    for task_id in ("p1a", "p1d", "p1b", "p2a", "p2c", "p2d", "p3a", "p3b", "p3c", "p4a", "p4b", "p4c", "p5a", "p5b", "p5c", "p6a", "p6b", "p6c"):
        if f"<strong>{solved[task_id]}</strong>" not in body:
            raise SystemExit(f"в теории нет ответа {task_id} = {solved[task_id]}")
    write_pack(lessons, body)
    scheme = {
        "theory": sum(1 for x in lessons if x["type"] == "theory"),
        "checkbox": sum(1 for x in lessons if x["type"] == "checkbox"),
        "radio": sum(1 for x in lessons if x["type"] == "radio"),
        "short_answer": sum(1 for x in lessons if x["type"] == "short_answer"),
        "total": len(lessons),
    }
    print("scheme", scheme)


if __name__ == "__main__":
    main()
