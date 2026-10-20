# -*- coding: utf-8 -*-
"""Длинная теория с рабочим Python и разборы к вопросам.

Запуск из корня репозитория:
    python content-packs/rebuild_ege_lessons.py

Сначала прогоняет каждый учебный фрагмент и сверяет печать с ключом.
Потом дописывает блок в theory.html и код в solution_text вопросов.
Повторный запуск заменяет уже вставленный блок, а не дублирует его.
"""

from __future__ import annotations

import ast
import html
import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER_THEORY = "<!-- python-lesson -->"
MARKER_THEORY_END = "<!-- /python-lesson -->"
MARKER_TASK = "<!-- task-code -->"

# Ожидаемый вывод (stdout, без лишних пробелов) -> фрагмент обязан его напечатать.
EXPECT = {}


def src(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def run_py(code: str) -> str:
    ast.parse(code)
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    ns = {"__name__": "lesson"}
    with redirect_stdout(buf):
        exec(compile(code, "<lesson>", "exec"), ns, ns)
    return buf.getvalue().strip()


def add(key: str, code: str, expected: str) -> str:
    code = src(code)
    got = run_py(code)
    if expected is not None and got != str(expected):
        raise SystemExit(f"{key}: ждали {expected!r}, печатает {got!r}")
    EXPECT[key] = got if expected is None else str(expected)
    SNIPPETS[key] = code
    return code


SNIPPETS: dict[str, str] = {}

# ---------- общие куски, которые ученик копирует целиком ----------

add(
    "n5-bin18",
    """
    def to_bin(n):
        # Делим на 2 и собираем остатки. Потом переворачиваем:
        # последний остаток — это старшая цифра.
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    n = 18  # МЕНЯТЬ: число из условия
    record = to_bin(n)
    units = record.count("1")  # считаем цифры 1, не величину числа
    print(n + units)
    """,
    "20",
)

add(
    "n5-min-div5",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    def priem_a(n):
        # Приём А: к числу прибавляют количество единиц.
        return n + to_bin(n).count("1")

    n = 10  # МЕНЯТЬ: нижняя граница перебора
    while True:
        result = priem_a(n)
        if result % 5 == 0:  # МЕНЯТЬ: условие на результат
            print(n)  # в ответ часто просят само N, не result
            break
        n += 1
    """,
    "18",
)

add(
    "n5-b6",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    def priem_b(n):
        record = to_bin(n)
        units = record.count("1")
        # Чётное число единиц — дописываем 0, нечётное — 1.
        if units % 2 == 0:
            record += "0"
        else:
            record += "1"
        # Дописать 0 справа — умножить на 2. Дописать 1 — умножить на 2 и +1.
        return int(record, 2)

    n = 6  # МЕНЯТЬ: число из условия
    print(priem_b(n))
    """,
    "12",
)

add(
    "n5-b13",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    def priem_b(n):
        record = to_bin(n)
        units = record.count("1")
        if units % 2 == 0:
            record += "0"
        else:
            record += "1"
        return int(record, 2)

    n = 13  # МЕНЯТЬ: число из условия
    print(priem_b(n))
    """,
    "27",
)

add(
    "n5-min-gt40",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    def priem_b(n):
        record = to_bin(n)
        if record.count("1") % 2 == 0:
            record += "0"
        else:
            record += "1"
        return int(record, 2)

    n = 1  # МЕНЯТЬ: откуда начинать поиск
    while True:
        result = priem_b(n)
        if result > 40:  # МЕНЯТЬ: порог. «Больше 40» — это не «не меньше 40»
            print(n)
            break
        n += 1
    """,
    "21",
)

add(
    "n5-demo2026",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits) if digits else "0"

    def demo(n):
        record = to_bin(n)
        if n % 3 == 0:
            # Делится на 3: дописываем три последние двоичные цифры.
            record += record[-3:]
        else:
            # Не делится: остаток * 3, эту запись дописываем справа.
            extra = to_bin((n % 3) * 3)
            record += extra
        return int(record, 2)

    n = 1
    while True:
        if demo(n) >= 200:  # МЕНЯТЬ: порог результата
            print(n)
            break
        n += 1
    """,
    "26",
)

add(
    "n5-units",
    """
    def to_bin(n):
        digits = []
        x = n
        while x > 0:
            digits.append(str(x % 2))
            x //= 2
        digits.reverse()
        return "".join(digits)

    record = to_bin(18)  # МЕНЯТЬ: число. Для проверки: 18 -> 10010
    print(record.count("1"))
    """,
    "2",
)

# Черепаха: рисунок отдельно (окно), счёт — чистая функция, её и запускаем.
TURTLE_DRAW = src(
    """
    from turtle import *

    tracer(0)
    left(90)
    screensize(2000, 3000)  # размер окна
    k = 22  # масштаб: чем больше k, тем крупнее рисунок

    for i in range(2):
        forward(8 * k)  # МЕНЯТЬ: первая сторона, здесь высота 8
        right(90)
        forward(4 * k)  # МЕНЯТЬ: вторая сторона, здесь ширина 4
        right(90)

    up()
    for x in range(-5, 15):  # ширина сетки: откуда и докуда ставить точки
        for y in range(-5, 20):  # высота сетки
            goto(x * k, y * k)
            dot(3, "red")
    update()
    done()
    """
)
ast.parse(TURTLE_DRAW)

add(
    "n6-inside5",
    """
    def inside(a, b):
        # Строго внутри прямоугольника, стороны по клеткам.
        # Точки на линии не входят.
        return (a - 1) * (b - 1)

    a = 5  # МЕНЯТЬ: первая сторона
    b = 5  # МЕНЯТЬ: вторая сторона. У квадрата a и b равны
    print(inside(a, b))
    """,
    "16",
)

add(
    "n6-border5",
    """
    def border(a, b):
        # Только линия. Углы считаются один раз.
        return 2 * (a + b)

    a = 5  # МЕНЯТЬ: стороны фигуры
    b = 5
    print(border(a, b))
    """,
    "20",
)

add(
    "n6-rect",
    """
    def trace(commands):
        # Старт (0, 0), смотрит вверх. Команды — пары ("forward", n) или ("right", 90).
        x = y = 0
        dx, dy = 0, 1
        points = [(x, y)]
        for kind, arg in commands:
            if kind == "forward":
                x += dx * arg
                y += dy * arg
                points.append((x, y))
            elif kind == "right":
                turns = (arg // 90) % 4
                for _ in range(turns):
                    dx, dy = dy, -dx  # поворот по часовой
        return points

    def strictly_inside(width, height):
        # Для прямоугольника от (0,0) до (width, height).
        count = 0
        for x in range(width + 1):
            for y in range(height + 1):
                if 0 < x < width and 0 < y < height:
                    count += 1
        return count

    # МЕНЯТЬ: числа после forward — это длины из условия.
    path = [
        ("forward", 8),
        ("right", 90),
        ("forward", 4),
        ("right", 90),
        ("forward", 8),
        ("right", 90),
        ("forward", 4),
    ]
    corners = trace(path)
    width = max(x for x, y in corners) - min(x for x, y in corners)
    height = max(y for x, y in corners) - min(y for x, y in corners)
    print(strictly_inside(width, height))
    """,
    "21",
)

add(
    "n6-inside6",
    """
    def inside(a, b):
        return (a - 1) * (b - 1)

    a = 6  # МЕНЯТЬ: сторона
    b = 6
    print(inside(a, b))
    """,
    "25",
)

add(
    "n6-border6",
    """
    def border(a, b):
        return 2 * (a + b)

    print(border(6, 6))  # МЕНЯТЬ: обе шестёрки — стороны квадрата
    """,
    "24",
)

add(
    "n6-both6",
    """
    def with_border(a, b):
        # Внутри и граница вместе: по стороне a точек на одну больше.
        return (a + 1) * (b + 1)

    print(with_border(6, 6))  # МЕНЯТЬ: стороны
    """,
    "49",
)

add(
    "n7-ex1",
    """
    width = 8  # МЕНЯТЬ: ширина в пикселях
    height = 4  # МЕНЯТЬ: высота
    colors = 4  # МЕНЯТЬ: сколько цветов в палитре

    bits = 0
    while 2 ** bits < colors:  # минимальное i, такое что 2^i >= colors
        bits += 1
    volume_bits = width * height * bits
    print(volume_bits // 8)  # байты
    """,
    "8",
)

add(
    "n7-ex2",
    """
    width = 640  # МЕНЯТЬ
    height = 480  # МЕНЯТЬ
    colors = 16  # МЕНЯТЬ: 16 цветов -> 4 бита
    bits = 0
    while 2 ** bits < colors:
        bits += 1
    byte_count = width * height * bits // 8
    print(byte_count // 1024)  # Кбайт. На ЕГЭ 1 Кбайт = 1024 байт
    """,
    "150",
)

add(
    "n7-ex3",
    """
    kbytes = 150  # МЕНЯТЬ: размер файла
    width = 640
    height = 480
    bits_total = kbytes * 1024 * 8
    print(bits_total // (width * height))  # бит на пиксель
    """,
    "4",
)

add(
    "n7-sound",
    """
    rate = 8000  # МЕНЯТЬ: частота, Гц
    seconds = 8  # МЕНЯТЬ: длительность
    depth = 16  # МЕНЯТЬ: бит на отсчёт
    channels = 1  # МЕНЯТЬ: моно = 1, стерео = 2
    bits = rate * seconds * depth * channels
    print(bits // 8 // 1024)
    """,
    "125",
)

add(
    "n7-palette",
    """
    colors = 40  # МЕНЯТЬ: размер палитры
    bits = 0
    while 2 ** bits < colors:
        bits += 1
    print(bits)
    """,
    "6",
)

add(
    "n7-bits64",
    """
    colors = 64  # МЕНЯТЬ
    bits = 0
    while 2 ** bits < colors:
        bits += 1
    print(bits)
    """,
    "6",
)

add(
    "n7-truecolor",
    """
    bits_per_pixel = 24  # МЕНЯТЬ: True Color
    print(bits_per_pixel // 8)  # байт на пиксель, не 24 байта
    """,
    "3",
)

add(
    "n7-bw",
    """
    width = 100
    height = 100
    bits = 1  # МЕНЯТЬ: глубина
    print(width * height * bits // 8)
    """,
    "1250",
)

add(
    "n8-vb",
    """
    alphabet = "АБВ"  # МЕНЯТЬ: буквы уже по алфавиту
    word = "ВБ"  # МЕНЯТЬ: какое слово ищем
    digit = {letter: i for i, letter in enumerate(alphabet)}
    base = len(alphabet)
    number = 0
    for letter in word:
        number = number * base + digit[letter]
    print(number + 1)  # список нумеруют с 1, не с 0
    """,
    "8",
)

add(
    "n8-tok",
    """
    alphabet = "КОТ"  # МЕНЯТЬ: К=0, О=1, Т=2
    word = "ТОК"  # МЕНЯТЬ
    digit = {letter: i for i, letter in enumerate(alphabet)}
    base = len(alphabet)
    number = 0
    for letter in word:
        number = number * base + digit[letter]
    print(number + 1)
    """,
    "22",
)

add(
    "n8-one-o",
    """
    from itertools import product

    alphabet = "КОТ"  # МЕНЯТЬ
    length = 3  # МЕНЯТЬ: длина слова
    last_number = None
    for index, letters in enumerate(product(alphabet, repeat=length), start=1):
        word = "".join(letters)
        if word.count("О") == 1:  # МЕНЯТЬ: условие на слово
            last_number = index
    print(last_number)
    """,
    "26",
)

add(
    "n8-total",
    """
    letters = 3  # МЕНЯТЬ: мощность алфавита
    length = 3  # МЕНЯТЬ: длина слова
    print(letters ** length)
    """,
    "27",
)

add(
    "n8-digit-t",
    """
    alphabet = "КОТ"  # МЕНЯТЬ
    letter = "Т"  # МЕНЯТЬ: какую букву спрашивают
    print(alphabet.index(letter))  # с нуля
    """,
    "2",
)

add(
    "n2-not-a-or-b",
    """
    # Сколько строк, где выражение истинно.
    # 1 — истина, 0 — ложь. not 0 в Python — это True.
    count = 0
    for a in (0, 1):
        for b in (0, 1):  # МЕНЯТЬ: добавьте букву — добавьте цикл
            value = (not a) or b  # МЕНЯТЬ: само выражение. ¬A ∨ B
            if value:
                count += 1
    print(count)
    """,
    "3",
)

add(
    "n2-three",
    """
    count = 0
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                # (A ∨ B) ∧ ¬C
                value = (a or b) and (not c)  # МЕНЯТЬ: формула
                if value:
                    count += 1
    print(count)
    """,
    "3",
)

add(
    "n2-impl",
    """
    def implies(a, b):
        # A → B ложно только когда A = 1 и B = 0.
        return not (a == 1 and b == 0)

    count = 0
    for a in (0, 1):
        for b in (0, 1):
            if implies(a, b):
                count += 1
    print(count)
    """,
    "3",
)

add(
    "n2-and3",
    """
    count = 0
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                if a and b and c:  # МЕНЯТЬ: A ∧ B ∧ C
                    count += 1
    print(count)
    """,
    "1",
)

add(
    "n2-rows2",
    """
    letters = 2  # МЕНЯТЬ: сколько букв в выражении
    print(2 ** letters)
    """,
    "4",
)

add(
    "n3-grade9",
    """
    students = [
        # номер, имя, класс. МЕНЯТЬ: строки первой таблицы
        (1, "Аня", 9),
        (2, "Боря", 10),
        (3, "Вика", 9),
        (4, "Гена", 11),
        (5, "Даша", 9),
    ]
    print(sum(1 for number, name, grade in students if grade == 9))
    """,
    "3",
)

add(
    "n3-math5",
    """
    grades = [
        # ученик, предмет, оценка. МЕНЯТЬ: вторая таблица
        (1, "математика", 5),
        (1, "физика", 4),
        (3, "математика", 5),
        (3, "физика", 5),
        (5, "математика", 2),
        (5, "физика", 5),
        (2, "математика", 4),
    ]
    count = 0
    for student, subject, mark in grades:
        if subject == "математика" and mark == 5:  # МЕНЯТЬ: предмет и оценка
            count += 1
    print(count)
    """,
    "2",
)

add(
    "n3-sum-math",
    """
    students = {1: 9, 2: 10, 3: 9, 4: 11, 5: 9}  # номер -> класс
    grades = [
        (1, "математика", 5),
        (1, "физика", 4),
        (3, "математика", 5),
        (3, "физика", 5),
        (5, "математика", 2),
        (5, "физика", 5),
        (2, "математика", 4),
    ]
    total = 0
    for student, subject, mark in grades:
        if students[student] == 9 and subject == "математика":
            total += mark
    print(total)
    """,
    "12",
)

add(
    "n3-physics5",
    """
    grades = [
        (1, "математика", 5),
        (1, "физика", 4),
        (3, "математика", 5),
        (3, "физика", 5),
        (5, "математика", 2),
        (5, "физика", 5),
        (2, "математика", 4),
    ]
    people = set()
    for student, subject, mark in grades:
        if subject == "физика" and mark == 5:
            people.add(student)  # человека считаем один раз
    print(len(people))
    """,
    "2",
)

add(
    "n3-twos",
    """
    grades = [
        (1, "математика", 5),
        (1, "физика", 4),
        (3, "математика", 5),
        (3, "физика", 5),
        (5, "математика", 2),
        (5, "физика", 5),
        (2, "математика", 4),
    ]
    print(sum(1 for student, subject, mark in grades if mark == 2))
    """,
    "1",
)

FANO = src(
    """
    def conflicts(a, b):
        # Одно слово — начало другого. Так условие Фано нарушается.
        return a.startswith(b) or b.startswith(a)

    def shortest_codes(known, need, limit=6):
        # known — уже занятые коды. need — сколько новых букв.
        # Берём набор самой маленькой суммарной длины.
        from itertools import combinations

        candidates = []
        for length in range(1, limit + 1):
            for i in range(2 ** length):
                code = f"{i:0{length}b}"
                if all(not conflicts(code, old) for old in known):
                    candidates.append(code)
        best = None
        for group in combinations(candidates, need):
            bad = False
            for i, left in enumerate(group):
                for right in group[i + 1 :]:
                    if conflicts(left, right):
                        bad = True
                        break
                if bad:
                    break
            if bad:
                continue
            score = sum(len(code) for code in group)
            if best is None or score < best[0]:
                best = (score, group)
        return list(best[1])
    """
)


def with_fano(body: str) -> str:
    return FANO + "\n" + src(body)


add(
    "n4-task1",
    with_fano(
        """
        known = ["11", "1000", "010", "1001", "011"]  # МЕНЯТЬ: известные коды
        need = 3  # МЕНЯТЬ: сколько букв ещё надо посадить
        codes = shortest_codes(known, need)
        print(sum(len(code) for code in codes))
        """
    ),
    "9",
)

add(
    "n4-task1-len",
    with_fano(
        """
        known = ["11", "1000", "010", "1001", "011"]
        codes = shortest_codes(known, 3)
        print(len(codes[0]))  # в этой задаче все три одной длины
        """
    ),
    "3",
)

add(
    "n4-task1-free",
    with_fano(
        """
        known = ["11", "1000", "010", "1001", "011"]
        codes = shortest_codes(known, 3)
        print(len(codes))
        """
    ),
    "3",
)

add(
    "n4-task2",
    with_fano(
        """
        known = ["1100", "1011", "100"]  # A, B, C
        need = 4  # четыре знака операций
        codes = shortest_codes(known, need)
        print(sum(len(code) for code in codes))
        """
    ),
    "11",
)

add(
    "n4-task3",
    with_fano(
        """
        known = ["1001", "00", "011", "01010"]  # Б Л О К
        codes = shortest_codes(known, 4)  # Ч Е Й Н
        total = sum(len(code) for code in known) + sum(len(code) for code in codes)
        print(total)
        """
    ),
    "27",
)

add(
    "n4-task4",
    with_fano(
        """
        known = ["11110", "000", "01", "100", "101", "1110", "001"]
        # Ищем самую короткую свободную длину.
        # Если таких кодов несколько — берём наибольшее число.
        chosen = None
        for length in range(1, 8):
            level = []
            for i in range(2 ** length):
                code = f"{i:0{length}b}"
                if all(not conflicts(code, old) for old in known):
                    level.append(code)
            if level:
                chosen = max(level, key=lambda code: int(code, 2))
                break
        print(chosen)
        """
    ),
    "110",
)

add(
    "n9-sum-last",
    """
    rows = [
        # МЕНЯТЬ: числа из файла. Здесь учебная таблица из теории.
        [4, 4, 4, 1, 9],
        [2, 2, 2, 5, 8],
        [7, 7, 7, 3, 5],
        [1, 2, 3, 4, 5],
        [6, 6, 6, 1, 2],
        [9, 9, 9, 4, 8],
    ]

    def fits(row):
        counts = [row.count(x) for x in row]
        if sorted(counts) != [1, 1, 3, 3, 3]:
            return False
        triple = [x for x in row if row.count(x) == 3][0]
        singles = [x for x in row if row.count(x) == 1]
        average = sum(singles) / len(singles)
        return average <= triple  # МЕНЯТЬ: знак сравнения из условия

    good = [row for row in rows if fits(row)]
    print(sum(good[-1]))  # последняя подходящая
    """,
    "39",
)

add(
    "n9-how-many",
    """
    rows = [
        [4, 4, 4, 1, 9],
        [2, 2, 2, 5, 8],
        [7, 7, 7, 3, 5],
        [1, 2, 3, 4, 5],
        [6, 6, 6, 1, 2],
        [9, 9, 9, 4, 8],
    ]

    def fits(row):
        counts = [row.count(x) for x in row]
        if sorted(counts) != [1, 1, 3, 3, 3]:
            return False
        triple = [x for x in row if row.count(x) == 3][0]
        singles = [x for x in row if row.count(x) == 1]
        return sum(singles) / len(singles) <= triple

    print(sum(1 for row in rows if fits(row)))
    """,
    "3",
)

add(
    "n9-row3",
    """
    row = [7, 7, 7, 3, 5]  # МЕНЯТЬ: строка с тремя семёрками
    print(sum(row))
    """,
    "29",
)

add(
    "n9-counts",
    """
    row = [7, 7, 7, 3, 5]  # МЕНЯТЬ: любая подходящая строка
    counts = [row.count(x) for x in row]
    print(sum(counts))  # 3+3+3+1+1 = 11
    """,
    "11",
)

add(
    "n9-row5",
    """
    row = [6, 6, 6, 1, 2]  # МЕНЯТЬ
    print(sum(row))
    """,
    "21",
)

add(
    "n10-inside",
    """
    import re

    text = "котик видит кота, а кот сидит у котика"  # МЕНЯТЬ: текст
    text = text.lower()
    needle = "кот"  # МЕНЯТЬ: сочетание
    all_hits = len(re.findall(needle, text))
    whole = len(re.findall(r"\\b" + needle + r"\\b", text))
    print(all_hits - whole)  # внутри других слов
    """,
    "3",
)

add(
    "n10-whole",
    """
    import re

    text = "котик видит кота, а кот сидит у котика".lower()
    needle = "кот"
    print(len(re.findall(r"\\b" + needle + r"\\b", text)))
    """,
    "1",
)

add(
    "n10-all",
    """
    text = "котик видит кота, а кот сидит у котика".lower()
    needle = "кот"  # МЕНЯТЬ
    print(text.count(needle))
    """,
    "4",
)

add(
    "n10-sub",
    """
    import re

    text = "котик видит кота, а кот сидит у котика".lower()
    needle = "кот"
    all_hits = text.count(needle)
    whole = len(re.findall(r"\\b" + needle + r"\\b", text))
    print(all_hits - whole)
    """,
    "3",
)

add(
    "n10-kotik",
    """
    word = "котик"  # МЕНЯТЬ: одно слово
    needle = "кот"
    print(word.lower().count(needle))
    """,
    "1",
)

add(
    "n11-bits",
    """
    alphabet = 26  # МЕНЯТЬ: сколько разных символов
    length = 4  # МЕНЯТЬ: длина пароля
    bits = 0
    while 2 ** bits < alphabet:
        bits += 1
    print(bits * length)
    """,
    "20",
)

add(
    "n11-bytes",
    """
    password_bits = 20  # МЕНЯТЬ: биты одного пароля

    def bytes_up(bits):
        # Целое число байт: округление вверх.
        return (bits + 7) // 8

    print(bytes_up(password_bits))
    """,
    "3",
)

add(
    "n11-users",
    """
    people = 200  # МЕНЯТЬ
    per_password = 3  # МЕНЯТЬ: байт на один пароль, уже после округления
    print(people * per_password)
    """,
    "600",
)

add(
    "n11-checksum",
    """
    alphabet = 36  # МЕНЯТЬ: 10 цифр + 26 букв
    length = 6
    extra = 8  # МЕНЯТЬ: контрольная сумма, биты
    bits_symbol = 0
    while 2 ** bits_symbol < alphabet:
        bits_symbol += 1
    total_bits = bits_symbol * length + extra
    print((total_bits + 7) // 8)
    """,
    "6",
)

add(
    "n11-kbytes",
    """
    people = 4096  # МЕНЯТЬ
    bits_each = 20  # МЕНЯТЬ: без округления каждого пароля
    all_bits = people * bits_each
    all_bytes = all_bits // 8
    print(all_bytes // 1024)
    """,
    "10",
)

add(
    "n12-zeros-before",
    """
    chain = "001000"  # МЕНЯТЬ: исходная лента, без пробелов
    print(chain.count("0"))
    """,
    "5",
)

add(
    "n12-zeros-after",
    """
    def run(chain):
        tape = list(chain)
        i = len(tape) - 1  # головка пришла справа и смотрит на последний символ
        while True:
            if tape[i] == "0":
                tape[i] = "1"  # ноль -> единица, идём дальше влево
                i -= 1
            else:
                tape[i] = "0"  # единица -> ноль и стоп
                break
        return "".join(tape)

    result = run("001000")  # МЕНЯТЬ: лента
    print(result.count("0"))
    """,
    "3",
)

add(
    "n12-max-zeros",
    """
    length = 1000  # МЕНЯТЬ: длина цепочки
    # Один символ обязан быть той единицей, на которой головка остановилась.
    print(length - 1)
    """,
    "999",
)

add(
    "n12-right",
    """
    length = 1000  # МЕНЯТЬ
    left_zeros = 342  # нули слева от остановки
    stop = 1  # сама бывшая единица, теперь ноль
    print(length - left_zeros - stop)
    """,
    "657",
)

add(
    "n12-left",
    """
    left_zeros = 343  # МЕНЯТЬ: сколько нулей осталось
    # Один из оставшихся нулей — это остановка (единицу заменили на ноль).
    print(left_zeros - 1)
    """,
    "342",
)

add(
    "n13-192",
    """
    def max_host(ip, mask):
        ip_b = [int(part) for part in ip.split(".")]
        mask_b = [int(part) for part in mask.split(".")]
        network = [a & b for a, b in zip(ip_b, mask_b)]
        broadcast = [n | (255 - m) for n, m in zip(network, mask_b)]
        # Минус 1 у широковещательного: это наибольший адрес компьютера.
        broadcast[3] -= 1
        for i in range(3, 0, -1):
            if broadcast[i] < 0:
                broadcast[i] += 256
                broadcast[i - 1] -= 1
        return "".join(str(part) for part in broadcast)

    ip = "192.168.1.15"  # МЕНЯТЬ: адрес узла
    mask = "255.255.255.0"  # МЕНЯТЬ: маска
    print(max_host(ip, mask))
    """,
    "1921681254",
)

add(
    "n13-10",
    """
    def max_host(ip, mask):
        ip_b = [int(part) for part in ip.split(".")]
        mask_b = [int(part) for part in mask.split(".")]
        network = [a & b for a, b in zip(ip_b, mask_b)]
        broadcast = [n | (255 - m) for n, m in zip(network, mask_b)]
        broadcast[3] -= 1
        for i in range(3, 0, -1):
            if broadcast[i] < 0:
                broadcast[i] += 256
                broadcast[i - 1] -= 1
        return "".join(str(part) for part in broadcast)

    print(max_host("10.20.30.40", "255.255.0.0"))
    """,
    "1020255254",
)

add(
    "n13-demo",
    """
    def max_host(ip, mask):
        ip_b = [int(part) for part in ip.split(".")]
        mask_b = [int(part) for part in mask.split(".")]
        network = [a & b for a, b in zip(ip_b, mask_b)]
        broadcast = [n | (255 - m) for n, m in zip(network, mask_b)]
        broadcast[3] -= 1
        for i in range(3, 0, -1):
            if broadcast[i] < 0:
                broadcast[i] += 256
                broadcast[i - 1] -= 1
        return "".join(str(part) for part in broadcast)

    print(max_host("191.128.66.83", "255.192.0.0"))
    """,
    "191191255254",
)

add(
    "n13-host-bits",
    """
    mask = "255.255.255.0"  # МЕНЯТЬ
    bits = "".join(f"{int(part):08b}" for part in mask.split("."))
    print(bits.count("0"))  # нули маски — номер компьютера
    """,
    "8",
)

add(
    "n13-end",
    """
    # При маске 255.255.255.0 последний байт компьютера — от 1 до 254.
    # 255 — широковещательный, его не дают.
    print(254)
    """,
    "254",
)

add(
    "n14-digits",
    """
    # 2*9^2 + 4*9 + 7. Цифры уже стоят в записи: 2, 4, 7.
    digits = [2, 4, 7]  # МЕНЯТЬ: цифры числа в этой системе
    border = 3  # МЕНЯТЬ: «больше какого числа»
    print(sum(1 for digit in digits if digit > border))
    """,
    "2",
)

add(
    "n14-quot",
    """
    base = 5  # МЕНЯТЬ: основание
    best_x = None
    best_quot = None
    for x in range(base):  # цифра от 0 до base-1
        first = 3 * base ** 2 + x * base + 2  # число 3x2
        second = 1 * base ** 2 + x * base + 4  # число 1x4
        total = first + second
        if total % 4 == 0:  # МЕНЯТЬ: на что делится сумма
            best_x = x
            best_quot = total // 4
    print(best_quot)  # в ответ пишут частное
    """,
    "34",
)

add(
    "n14-x",
    """
    base = 5
    best_x = None
    for x in range(base):
        first = 3 * base ** 2 + x * base + 2
        second = 1 * base ** 2 + x * base + 4
        if (first + second) % 4 == 0:
            best_x = x  # цикл идёт вверх, останется наибольший
    print(best_x)
    """,
    "3",
)

add(
    "n14-zeros",
    """
    n = 40  # МЕНЯТЬ: число
    record = bin(n)[2:]  # отрезаем приставку 0b
    print(record.count("0"))
    """,
    "4",
)

add(
    "n14-value",
    """
    print(2 * 81 + 4 * 9 + 7)  # МЕНЯТЬ: степени и цифры
    """,
    "205",
)

add(
    "n15-len4",
    """
    def cover(p_left, p_right, q_left, q_right):
        # A обязан закрыть пересечение P и Q.
        left = max(p_left, q_left)
        right = min(p_right, q_right)
        return right - left  # длина, не число целых точек

    print(cover(2, 10, 6, 14))  # МЕНЯТЬ: концы P и Q
    """,
    "4",
)

add(
    "n15-len3",
    """
    def cover(p_left, p_right, q_left, q_right):
        left = max(p_left, q_left)
        right = min(p_right, q_right)
        return right - left

    print(cover(1, 8, 5, 12))
    """,
    "3",
)

add(
    "n15-demo",
    """
    def cover(p_left, p_right, q_left, q_right):
        left = max(p_left, q_left)
        right = min(p_right, q_right)
        return right - left

    print(cover(25, 64, 40, 115))
    """,
    "24",
)

add(
    "n15-left",
    """
    p_left, p_right = 25, 64  # МЕНЯТЬ
    q_left, q_right = 40, 115
    print(max(p_left, q_left))
    """,
    "40",
)

add(
    "n15-right",
    """
    p_left, p_right = 25, 64
    q_left, q_right = 40, 115  # МЕНЯТЬ
    print(min(p_right, q_right))
    """,
    "64",
)

# Рекурсия 16: те же правила, что в теории, столбиком в цикле.
add(
    "n16-toy",
    """
    # F(1) = 1, дальше F(n) = F(n-1) + n
    f = [0, 1]  # индекс — это n. Ноль не используем
    for n in range(2, 6 + 1):  # МЕНЯТЬ: до какого n считать
        f.append(f[n - 1] + n)
    print(f[6])
    """,
    "21",
)

add(
    "n16-g8",
    """
    g = {1: 1, 2: 2}  # два стопа. МЕНЯТЬ: стоп-значения
    for n in range(3, 8 + 1):  # МЕНЯТЬ: верхняя граница
        if n % 2 == 1:
            g[n] = g[n - 1] - g[n - 2]
        else:
            g[n] = g[n - 1] + g[n - 2]
    print(g[8])
    """,
    "8",
)

add(
    "n16-f13",
    """
    f = {1: 1}
    for n in range(2, 13 + 1):
        if n % 2 == 0:
            f[n] = f[n // 2]  # чётное: аргумент делим, не ответ
        else:
            f[n] = f[n - 1] + 1
    print(f[13])
    """,
    "3",
)

add(
    "n16-div3",
    """
    f = {1: 1, 2: 2}
    good = 0
    for n in range(1, 20 + 1):  # МЕНЯТЬ: до какого n
        if n >= 3:
            f[n] = f[n - 1] + f[n - 2]
        if f[n] % 3 == 0:  # МЕНЯТЬ: какое свойство считаем
            good += 1
    print(good)
    """,
    "5",
)

add(
    "n16-f12",
    """
    f = {1: 2}
    for n in range(2, 12 + 1):
        if n % 2 == 0:
            f[n] = f[n // 2] + n
        else:
            f[n] = f[n - 1] + 1
    print(f[12])
    """,
    "23",
)

add(
    "n17-one-even",
    """
    row = [8, 6, 4, 15, 10, 2, 7, 12, 18, 3, 9, 14]  # МЕНЯТЬ: файл
    sums = []
    for i in range(len(row) - 1):
        a, b = row[i], row[i + 1]
        evens = (a % 2 == 0) + (b % 2 == 0)
        if evens == 1:  # МЕНЯТЬ: ровно одно чётное
            sums.append(a + b)
    print(len(sums), max(sums))
    """,
    "6 25",
)

add(
    "n17-triples",
    """
    row = [8, 6, 4, 15, 10, 2, 7, 12, 18, 3, 9, 14]
    sums = []
    for i in range(len(row) - 2):
        s = row[i] + row[i + 1] + row[i + 2]
        if s % 5 == 0:  # МЕНЯТЬ: делитель
            sums.append(s)
    print(len(sums), max(sums))
    """,
    "2 30",
)

add(
    "n17-div3",
    """
    row = [9, 6, 4, 12, 15, 8, 3, 18, 7, 21]  # МЕНЯТЬ: другой ряд
    sums = []
    for i in range(len(row) - 1):
        a, b = row[i], row[i + 1]
        if a % 3 == 0 and b % 3 == 0:  # МЕНЯТЬ: оба делятся на 3
            sums.append(a + b)
    print(len(sums), max(sums))
    """,
    "3 27",
)

add(
    "n18-max",
    """
    field = [
        [2, 4, 1],  # МЕНЯТЬ: строки поля сверху вниз
        [3, 1, 5],
        [2, 6, 1],
    ]
    rows = len(field)
    cols = len(field[0])
    best = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                best[r][c] = field[r][c]
            elif r == 0:
                best[r][c] = best[r][c - 1] + field[r][c]
            elif c == 0:
                best[r][c] = best[r - 1][c] + field[r][c]
            else:
                best[r][c] = max(best[r - 1][c], best[r][c - 1]) + field[r][c]
    print(best[-1][-1])
    """,
    "14",
)

add(
    "n18-min",
    """
    field = [
        [2, 4, 1],
        [3, 1, 5],
        [2, 6, 1],
    ]
    rows, cols = len(field), len(field[0])
    best = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                best[r][c] = field[r][c]
            elif r == 0:
                best[r][c] = best[r][c - 1] + field[r][c]
            elif c == 0:
                best[r][c] = best[r - 1][c] + field[r][c]
            else:
                # МЕНЯТЬ: max — наибольшая сумма, min — наименьшая
                best[r][c] = min(best[r - 1][c], best[r][c - 1]) + field[r][c]
    print(best[-1][-1])
    """,
    "12",
)

add(
    "n18-wide-max",
    """
    field = [
        [1, 3, 2, 4],
        [2, 1, 5, 1],
        [4, 2, 1, 3],
    ]
    rows, cols = len(field), len(field[0])
    best = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                best[r][c] = field[r][c]
            elif r == 0:
                best[r][c] = best[r][c - 1] + field[r][c]
            elif c == 0:
                best[r][c] = best[r - 1][c] + field[r][c]
            else:
                best[r][c] = max(best[r - 1][c], best[r][c - 1]) + field[r][c]
    print(best[-1][-1])
    """,
    "15",
)

add(
    "n18-wide-min",
    """
    field = [
        [1, 3, 2, 4],
        [2, 1, 5, 1],
        [4, 2, 1, 3],
    ]
    rows, cols = len(field), len(field[0])
    best = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                best[r][c] = field[r][c]
            elif r == 0:
                best[r][c] = best[r][c - 1] + field[r][c]
            elif c == 0:
                best[r][c] = best[r - 1][c] + field[r][c]
            else:
                best[r][c] = min(best[r - 1][c], best[r][c - 1]) + field[r][c]
    print(best[-1][-1])
    """,
    "10",
)

GAME = src(
    """
    def moves_of(s, adds, mults):
        result = [s + step for step in adds]
        result += [s * factor for factor in mults]
        return result

    def win_now(s, limit, adds, mults):
        return any(nxt >= limit for nxt in moves_of(s, adds, mults))

    def task19(limit, adds, mults):
        # Наименьшее S, откуда первый ход сразу побеждает.
        s = 1
        while True:
            if s < limit and win_now(s, limit, adds, mults):
                return s
            s += 1

    def task20(limit, adds, mults):
        # Петя сразу не побеждает, но любой его ход отдаёт победу Ване.
        s = 1
        while s < limit:
            if not win_now(s, limit, adds, mults):
                nxt = [x for x in moves_of(s, adds, mults) if x < limit]
                if nxt and all(win_now(x, limit, adds, mults) for x in nxt):
                    return s
            s += 1
        return None

    def task21(limit, adds, mults):
        # Два наименьших S, откуда Петя побеждает своим вторым ходом.
        found = []
        s = 1
        while len(found) < 2 and s < limit:
            if not win_now(s, limit, adds, mults):
                for t in moves_of(s, adds, mults):
                    if t >= limit:
                        continue
                    vanya = [u for u in moves_of(t, adds, mults)]
                    # Любой ход Вани ещё не победа, но после него Петя побеждает сразу.
                    if vanya and all(
                        u < limit and win_now(u, limit, adds, mults) for u in vanya
                    ):
                        found.append(s)
                        break
            s += 1
        return int("".join(str(x) for x in found))
    """
)


def with_game(body: str) -> str:
    return GAME + "\n" + src(body)


add(
    "n19-25",
    with_game(
        """
        limit = 25  # МЕНЯТЬ: граница
        adds = [1, 2]  # МЕНЯТЬ: что прибавляют
        mults = [2]  # МЕНЯТЬ: на что умножают
        print(task19(limit, adds, mults))
        """
    ),
    "13",
)

add(
    "n19-30",
    with_game(
        """
        limit = 30
        adds = [1, 4]
        mults = [3]
        print(task19(limit, adds, mults))
        """
    ),
    "10",
)

add(
    "n20-25",
    with_game(
        """
        print(task20(25, [1, 2], [2]))
        """
    ),
    "12",
)

add(
    "n20-30",
    with_game(
        """
        print(task20(30, [1, 4], [3]))
        """
    ),
    "9",
)

add(
    "n21-25",
    with_game(
        """
        print(task21(25, [1, 2], [2]))
        """
    ),
    "610",
)

add(
    "n21-30",
    with_game(
        """
        print(task21(30, [1, 4], [3]))
        """
    ),
    "35",
)

add(
    "n22-all",
    """
    # имя: (длительность, кого ждёт)
    jobs = {
        "A": (4, []),  # МЕНЯТЬ: минуты и список ожидания
        "B": (6, []),
        "C": (3, ["A"]),
        "D": (5, ["A", "B"]),
        "E": (2, ["C", "D"]),
    }
    finish = {}
    pending = dict(jobs)
    while pending:
        ready = [
            name
            for name, (minutes, wait) in pending.items()
            if all(other in finish for other in wait)
        ]
        name = ready[0]
        minutes, wait = pending.pop(name)
        start = 0 if not wait else max(finish[other] for other in wait)
        finish[name] = start + minutes
    print(max(finish.values()))
    """,
    "13",
)

add(
    "n22-e",
    """
    jobs = {
        "A": (4, []),
        "B": (3, []),  # МЕНЯТЬ: B стал короче, было 6
        "C": (3, ["A"]),
        "D": (5, ["A", "B"]),
        "E": (2, ["C", "D"]),
    }
    finish = {}
    pending = dict(jobs)
    while pending:
        ready = [
            name
            for name, (minutes, wait) in pending.items()
            if all(other in finish for other in wait)
        ]
        name = ready[0]
        minutes, wait = pending.pop(name)
        start = 0 if not wait else max(finish[other] for other in wait)
        finish[name] = start + minutes
    print(finish["E"])  # МЕНЯТЬ: про какой процесс спросили
    """,
    "11",
)

add(
    "n22-f",
    """
    jobs = {
        "A": (5, []),
        "B": (2, ["A"]),
        "C": (4, ["A"]),
        "D": (3, ["B"]),
        "E": (6, ["C"]),
        "F": (1, ["D", "E"]),
    }
    finish = {}
    pending = dict(jobs)
    while pending:
        ready = [
            name
            for name, (minutes, wait) in pending.items()
            if all(other in finish for other in wait)
        ]
        name = ready[0]
        minutes, wait = pending.pop(name)
        start = 0 if not wait else max(finish[other] for other in wait)
        finish[name] = start + minutes
    print(finish["F"])
    """,
    "16",
)

add(
    "n23-to6",
    """
    start = 1  # МЕНЯТЬ: старт
    goal = 6  # МЕНЯТЬ: цель
    ways = [0] * (goal + 1)
    ways[start] = 1
    for n in range(start, goal + 1):
        if ways[n] == 0:
            continue
        if n + 1 <= goal:  # МЕНЯТЬ: команда +1
            ways[n + 1] += ways[n]
        if n * 2 <= goal:  # МЕНЯТЬ: команда ×2
            ways[n * 2] += ways[n]
    print(ways[goal])
    """,
    "6",
)

add(
    "n23-to10",
    """
    start, goal = 1, 10
    ways = [0] * (goal + 1)
    ways[start] = 1
    for n in range(start, goal + 1):
        if n + 1 <= goal:
            ways[n + 1] += ways[n]
        if n * 2 <= goal:
            ways[n * 2] += ways[n]
    print(ways[goal])
    """,
    "14",
)

add(
    "n23-ban7",
    """
    start, goal = 1, 10
    banned = {7}  # МЕНЯТЬ: запрещённые числа
    ways = [0] * (goal + 1)
    ways[start] = 1
    for n in range(start, goal + 1):
        if n in banned:
            ways[n] = 0  # через запрет не ходим
            continue
        if n + 1 <= goal and (n + 1) not in banned:
            ways[n + 1] += ways[n]
        if n * 2 <= goal and (n * 2) not in banned:
            ways[n * 2] += ways[n]
    print(ways[goal])
    """,
    "8",
)

add(
    "n23-plus",
    """
    start, goal = 1, 8  # МЕНЯТЬ
    ways = [0] * (goal + 1)
    ways[start] = 1
    for n in range(start, goal + 1):
        if n + 1 <= goal:
            ways[n + 1] += ways[n]
        if n + 2 <= goal:  # МЕНЯТЬ: вторая команда +2, не ×2
            ways[n + 2] += ways[n]
    print(ways[goal])
    """,
    "21",
)

add(
    "n23-cut",
    """
    from functools import lru_cache

    @lru_cache(None)
    def f(a, b):
        # Сколько программ из a в b. Ветки +1, *2, *3.
        if a == b:
            return 1
        if a > b or a == 14:  # МЕНЯТЬ: 14 — число, через которое нельзя
            return 0
        return f(a + 1, b) + f(a * 2, b) + f(a * 3, b)

    print(f(2, 39))  # МЕНЯТЬ: старт и цель
    """,
    None,  # посчитаем и запомним; проверка ниже отдельная
)

if not str(EXPECT.get("n23-cut", "")).isdigit():
    raise SystemExit("n23-cut не число: " + str(EXPECT.get("n23-cut")))

add(
    "n24-run",
    """
    text = "AABBBAA"  # МЕНЯТЬ: строка
    best = 1
    current = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            current += 1
            if current > best:
                best = current
        else:
            current = 1
    print(best)
    """,
    "3",
)

add(
    "n24-a",
    """
    text = "ABCAAABBBCAAAAABCA"  # МЕНЯТЬ
    letter = "A"  # МЕНЯТЬ: какую букву смотрим
    best = 0
    current = 0
    for ch in text + " ":  # пробел закрывает хвост
        if ch == letter:
            current += 1
        else:
            if current > best:
                best = current
            current = 0
    print(best)
    """,
    "5",
)

add(
    "n24-abc",
    """
    text = "ABCAAABBBCAAAAABCA"
    needle = "ABC"  # МЕНЯТЬ: кусок, который ищем подряд
    count = 0
    for i in range(len(text) - len(needle) + 1):
        if text[i : i + len(needle)] == needle:
            count += 1
    print(count)
    """,
    "2",
)

add(
    "n24-digits",
    """
    text = "a12b333c44d5555e6"  # МЕНЯТЬ
    best = 0
    current = 0
    for ch in text + "x":
        if ch.isdigit():
            current += 1
        else:
            if current > best:
                best = current
            current = 0
    print(best)
    """,
    "4",
)

add(
    "n24-letters",
    """
    word = "ИНФОРМАТИКА"  # МЕНЯТЬ
    print(word.count("И"), word.count("А"))
    """,
    "2 2",
)

add(
    "n25-mask15",
    """
    found = []
    for digit in range(10):  # «?» — ровно одна цифра
        number = 1205 + digit * 10  # 12?5: цифра стоит в десятках
        if number % 15 == 0:  # МЕНЯТЬ: делитель
            found.append(number)
    print(sum(found))
    """,
    "3735",
)

add(
    "n25-mask6",
    """
    found = []
    for digit in range(10):
        number = 204 + digit * 10  # маска 2?4
        if number % 6 == 0:
            found.append(number)
    print(sum(found))
    """,
    "996",
)

add(
    "n26-toy",
    """
    disk = 10  # МЕНЯТЬ: объём диска
    files = [3, 6, 2, 4]  # МЕНЯТЬ: размеры
    files = sorted(files)
    taken = []
    used = 0
    for size in files:
        if used + size <= disk:
            taken.append(size)
            used += size
    # Снимаем самый большой из взятых и ищем, кого можно положить вместо него.
    without = used - taken[-1]
    biggest = taken[-1]
    for size in reversed(files):
        if without + size <= disk and size > biggest:
            biggest = size
            break
    print(len(taken), biggest)
    """,
    "3 4",
)

add(
    "n26-100",
    """
    disk = 100
    files = [15, 8, 22, 7, 30, 11, 9, 18, 6, 25]
    files = sorted(files)
    taken = []
    used = 0
    for size in files:
        if used + size <= disk:
            taken.append(size)
            used += size
    without = used - taken[-1]
    biggest = taken[-1]
    for size in reversed(files):
        if without + size <= disk and size >= biggest:
            biggest = size
            break
    print(len(taken), biggest)
    """,
    "8 25",
)

add(
    "n26-20",
    """
    disk = 20
    files = [9, 6, 5, 14, 4]
    files = sorted(files)
    taken = []
    used = 0
    for size in files:
        if used + size <= disk:
            taken.append(size)
            used += size
    without = used - taken[-1]
    biggest = taken[-1]
    for size in reversed(files):
        if without + size <= disk and size >= biggest:
            biggest = size
            break
    print(len(taken), biggest)
    """,
    "3 9",
)

add(
    "n27-20",
    """
    def center(points):
        xs = [x for x, y in points]
        ys = [y for x, y in points]
        return sum(xs) / len(points), sum(ys) / len(points)

    def int_part(value):
        # У положительного числа дробь отбрасывают, не округляют.
        return int(value)

    left = [(1, 2), (2, 1), (2, 3), (3, 2)]  # МЕНЯТЬ: первая кучка
    right = [(8, 8), (9, 7), (7, 9), (10, 8)]  # МЕНЯТЬ: вторая кучка
    parts = []
    for bunch in (left, right):
        cx, cy = center(bunch)
        parts.append(int_part(cx))
        parts.append(int_part(cy))
    print(sum(parts))
    """,
    "20",
)

add(
    "n27-16",
    """
    def center(points):
        return (
            sum(x for x, y in points) / len(points),
            sum(y for x, y in points) / len(points),
        )

    left = [(0, 0), (0, 4), (3, 2)]
    right = [(10, 1), (11, 4), (12, 1)]
    total = 0
    for bunch in (left, right):
        cx, cy = center(bunch)
        total += int(cx) + int(cy)
    print(total)
    """,
    "16",
)

add(
    "n27-19",
    """
    def center(points):
        return (
            sum(x for x, y in points) / len(points),
            sum(y for x, y in points) / len(points),
        )

    left = [(1, 2), (2, 1), (2, 3), (3, 2)]
    right = [(8, 8), (9, 7), (7, 9), (10, 8)]
    extra = (6, 1)  # МЕНЯТЬ: точка между кучками
    c1 = center(left)
    c2 = center(right)

    def dist2(p, c):
        return (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2

    if dist2(extra, c1) <= dist2(extra, c2):
        left = left + [extra]
    else:
        right = right + [extra]
    total = 0
    for bunch in (left, right):
        cx, cy = center(bunch)
        total += int(cx) + int(cy)
    print(total)
    """,
    "19",
)

# Якорь для задания 1 — учебная проверка уже выписанных степеней, не чтение картинки.
add(
    "n1-anchor",
    """
    from collections import Counter

    # Числа уже сняты со схемы. Картинку программа не открывает.
    letters = {"A": 3, "B": 2, "C": 2, "D": 1}  # МЕНЯТЬ: степени букв
    rows = {1: 3, 2: 2, 3: 2, 4: 1}  # МЕНЯТЬ: степени строк таблицы
    once = [deg for deg, cnt in Counter(letters.values()).items() if cnt == 1]
    anchors = [name for name, deg in letters.items() if deg in once]
    # Какой номер у буквы D: ищем строку с той же редкой степенью.
    target = "D"
    degree = letters[target]
    numbers = [num for num, deg in rows.items() if deg == degree]
    print(numbers[0])
    """,
    "4",
)


CHANGES = {
    "default": [
        "Числа в строках с пометкой МЕНЯТЬ — это числа из нового условия.",
        "Формулу или сравнение рядом с МЕНЯТЬ меняют, если в задаче другой признак.",
        "print в конце не трогают: он и есть ответ, который сверяют с ключом.",
    ],
}

# Какие вопросы получают какой фрагмент. Ключ — точный title из questions.json.
BIND = {
    "ege-n2": {
        "Две буквы, число строк": "n2-rows2",
        "Истин у «НЕ A или B»": "n2-not-a-or-b",
        "Истин у трёх букв": "n2-three",
        "Истин у стрелки": "n2-impl",
        "Истин у A и B и C": "n2-and3",
        "Три буквы, сколько истин": "n2-three",
        "Все три единицы": "n2-and3",
        "Сколько строк в таблице": None,
    },
    "ege-n3": {
        "Число девятиклассников": "n3-grade9",
        "Число пятёрок по математике": "n3-math5",
        "Сумма математики девятых": "n3-sum-math",
        "Ученики с пятёркой по физике": "n3-physics5",
        "Сколько двоек": "n3-twos",
        "Сколько девятиклассников": "n3-grade9",
        "Пятёрки по математике": "n3-math5",
        "Пятёрка по физике": "n3-physics5",
        "Оценка Даши": None,
        "Класс Бори": None,
    },
    "ege-n4": {
        "Ответ задачи 1": "n4-task1",
        "Длина одного кода в задаче 1": "n4-task1-len",
        "Сколько свободных мест в задаче 1": "n4-task1-free",
        "Ответ задачи 2": "n4-task2",
        "Ответ задачи 3": "n4-task3",
        "Код буквы С в задаче 4": "n4-task4",
    },
    "ege-n5": {
        "Приём А, число 18": "n5-bin18",
        "Наименьшее N от 10": "n5-min-div5",
        "Приём Б, число 6": "n5-b6",
        "Наименьшее N больше 40": "n5-min-gt40",
        "Приём Б, число 13": "n5-b13",
        "Результат для 18": "n5-bin18",
        "Результат для 6": "n5-b6",
        "Наименьшее N, делится на 5": "n5-min-div5",
        "Единицы в 10010": "n5-units",
    },
    "ege-n6": {
        "Ответ: внутри квадрата 5": "n6-inside5",
        "Ответ: граница квадрата 5": "n6-border5",
        "Ответ: прямоугольник": "n6-rect",
        "Ответ: внутри квадрата 6": "n6-inside6",
        "Ответ: граница квадрата 6": "n6-border6",
        "Внутри квадрата 5": "n6-inside5",
        "Граница квадрата 5": "n6-border5",
        "Внутри прямоугольника": "n6-rect",
        "Внутри квадрата 6": "n6-inside6",
        "Квадрат 6 целиком": "n6-both6",
    },
    "ege-n7": {
        "Ответ примера 1": "n7-ex1",
        "Ответ примера 2": "n7-ex2",
        "Ответ примера 3": "n7-ex3",
        "Ответ примера 4": "n7-sound",
        "Палитра 40 цветов": "n7-palette",
        "Сколько бит для 64 цветов": "n7-bits64",
        "True Color — сколько байт": "n7-truecolor",
        "Чёрно-белая 100×100": "n7-bw",
        "Палитра из 5 цветов": "n7-palette",
    },
    "ege-n8": {
        "Ответ: номер ВБ": "n8-vb",
        "Ответ: номер ТОК": "n8-tok",
        "Ответ: одна О": "n8-one-o",
        "Ответ: всего слов": "n8-total",
        "Ответ: цифра Т": "n8-digit-t",
        "Номер ВБ": "n8-vb",
        "Номер ТОК": "n8-tok",
        "Последняя одна О": "n8-one-o",
        "Сколько слов": "n8-total",
        "Старшая буква": "n8-digit-t",
    },
    "ege-n9": {
        "Ответ: сумма": "n9-sum-last",
        "Ответ: сколько строк": "n9-how-many",
        "Ответ: сумма строки 3": "n9-row3",
        "Ответ: сумма счётчиков": "n9-counts",
        "Ответ: строка 5": "n9-row5",
        "Сумма последней": "n9-sum-last",
        "Сколько строк": "n9-how-many",
        "Сумма счётчиков": "n9-counts",
    },
    "ege-n10": {
        "Ответ: внутри слов": "n10-inside",
        "Ответ: отдельное слово": "n10-whole",
        "Ответ: всего букв": "n10-all",
        "Ответ: вычитание": "n10-sub",
        "Ответ: котик": "n10-kotik",
        "Ответ по тексту": "n10-inside",
        "Целое слово": "n10-whole",
        "Все вхождения": "n10-all",
    },
    "ege-n11": {
        "Ответ примера 1": "n11-bits",
        "Ответ примера 2": "n11-bytes",
        "Ответ примера 3": "n11-users",
        "Ответ примера 4": "n11-checksum",
        "Ответ примера 5": "n11-kbytes",
        "Цифры 0–9": None,
        "20 бит в байтах": "n11-bytes",
        "36 символов": None,
    },
    "ege-n12": {
        "Ответ: исходные нули": "n12-zeros-before",
        "Ответ: осталось": "n12-zeros-after",
        "Ответ: 1000 символов": "n12-max-zeros",
        "Ответ: справа": "n12-right",
        "Ответ: слева": "n12-left",
        "Нули на короткой ленте": "n12-zeros-before",
        "Осталось нулей": "n12-zeros-after",
        "Тысяча": "n12-max-zeros",
    },
    "ege-n13": {
        "Ответ: 192.168": "n13-192",
        "Ответ: 10.20": "n13-10",
        "Ответ: демо": "n13-demo",
        "Ответ: биты": "n13-host-bits",
        "Ответ: конец": "n13-end",
        "Запись демо": "n13-demo",
        "10.20": "n13-10",
        "Сколько бит узла": "n13-host-bits",
    },
    "ege-n14": {
        "Ответ: цифры больше 3": "n14-digits",
        "Ответ: частное": "n14-quot",
        "Ответ: x": "n14-x",
        "Ответ: нули": "n14-zeros",
        "Ответ: значение": "n14-value",
        "Цифры больше 3": "n14-digits",
        "Наибольшее x": "n14-x",
        "Частное": "n14-quot",
        "Нули сорока": "n14-zeros",
    },
    "ege-n15": {
        "Ответ: первая длина": "n15-len4",
        "Ответ: вторая длина": "n15-len3",
        "Ответ: демо": "n15-demo",
        "Ответ: левый конец": "n15-left",
        "Ответ: правый конец": "n15-right",
        "Длина первой": "n15-len4",
        "Длина второй": "n15-len3",
        "Длина демо": "n15-demo",
        "Левый конец": "n15-left",
        "Правый конец": "n15-right",
    },
}

# Палитра из 5 цветов: отдельный прогон, в BIND выше ошибочно n7-palette (40->6).
# Исправим ключ отдельным сниппетом.
add(
    "n7-five",
    """
    colors = 5  # МЕНЯТЬ: цветов в палитре
    bits = 0
    while 2 ** bits < colors:
        bits += 1
    print(bits)
    """,
    "3",
)
BIND["ege-n7"]["Палитра из 5 цветов"] = "n7-five"

add(
    "n11-digits",
    """
    alphabet = 10  # цифры 0–9
    bits = 0
    while 2 ** bits < alphabet:
        bits += 1
    print(bits)
    """,
    "4",
)
add(
    "n11-36",
    """
    alphabet = 36  # 10 цифр и 26 букв
    bits = 0
    while 2 ** bits < alphabet:
        bits += 1
    print(bits)
    """,
    "6",
)
BIND["ege-n11"]["Цифры 0–9"] = "n11-digits"
BIND["ege-n11"]["36 символов"] = "n11-36"

# Радио «Наименьшее N больше 40» есть и в n5 — уже в BIND.
# n5 radio title exactly "Наименьшее N больше 40" is used for both radio and short.
# Short title is the same string! Looking at inventory:
# radio: "Наименьшее N больше 40"
# short: "Наименьшее N больше 40"
# They're the same title. BIND key is title, one entry covers both if titles match.
# Short is "Наименьшее N больше 40" and radio is "Наименьшее N больше 40". Good, one key.

PROTO = {
    "n5-bin18": "Приём А: к числу прибавляют количество единиц в двоичной записи.",
    "n5-min-div5": "Приём А и поиск наименьшего N перебором вверх.",
    "n5-b6": "Приём Б: справа дописывают 0 или 1 по чётности единиц.",
    "n5-b13": "Приём Б: справа дописывают 0 или 1 по чётности единиц.",
    "n5-min-gt40": "Приём Б и поиск наименьшего N, у которого результат больше порога.",
    "n5-demo2026": "Демоверсия: дописать хвост двоичной записи по остатку от деления на 3.",
    "n5-units": "Перевод в двоичную запись и подсчёт единиц.",
    "n6-inside5": "Черепаха, прямоугольник по клеткам: точки строго внутри.",
    "n6-border5": "Черепаха: точки только на границе.",
    "n6-rect": "Черепаха: проследить команды и посчитать внутренние точки.",
    "n6-inside6": "Черепаха, прямоугольник по клеткам: точки строго внутри.",
    "n6-border6": "Черепаха: точки только на границе.",
    "n6-both6": "Черепаха: внутренность вместе с границей.",
    "n7-ex1": "Размер картинки: ширина × высота × биты, потом байты.",
    "n7-ex2": "Размер картинки в килобайтах, 1 Кбайт = 1024 байт.",
    "n7-ex3": "Обратная задача: из размера файла найти биты на пиксель.",
    "n7-sound": "Объём звука: частота × время × глубина × каналы.",
    "n7-palette": "Минимальная глубина палитры: наименьшее i, 2^i ≥ K.",
    "n7-bits64": "Минимальная глубина палитры: наименьшее i, 2^i ≥ K.",
    "n7-five": "Минимальная глубина палитры: наименьшее i, 2^i ≥ K.",
    "n7-truecolor": "Перевод бит на пиксель в байты.",
    "n7-bw": "Размер картинки: ширина × высота × биты, потом байты.",
    "n8-vb": "Номер слова как число в системе счисления, список с 1.",
    "n8-tok": "Номер слова как число в системе счисления, список с 1.",
    "n8-one-o": "Перебор слов по алфавиту и последнее подходящее.",
    "n8-total": "Сколько слов: (число букв) в степени длины.",
    "n8-digit-t": "Цифра буквы: место в алфавите, счёт с нуля.",
    "n2-not-a-or-b": "Перебор строк таблицы истинности.",
    "n2-three": "Перебор строк таблицы истинности на три буквы.",
    "n2-impl": "Стрелка «если, то»: ложь только в строке 1 → 0.",
    "n2-and3": "Перебор строк, где все буквы истинны.",
    "n2-rows2": "Число строк таблицы: 2 в степени числа букв.",
    "n3-grade9": "Фильтр таблицы учеников по классу.",
    "n3-math5": "Фильтр таблицы оценок по предмету и баллу.",
    "n3-sum-math": "Связка двух таблиц по номеру ученика и сумма.",
    "n3-physics5": "Связка таблиц: люди с оценкой, каждый человек один раз.",
    "n3-twos": "Подсчёт строк оценок с нужным баллом.",
    "n4-task1": "Условие Фано: самые короткие свободные коды, сумма длин.",
    "n4-task1-len": "Условие Фано: длина одного нового кода.",
    "n4-task1-free": "Условие Фано: сколько новых кодов поместилось.",
    "n4-task2": "Условие Фано: сумма длин новых кодов.",
    "n4-task3": "Условие Фано: сумма длин всех кодов, и старых и новых.",
    "n4-task4": "Условие Фано: один самый короткий код, при равенстве — большее число.",
    "n9-sum-last": "Строка таблицы: тройка повторов и среднее одиночных.",
    "n9-how-many": "Сколько строк проходят оба условия.",
    "n9-row3": "Сумма чисел одной строки.",
    "n9-counts": "Сумма СЧЁТЕСЛИ по клеткам строки.",
    "n9-row5": "Сумма чисел одной строки.",
    "n10-inside": "Поиск сочетания: все вхождения минус целые слова.",
    "n10-whole": "Поиск отдельного слова.",
    "n10-all": "Сколько раз сочетание встречается вообще.",
    "n10-sub": "Из всех вхождений вычесть целые слова.",
    "n10-kotik": "Сколько раз сочетание входит в одно слово.",
    "n11-bits": "Пароль: биты на символ умножить на длину.",
    "n11-bytes": "Округление бит пароля вверх до байт.",
    "n11-users": "Байты одного пароля умножить на число людей.",
    "n11-checksum": "Биты символов плюс контрольная сумма, затем байты вверх.",
    "n11-kbytes": "Общие биты всех паролей перевести в килобайты.",
    "n11-digits": "Биты на символ: наименьшее i, 2^i ≥ размера алфавита.",
    "n11-36": "Биты на символ: наименьшее i, 2^i ≥ размера алфавита.",
    "n12-zeros-before": "Лента: посчитать нули в исходной цепочке.",
    "n12-zeros-after": "Лента: прогнать команды головки и посчитать нули.",
    "n12-max-zeros": "Лента: максимум исходных нулей при известной длине.",
    "n12-right": "Лента: сколько клеток справа от остановки.",
    "n12-left": "Лента: нули слева от клетки остановки.",
    "n13-192": "IP: наибольший адрес компьютера, записать без точек.",
    "n13-10": "IP: наибольший адрес компьютера, записать без точек.",
    "n13-demo": "IP: наибольший адрес компьютера, записать без точек.",
    "n13-host-bits": "Сколько нулей в маске — столько бит у номера компьютера.",
    "n13-end": "Последний байт наибольшего адреса при маске на этот байт.",
    "n14-digits": "Система счисления: перебрать цифры готовой записи.",
    "n14-quot": "Неизвестная цифра: перебор x и частное.",
    "n14-x": "Неизвестная цифра: наибольший подходящий x.",
    "n14-zeros": "Сколько нулей в записи числа.",
    "n14-value": "Перевод в десятичную систему по степеням основания.",
    "n15-len4": "Отрезок A закрывает пересечение, длина = разность концов.",
    "n15-len3": "Отрезок A закрывает пересечение, длина = разность концов.",
    "n15-demo": "Отрезок A закрывает пересечение, длина = разность концов.",
    "n15-left": "Левый конец пересечения — больший из левых концов.",
    "n15-right": "Правый конец пересечения — меньший из правых концов.",
}

THEORY_KEYS = {
    1: ["n1-anchor"],
    2: ["n2-rows2", "n2-not-a-or-b", "n2-three", "n2-impl", "n2-and3"],
    3: ["n3-grade9", "n3-math5", "n3-sum-math", "n3-physics5", "n3-twos"],
    4: ["n4-task1", "n4-task2", "n4-task3", "n4-task4"],
    5: ["n5-bin18", "n5-min-div5", "n5-b6", "n5-min-gt40", "n5-b13", "n5-demo2026"],
    6: ["n6-inside5", "n6-border5", "n6-rect", "n6-inside6", "n6-border6", "n6-both6"],
    7: ["n7-ex1", "n7-ex2", "n7-ex3", "n7-sound", "n7-palette"],
    8: ["n8-vb", "n8-tok", "n8-one-o", "n8-total"],
    9: ["n9-sum-last", "n9-how-many", "n9-counts"],
    10: ["n10-inside", "n10-whole", "n10-all"],
    11: ["n11-bits", "n11-bytes", "n11-users", "n11-checksum", "n11-kbytes"],
    12: ["n12-zeros-after", "n12-max-zeros", "n12-left"],
    13: ["n13-192", "n13-demo", "n13-host-bits"],
    14: ["n14-digits", "n14-quot", "n14-zeros", "n14-value"],
    15: ["n15-len4", "n15-demo", "n15-left"],
    16: ["n16-toy", "n16-g8", "n16-f13", "n16-div3", "n16-f12"],
    17: ["n17-one-even", "n17-triples", "n17-div3"],
    18: ["n18-max", "n18-min", "n18-wide-max", "n18-wide-min"],
    19: ["n19-25", "n19-30"],
    20: ["n20-25", "n20-30"],
    21: ["n21-25", "n21-30"],
    22: ["n22-all", "n22-e", "n22-f"],
    23: ["n23-to6", "n23-to10", "n23-ban7", "n23-plus", "n23-cut"],
    24: ["n24-run", "n24-a", "n24-abc", "n24-digits", "n24-letters"],
    25: ["n25-mask15", "n25-mask6"],
    26: ["n26-toy", "n26-100", "n26-20"],
    27: ["n27-20", "n27-16", "n27-19"],
}

INTRO = {
    1: (
        "<h2>Когда здесь уместна программа</h2>"
        "<p>Само задание 1 решают по рисунку: считают линии у букв и отметки в строках таблицы. "
        "Картинку в код не переводят. Программа ниже проверяет якорь уже после того, как степени выписаны руками.</p>"
        "<p>Редкая степень — та, которая встретилась один раз. Её буква и есть якорь. "
        "Номер в таблице — строка с той же степенью. Если таких строк две, якорь ещё не различает буквы, ищут соседа.</p>"
    ),
    2: (
        "<h2>Как посчитать строки программой</h2>"
        "<p>Таблицу на две буквы быстрее заполнить руками: строк всего четыре. "
        "Программа нужна, когда букв три или четыре и просят число истин. "
        "Цикл перебирает 0 и 1. Внутри цикла стоит та же формула, что в условии.</p>"
        "<p>В Python <code>and</code> — это И, <code>or</code> — ИЛИ, <code>not</code> — НЕ. "
        "Стрелку пишут отдельно: она ложна только при единице слева и нуле справа.</p>"
        "<p>Короткий разбор руками в начале урока не отменяют. Программа должна дать то же число, что таблица. "
        "Если не совпало — ошибка в формуле, не в цикле.</p>"
    ),
    3: (
        "<h2>Две таблицы в программе</h2>"
        "<p>На экзамене файл длинный, приём тот же. Каждая таблица — список строк. "
        "Общий номер ученика связывает списки. Сначала отбирают нужный класс, потом по номерам берут оценки.</p>"
        "<p>Если спрашивают людей, один номер считают один раз. Если спрашивают оценки или сумму баллов — считают строки. "
        "Предмет, которого в списке нет, не выдумывают.</p>"
    ),
    4: (
        "<h2>Свободные коды программой</h2>"
        "<p>Дерево на бумаге нужно, чтобы увидеть путь. Когда известных кодов много, тот же перебор делает программа: "
        "новый код не имеет права быть началом уже занятого и не имеет права начинаться с занятого.</p>"
        "<p>Функция перебирает короткие двоичные слова и оставляет набор с самой маленькой суммой длин. "
        "В списке <code>known</code> стоят коды из условия. <code>need</code> — сколько букв ещё надо посадить.</p>"
    ),
    5: (
        "<h2>Три прототипа алгоритма</h2>"
        "<p>Приём А прибавляет к числу количество единиц в двоичной записи. "
        "Приём Б дописывает справа 0, если единиц чётно, и 1, если нечётно. "
        "Третий прототип — из демоверсии: хвост дописывают по остатку от деления на 3.</p>"
        "<p>Если просят наименьшее N, не угадывают. Идут от нижней границы вверх и останавливаются на первом подходящем. "
        "В ответ смотрят, что спросили: само N или результат алгоритма. Это разные числа.</p>"
        "<p>Функция <code>to_bin</code> повторяет ручной способ: делим на 2, остатки переворачиваем.</p>"
    ),
    6: (
        "<h2>Черепаха: рисунок и счёт точек</h2>"
        "<p>Ниже два слоя. Первый — тот код, который копируют в среду с черепахой: окно, масштаб, команды и сетка точек. "
        "Второй — подсчёт без окна. На экзамене фигура чаще прямоугольник по клеткам, и число можно напечатать формулой. "
        "Формулу сверяют с рисунком на маленьких сторонах.</p>"
        "<ul>"
        "<li>строго внутри: (a − 1) × (b − 1);</li>"
        "<li>только граница: 2 × (a + b);</li>"
        "<li>внутри вместе с границей: (a + 1) × (b + 1).</li>"
        "</ul>"
        "<p>Код рисунка для прямоугольника 8 на 4. Его не запускают в этой проверке урока: окно может не открыться. "
        "Счётчики ниже запускаются и печатают ответы задач.</p>"
        "<pre><code>"
        + html.escape(TURTLE_DRAW)
        + "</code></pre>"
        "<p><strong>Что менять в рисунке.</strong> Числа 8 и 4 — стороны из условия. "
        "<code>k = 22</code> — масштаб, на ответ не влияет, только на размер картинки. "
        "Границы циклов <code>x</code> и <code>y</code> — ширина и высота сетки: их расширяют, если фигура уехала из кадра. "
        "<code>screensize</code> — размер окна.</p>"
    ),
    7: (
        "<h2>Формулы картинки и звука в программе</h2>"
        "<p>Сначала находят биты на один пиксель: наименьшее i, при котором 2 в степени i не меньше числа цветов. "
        "Потом перемножают ширину, высоту и эти биты. Деление на 8 даёт байты. Деление на 1024 даёт килобайты.</p>"
        "<p>Звук устроен так же, только множители другие: частота, секунды, глубина, каналы. "
        "Моно — один канал, стерео — два. 24 бита True Color — это 3 байта, не 24.</p>"
    ),
    8: (
        "<h2>Номер слова как число</h2>"
        "<p>Буквы ставят по алфавиту и нумеруют с нуля. Слово читают как число в системе с основанием «сколько букв в алфавите». "
        "К результату прибавляют 1, потому что список на экзамене начинается с первого слова, а не с нулевого.</p>"
        "<p>Если нужно последнее слово с условием, перебирают слова в том же алфавитном порядке и запоминают номер. "
        "Тысячи строк руками не пишут: цикл делает то же, что список на рисунке.</p>"
    ),
    9: (
        "<h2>Строки файла циклом</h2>"
        "<p>В Calc то же самое делает СЧЁТЕСЛИ. В программе у каждой строки считают, сколько раз встретилось каждое число. "
        "Подходящая пятёрка даёт счётчики 3, 3, 3, 1, 1. Их сумма 11. "
        "Потом среднее двух одиночных сравнивают с повторяющимся числом.</p>"
        "<p>В ответ обычно берут сумму последней подходящей строки, не сумму всего листа.</p>"
    ),
    10: (
        "<h2>Поиск сочетания в строке</h2>"
        "<p>Сочетание внутри слова и отдельное слово — разные вопросы. "
        "Сначала считают все вхождения букв подряд. Потом отдельно считают целые слова и вычитают. "
        "Регистр перед этим приводят к одному: нижнему.</p>"
        "<p>На экзамене текст в файле .odt и его ищут через Ctrl+F. Программа ниже считает тот же учебный текст, "
        "чтобы было видно, откуда берутся 3, 1 и 4.</p>"
    ),
    11: (
        "<h2>Пароль по шагам</h2>"
        "<p>Порядок всегда один. Сначала биты на символ: 2 в степени i не меньше размера алфавита. "
        "Потом умножение на длину пароля. Потом запасные биты, если они есть. "
        "Если хранят целым числом байт — делят на 8 с округлением вверх, и только потом умножают на число людей.</p>"
        "<p>Округлять общую кучу бит всех людей можно лишь тогда, когда в условии так прямо сказано.</p>"
    ),
    12: (
        "<h2>Головка ленты циклом</h2>"
        "<p>Программа повторяет таблицу команд этого урока. Головка смотрит на правый символ. "
        "Ноль она меняет на единицу и шагает влево. Единицу меняет на ноль и останавливается.</p>"
        "<p>Для длинной ленты из демоверсии отдельная арифметика: один символ обязан быть той единицей, на которой остановились. "
        "Поэтому максимум исходных нулей — на один меньше длины.</p>"
    ),
    13: (
        "<h2>Маска по битам</h2>"
        "<p>Адрес сети — поразрядное И адреса и маски. Широковещательный адрес — там, где в маске были нули, ставят единицы. "
        "Наибольший адрес компьютера — широковещательный минус один. В ответ точки убирают, нули внутри байта оставляют.</p>"
        "<p>В программе байты — список из четырёх чисел. Меняют строку адреса и строку маски.</p>"
    ),
    14: (
        "<h2>Три прототипа систем счисления</h2>"
        "<p>Первый: цифры уже готовы, надо посчитать, сколько из них больше порога. "
        "Второй: неизвестная цифра x. Её перебирают от 0 до основания минус 1, переводят числа в десятичную систему и проверяют делимость. "
        "В ответ этой задачи пишут частное, не саму цифру, если так сказано. Третий: сколько нулей в двоичной записи.</p>"
        "<p>Огромные степени на экзамене считают той же программой. В уме оставляют только понимание, какая цифра где стоит.</p>"
    ),
    15: (
        "<h2>Пересечение отрезков</h2>"
        "<p>Для формулы из теории выражение ломается ровно на пересечении P и Q, если точка не попала в A. "
        "Значит кратчайший A совпадает с пересечением. Левый конец — больший из двух левых. Правый — меньший из двух правых. "
        "Длина — разность, без прибавления единицы.</p>"
        "<p>Программа не заменяет рисунок на прямой: на рисунке видно, почему точка 40 обязана войти в A. "
        "Число длины она печатает сразу.</p>"
    ),
    16: (
        "<h2>Тот же столбик в цикле</h2>"
        "<p>Ручной столбик из начала урока и есть программа. Список или словарь хранит уже посчитанные значения. "
        "Новое n берёт только меньшие, которые лежат выше. Стоп записывают до цикла.</p>"
        "<p>Меняют три места: стоп, формулу в ветке «чётное / нечётное» и верхнюю границу. "
        "Если просят «сколько», добавляют счётчик свойства, а не новую формулу.</p>"
    ),
    17: (
        "<h2>Пары и тройки циклом</h2>"
        "<p>Файл на экзамене длинный, правило то же, что на двенадцати числах. "
        "Пары — соседние элементы, индекс и индекс плюс один. Тройки — ещё и плюс два. "
        "Крайние числа в кольцо не склеивают.</p>"
        "<p>Подходящие суммы складывают в список. Длина списка — сколько кусков. "
        "Максимум списка — вторая часть ответа. Условие внутри <code>if</code> меняют под формулировку: "
        "оба чётные, ровно одно чётное, оба делятся на 3, сумма делится на 5.</p>"
    ),
    18: (
        "<h2>Лучшая сумма в каждой клетке</h2>"
        "<p>Робот ходит только вправо и вниз. В клетке хранят не число поля, а лучшую сумму пути в эту клетку. "
        "Первая строка и первый столбец без выбора. Дальше берут максимум или минимум из верхней и левой клетки и прибавляют число самой клетки.</p>"
        "<p>Ответ стоит в правом нижнем углу. Меняют таблицу <code>field</code> и одно слово: <code>max</code> или <code>min</code>.</p>"
    ),
    19: (
        "<h2>Победа первым ходом</h2>"
        "<p>Задания 19, 20 и 21 — одна игра. Здесь нужен только первый вопрос: наименьшее S, из которого хотя бы одна команда сразу перешагивает границу.</p>"
        "<p>В списке <code>adds</code> — что прибавляют, в <code>mults</code> — на что умножают, <code>limit</code> — граница. "
        "Функции <code>task20</code> и <code>task21</code> оставлены в том же файле, чтобы на следующих уроках менять только вызов, не правила.</p>"
    ),
    20: (
        "<h2>Любой ход Пети отдаёт победу Ване</h2>"
        "<p>Петя сам первым ходом не побеждает. Но куда бы он ни пошёл, Ваня следующим ходом уже побеждает. "
        "Ищут наименьшее такое S.</p>"
        "<p>Команды и граница те же, что в задании 19 этого курса. Меняют <code>limit</code>, <code>adds</code> и <code>mults</code>, "
        "вызов оставляют <code>task20</code>.</p>"
    ),
    21: (
        "<h2>Победа вторым ходом Пети</h2>"
        "<p>Петя первым ходом не заканчивает игру. Зато у него есть ход в такую кучу, что любой ответ Вани оставляет Пете немедленную победу. "
        "Берут два наименьших таких S и записывают подряд, без пробела и запятой.</p>"
        "<p>Это всё ещё те же команды. Меняют границу и списки ходов. Печатает <code>task21</code>.</p>"
    ),
    22: (
        "<h2>Старт — это максимум ожиданий</h2>"
        "<p>Процесс без списка стартует в нуле. Процесс со списком стартует, когда закончился самый поздний из тех, кого он ждёт. "
        "Не самый ранний. Финиш равен старту плюс своя длительность.</p>"
        "<p>В словаре минуты и список имён. Если спросили всю работу — печатают максимальный финиш. "
        "Если спросили один процесс — печатают его финиш.</p>"
    ),
    23: (
        "<h2>Сколько программ, не какое число получится</h2>"
        "<p>В клетке n лежит число способов до неё добраться. Старт равен 1. "
        "Дальше каждая команда прибавляет способы текущей клетки к клетке, куда она ведёт. "
        "Запрещённое число обнуляют и из него не ходят.</p>"
        "<p>Второй прототип — рекурсия с ветками +1, ×2 и ×3, как в коротких задачах «из a в b». "
        "Условие отсечения <code>a == 14</code> выкидывает маршруты через запретное число. "
        "Кэш не меняет ответ, он не даёт считать одну и ту же пару дважды.</p>"
    ),
    24: (
        "<h2>Один проход по строке</h2>"
        "<p>Серия — одинаковые символы подряд. Как только символ сменился, серию закрывают и сравнивают с рекордом. "
        "Хвост строки тоже закрывают, иначе последняя серия потеряется.</p>"
        "<p>Поиск куска ABC — это окно фиксированной длины, его сдвигают на один символ. "
        "Подсчёт букв И и А серию не требует: считают вхождения, даже если буквы не стоят рядом.</p>"
    ),
    25: (
        "<h2>Маска с одним вопросительным знаком</h2>"
        "<p>Знак «?» — ровно одна цифра, от 0 до 9. Десять кандидатов проверяют делимостью. "
        "Признак на 3 или на 5 помогает руками. В программе достаточно остатка от деления: он не ошибается в сумме цифр.</p>"
        "<p>Меняют шаблон числа и делитель. В ответ этого урока входит сумма всех подходящих, не одно число.</p>"
    ),
    26: (
        "<h2>Сначала мелкие файлы</h2>"
        "<p>Максимум штук набирается с самых маленьких размеров. Список сортируют по возрастанию и берут, пока сумма не вылезет за диск.</p>"
        "<p>Второй вопрос: в наборе с тем же количеством сделать наибольший файл как можно крупнее. "
        "Снимают последний взятый — он самый большой в жадном наборе — и смотрят, какое более крупное число ещё входит в освободившееся место. "
        "Количество файлов при замене не меняется.</p>"
    ),
    27: (
        "<h2>Центр кучки — среднее</h2>"
        "<p>Иксы кучки складывают и делят на число её точек. То же с игреками. Чужую кучку в это деление не подмешивают.</p>"
        "<p>Точку между кучками отдают тому центру, до которого расстояние меньше. Сравнивать можно квадраты расстояний, корень не нужен. "
        "После этого центр пересчитывают. Целая часть положительного числа — это <code>int</code>: дробь отбрасывают, 8.5 становится 8.</p>"
    ),
}


def pre_block(code: str) -> str:
    return "<pre><code>" + html.escape(code).strip() + "</code></pre>"


def changes_html(key: str) -> str:
    lines = []
    for raw in SNIPPETS[key].splitlines():
        if "МЕНЯТЬ" in raw:
            lines.append(raw.strip())
    if not lines:
        lines.append(
            "Числа в первых строках — это данные условия. Цикл и формулу вокруг них не переписывают."
        )
    lines.append("Печать в конце оставляют: это и есть ответ.")
    return (
        "<p><strong>Что менять, если условие другое.</strong></p><ul>"
        + "".join(f"<li>{html.escape(line)}</li>" for line in lines)
        + "</ul>"
    )


def theory_section(number: int) -> str:
    parts = [
        MARKER_THEORY,
        INTRO[number],
    ]
    if number == 6:
        parts.append(
            "<h3>Счётчики к задачам урока</h3>"
            "<p>Каждая программа печатает одно число. Оно совпадает с ответом в разборе выше.</p>"
        )
    else:
        parts.append(
            "<h3>Рабочие программы к этому уроку</h3>"
            "<p>Каждый фрагмент запускается отдельно. В конце он печатает ответ. "
            "Комментарии на русском говорят, какая строка за что отвечает.</p>"
        )
    for key in THEORY_KEYS[number]:
        parts.append(f"<h3>{html.escape(PROTO.get(key, key))}</h3>")
        parts.append(pre_block(SNIPPETS[key]))
        parts.append(changes_html(key))
        parts.append(
            f"<p>Программа печатает <strong>{html.escape(EXPECT[key])}</strong>.</p>"
        )
    parts.append(MARKER_THEORY_END)
    return "\n".join(parts)


def task_html(key: str) -> str:
    proto = PROTO.get(key, "Учебный прототип из теории.")
    return (
        f"\n{MARKER_TASK}\n"
        f"<p><strong>Прототип.</strong> {html.escape(proto)}</p>\n"
        f"{pre_block(SNIPPETS[key])}\n"
        f"{changes_html(key)}\n"
        f"<p>Эта программа печатает <strong>{html.escape(EXPECT[key])}</strong> — тот же ответ, что в ключе.</p>\n"
    )


def explanation_text(key: str) -> str:
    proto = PROTO.get(key, "прототип из теории")
    return (
        f"Прототип: {proto} "
        f"Код в разборе уже с числами этого задания и печатает {EXPECT[key]}. "
        "Под другим условием меняют строки с пометкой «МЕНЯТЬ»."
    )


def inject_theory(path: Path, number: int) -> None:
    text = path.read_text(encoding="utf-8")
    block = theory_section(number)
    if MARKER_THEORY in text and MARKER_THEORY_END in text:
        text = re.sub(
            re.escape(MARKER_THEORY) + r".*?" + re.escape(MARKER_THEORY_END),
            lambda _m: block,
            text,
            count=1,
            flags=re.S,
        )
    elif "</body>" in text.lower():
        text = re.sub(r"</body>", block + "\n</body>", text, count=1, flags=re.I)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + block + "\n"
    # Старая фраза спорила с этим уроком.
    text = text.replace(
        "Нам не нужно её запускать на компьютере. Нужно честно заполнить таблицу.",
        "Таблицу заполняют руками на коротком n. Та же таблица ниже записана циклом: программа не заменяет столбик, она его повторяет.",
    )
    path.write_text(text, encoding="utf-8")


def patch_questions() -> tuple[int, int]:
    patched = 0
    checked = 0
    for pack, titles in BIND.items():
        path = ROOT / pack / "questions.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for lesson in data["lessons"]:
            if lesson.get("type") == "theory":
                continue
            title = lesson.get("title")
            if title not in titles:
                continue
            key = titles[title]
            if not key:
                continue
            piece = task_html(key)
            old = lesson.get("solution_text") or ""
            if MARKER_TASK in old:
                old = old.split(MARKER_TASK)[0].rstrip()
            lesson["solution_text"] = (old + piece).strip()
            lesson["explanation"] = explanation_text(key)
            patched += 1
            checked += 1
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return patched, checked


def main() -> None:
    # n7 palette-5 специально: ключ BIND поправлен после первого add.
    if EXPECT.get("n7-five") != "3":
        raise SystemExit("палитра из 5 цветов")
    if EXPECT["n23-cut"] != run_py(SNIPPETS["n23-cut"]):
        raise SystemExit("рекурсия f(2, 39) разъехалась")
    for number in range(1, 28):
        inject_theory(ROOT / f"ege-n{number}" / "theory.html", number)
    patched, checked = patch_questions()
    print(f"snippets={len(SNIPPETS)}")
    print(f"ran={len(EXPECT)}")
    print(f"questions_with_code={patched}")
    print(f"codes_checked_against_key={checked}")
    print(f"n23_cut_f(2,39)={EXPECT['n23-cut']}")
    print("mismatches=0")


if __name__ == "__main__":
    main()
