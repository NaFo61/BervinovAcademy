#!/usr/bin/env python3
"""Вопросы к заданиям 16–27 и три контрольные.

Ответы считаются здесь же и сверяются с разборами из теории.
Повторный запуск заменяет только эти вопросы, теорию не трогает.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READY = ROOT / "к-импорту"


def f_plus_n(n: int, stop: int = 1) -> int:
    values = {1: stop}
    for current in range(2, n + 1):
        values[current] = values[current - 1] + current
    return values[n]


def g_even_odd(n: int) -> int:
    values = {1: 1, 2: 2}
    for current in range(3, n + 1):
        if current % 2:
            values[current] = values[current - 1] - values[current - 2]
        else:
            values[current] = values[current - 1] + values[current - 2]
    return values[n]


def f_half_or_plus(n: int) -> int:
    values = {1: 1}
    for current in range(2, n + 1):
        if current % 2 == 0:
            values[current] = values[current // 2]
        else:
            values[current] = values[current - 1] + 1
    return values[n]


def fib_like_count(limit: int, divisor: int) -> int:
    values = {1: 1, 2: 2}
    good = 0
    for current in range(1, limit + 1):
        if current >= 3:
            values[current] = values[current - 1] + values[current - 2]
        if values[current] % divisor == 0:
            good += 1
    return good


def f_half_add(n: int) -> int:
    values = {1: 2}
    for current in range(2, n + 1):
        if current % 2 == 0:
            values[current] = values[current // 2] + current
        else:
            values[current] = values[current - 1] + 1
    return values[n]


def pair_stats(numbers: list[int], pred) -> tuple[int, int]:
    """Соседние пары, как в уроке: (1,2), (2,3), а не все сочетания."""
    count = 0
    best = None
    for index in range(len(numbers) - 1):
        a, b = numbers[index], numbers[index + 1]
        if not pred(a, b):
            continue
        count += 1
        total = a + b
        if best is None or total > best:
            best = total
    return count, int(best or 0)


def triple_stats(numbers: list[int]) -> tuple[int, int]:
    count = 0
    best = None
    for index in range(len(numbers) - 2):
        total = numbers[index] + numbers[index + 1] + numbers[index + 2]
        if total % 5:
            continue
        count += 1
        if best is None or total > best:
            best = total
    return count, int(best or 0)


def grid_ends(grid: list[list[int]]) -> tuple[int, int]:
    rows, cols = len(grid), len(grid[0])
    best = [[0] * cols for _ in range(rows)]
    worst = [[0] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            cell = grid[row][col]
            if row == 0 and col == 0:
                best[row][col] = worst[row][col] = cell
            elif row == 0:
                best[row][col] = best[row][col - 1] + cell
                worst[row][col] = worst[row][col - 1] + cell
            elif col == 0:
                best[row][col] = best[row - 1][col] + cell
                worst[row][col] = worst[row - 1][col] + cell
            else:
                best[row][col] = max(best[row - 1][col], best[row][col - 1]) + cell
                worst[row][col] = min(worst[row - 1][col], worst[row][col - 1]) + cell
    return best[-1][-1], worst[-1][-1]


def game_sets(target: int, adds: tuple[int, ...], muls: tuple[int, ...]):
    def nxt(value: int) -> list[int]:
        return [value + add for add in adds] + [value * mul for mul in muls]

    win_now = set()
    lose = set()
    win_later = set()
    for value in range(target - 1, 0, -1):
        if any(step >= target for step in nxt(value)):
            win_now.add(value)
    for value in range(target - 1, 0, -1):
        if value in win_now:
            continue
        steps = nxt(value)
        if steps and all(step in win_now for step in steps):
            lose.add(value)
    for value in range(target - 1, 0, -1):
        if value in win_now or value in lose:
            continue
        if any(step in lose for step in nxt(value)):
            win_later.add(value)
    return win_now, lose, win_later


def two_smallest(values: set[int]) -> str:
    first, second = sorted(values)[:2]
    return f"{first}{second}"


def schedule(jobs: list[tuple[str, int, tuple[str, ...]]]) -> dict[str, int]:
    done: dict[str, int] = {}
    left = list(jobs)
    while left:
        moved = False
        for name, duration, deps in list(left):
            if not all(dep in done for dep in deps):
                continue
            start = max((done[dep] for dep in deps), default=0)
            done[name] = start + duration
            left.remove((name, duration, deps))
            moved = True
        if not moved:
            raise RuntimeError(left)
    return done


def ways(goal: int, ops: list, ban: int | None = None) -> int:
    counts = [0] * (goal + 1)
    counts[1] = 1
    for value in range(1, goal):
        if ban is not None and value == ban:
            continue
        if counts[value] == 0:
            continue
        for op in ops:
            landed = op(value)
            if landed == ban or landed < 1 or landed > goal:
                continue
            counts[landed] += counts[value]
    return counts[goal]


def max_run(text: str, only: str | None = None) -> int:
    best = 0
    current = 0
    previous = ""
    for char in text:
        if only is not None and char != only:
            current = 0
            previous = char
            continue
        if char == previous:
            current += 1
        else:
            current = 1
            previous = char
        if only is None or char == only:
            best = max(best, current)
    return best


def max_digit_run(text: str) -> int:
    best = current = 0
    for char in text:
        if char.isdigit():
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def mask_sum(pattern: str, divisor: int) -> tuple[list[int], int]:
    found = []
    for digit in range(10):
        number = int(pattern.replace("?", str(digit)))
        if number % divisor == 0:
            found.append(number)
    return found, sum(found)


def disk_pack(capacity: int, files: list[int]) -> tuple[int, int]:
    ordered = sorted(files)
    chosen: list[int] = []
    total = 0
    for size in ordered:
        if total + size <= capacity:
            chosen.append(size)
            total += size
    base = sum(chosen[:-1])
    largest = chosen[-1]
    for size in sorted(files, reverse=True):
        if size <= largest:
            break
        if base + size <= capacity:
            largest = size
            break
    return len(chosen), largest


def center(points: list[tuple[float, float]]) -> tuple[float, float]:
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
    )


def integer_parts_sum(left, right) -> int:
    return int(left[0]) + int(left[1]) + int(right[0]) + int(right[1])


def check_known() -> None:
    assert f_plus_n(6) == 21
    assert f_plus_n(8) == 36
    assert g_even_odd(8) == 8
    assert g_even_odd(10) == 13
    assert f_half_or_plus(13) == 3
    assert f_half_or_plus(20) == 2
    assert fib_like_count(20, 3) == 5
    assert fib_like_count(12, 3) == 3
    assert f_half_add(12) == 23
    assert f_half_add(9) == 17
    demo = [8, 6, 4, 15, 10, 2, 7, 12, 18, 3, 9, 14]
    assert pair_stats(demo, lambda a, b: a % 2 == 0 and b % 2 == 0) == (4, 30)
    practice = [8, 4, 7, 6, 2, 9, 10, 3]
    assert pair_stats(practice, lambda a, b: a % 2 == 0 and b % 2 == 0) == (2, 12)
    assert pair_stats(
        practice, lambda a, b: (a % 2 == 0) != (b % 2 == 0)
    ) == (5, 19)
    assert triple_stats([8, 6, 4, 15, 10, 2, 7, 12, 18, 3, 9, 14])[0] >= 2
    assert grid_ends([[2, 4, 1], [3, 1, 5], [2, 6, 1]]) == (14, 12)
    assert grid_ends([[1, 4, 2], [3, 1, 5], [2, 6, 2]]) == (14, 12)
    win, lose, later = game_sets(10, (1,), (2,))
    assert min(win) == 5 and min(lose) == 4 and two_smallest(later) == "23"
    win, lose, later = game_sets(25, (1, 2), (2,))
    assert min(win) == 13 and 12 in lose and two_smallest(later) == "610"
    win, lose, later = game_sets(30, (1, 4), (3,))
    assert min(win) == 10 and 9 in lose and two_smallest(later) == "35"
    chain = schedule(
        [
            ("A", 4, ()),
            ("B", 6, ()),
            ("C", 3, ("A",)),
            ("D", 5, ("A", "B")),
            ("E", 2, ("C", "D")),
        ]
    )
    assert chain["E"] == 13
    fresh = schedule(
        [
            ("A", 3, ()),
            ("B", 5, ()),
            ("C", 2, ("A",)),
            ("D", 4, ("A", "B")),
            ("E", 6, ("C", "D")),
        ]
    )
    assert fresh["E"] == 15
    plus_double = [lambda x: x + 1, lambda x: x * 2]
    plus_two = [lambda x: x + 1, lambda x: x + 2]
    assert ways(6, plus_double) == 6
    assert ways(10, plus_double) == 14
    assert ways(10, plus_double, ban=7) == 8
    assert ways(4, plus_two) == 3
    assert ways(8, plus_two) == 21
    assert ways(7, plus_double) == 6
    assert max_run("AABBBAA") == 3
    assert max_run("ABCAAABBBCAAAAABCA", "A") == 5
    assert "ABCAAABBBCAAAAABCA".count("ABC") == 2
    assert max_digit_run("a12b333c44d5555e6") == 4
    assert max_run("AAABBC") == 3
    assert max_digit_run("ab11c222d3") == 3
    assert mask_sum("12?5", 15)[1] == 3735
    assert mask_sum("2?4", 6)[1] == 996
    assert mask_sum("3?6", 9) == ([306, 396], 702)
    assert disk_pack(10, [3, 6, 2, 4]) == (3, 4)
    assert disk_pack(100, [15, 8, 22, 7, 30, 11, 9, 18, 6, 25]) == (8, 25)
    assert disk_pack(20, [9, 6, 5, 14, 4]) == (3, 9)
    left = center([(1, 2), (2, 1), (2, 3), (3, 2)])
    right = center([(8, 8), (9, 7), (7, 9), (10, 8)])
    assert integer_parts_sum(left, right) == 20
    new_left = center([(1, 1), (1, 3), (3, 1)])
    new_right = center([(10, 10), (12, 10), (11, 13)])
    assert integer_parts_sum(new_left, new_right) == 24


def sol(steps: list[str], answer) -> str:
    items = "".join(f"<li>{step}</li>" for step in steps)
    return f"<ol>{items}</ol><p>Ответ: <strong>{answer}</strong>.</p>"


def checkbox(title: str, question: str, answers: list, steps: list[str]) -> dict:
    if not any(row[1] for row in answers):
        raise ValueError(title)
    return {
        "type": "checkbox",
        "title": title,
        "question_text": question,
        "points": 4,
        "answers": answers,
        "solution_text": sol(steps, "отмечены верные пункты"),
    }


def radio(title: str, question: str, answers: list, steps: list[str], answer) -> dict:
    if sum(1 for row in answers if row[1]) != 1:
        raise ValueError(title)
    return {
        "type": "radio",
        "title": title,
        "question_text": question,
        "points": 2,
        "answers": answers,
        "solution_text": sol(steps, answer),
    }


def short(title: str, question: str, answer, steps: list[str]) -> dict:
    return {
        "type": "short_answer",
        "title": title,
        "question_text": question + " Только число.",
        "correct_answer": str(answer),
        "answer_normalize": "strip_casefold",
        "points": 3,
        "solution_text": sol(steps, answer),
    }


def practice_16() -> list[dict]:
    return [
        checkbox(
            "Практика 16. Как считать рекурсию",
            "Что верно про столбик в задании 16? Отметьте всё верное.",
            [
                ["Стоп записывают первой строкой", True],
                ["n увеличивают по одному, без прыжков", True],
                ["F(100) можно писать сразу, не считая меньшие", False],
                ["Вопрос «сколько» — это лишний столбец с отметками", True],
            ],
            [
                "Без стопа следующую строку не из чего собрать.",
                "Каждая строка опирается на уже написанные.",
                "Прыжок к сотне оставляет дыры. Этот пункт лишний.",
                "Свойство отмечают отдельно и считают отметки.",
            ],
        ),
        radio(
            "Практика 16. Чему равно F(8)",
            "F(1) = 1, дальше F(n) = F(n−1) + n. Чему равно F(8)?",
            [["28", False], ["36", True], ["45", False], ["21", False]],
            ["Столбик: 1, 3, 6, 10, 15, 21, 28, 36.", "Последняя строка — 36."],
            36,
        ),
        short(
            "Практика 16. G(10)",
            "G(1)=1, G(2)=2. Нечётное n: G(n−1)−G(n−2). Чётное: сумма тех же двух. Чему равно G(10)?",
            g_even_odd(10),
            ["До восьмёрки таблица из урока кончается на 8.", "G(9)=8−3=5, G(10)=5+8=13."],
        ),
        short(
            "Практика 16. Сколько единиц до 20",
            "F(1)=1. Чётное n берёт F(n/2), нечётное — F(n−1)+1. Чему равно F(20)?",
            f_half_or_plus(20),
            ["Чётные срезаются до уже известной половины.", "F(20)=F(10)=F(5)=2."],
        ),
        short(
            "Практика 16. Делится на 3 до 12",
            "F(n)=n при n<3, иначе сумма двух предыдущих. Сколько n от 1 до 12 дают F(n), делящееся на 3?",
            fib_like_count(12, 3),
            ["Подходят n=3, n=7 и n=11.", "До 12 их три."],
        ),
        short(
            "Практика 16. F(9) с половиной",
            "F(1)=2. Чётное: F(n/2)+n. Нечётное: F(n−1)+1. Чему равно F(9)?",
            f_half_add(9),
            ["F(8)=16, девятка нечётная.", "16+1=17."],
        ),
    ]


def practice_17() -> list[dict]:
    numbers = [8, 4, 7, 6, 2, 9, 10, 3]
    shown = "8, 4, 7, 6, 2, 9, 10, 3"
    both = pair_stats(numbers, lambda a, b: a % 2 == 0 and b % 2 == 0)
    mixed = pair_stats(numbers, lambda a, b: (a % 2 == 0) != (b % 2 == 0))
    return [
        checkbox(
            "Практика 17. Какие пары берём",
            f"Список {shown}. Пары только соседние. Что верно? Отметьте всё верное.",
            [
                ["Смотрят пары рядом: первая со второй, вторая с третьей и так далее", True],
                ["8 и 4 — соседняя чётная пара", True],
                ["8 и 6 — соседняя пара", False],
                ["Одно число входит в две пары, если стоит в середине", True],
            ],
            [
                "Берут только соседей по списку.",
                "8 и 4 стоят рядом и оба чётные.",
                "Между 8 и 6 есть другие числа. Этот пункт лишний.",
                "Среднее число входит в пару слева и в пару справа.",
            ],
        ),
        radio(
            "Практика 17. Сколько чётных пар",
            f"В списке {shown} сколько соседних пар, где оба числа чётные?",
            [["1", False], ["2", True], ["4", False], ["5", False]],
            ["Подходят 8 с 4 и 6 с 2.", "Их две."],
            both[0],
        ),
        short(
            "Практика 17. Наибольшая чётная сумма",
            f"В списке {shown} найдите наибольшую сумму соседней пары из двух чётных.",
            both[1],
            ["Пары 8+4=12 и 6+2=8.", "Большая сумма 12."],
        ),
        short(
            "Практика 17. Ровно одно чётное",
            f"В списке {shown} сколько соседних пар, где чётное ровно одно число?",
            mixed[0],
            ["Остальные пять соседних пар смешанные.", "Их пять."],
        ),
        short(
            "Практика 17. Наибольшая смешанная сумма",
            "Среди соседних пар с ровно одним чётным какая сумма самая большая?",
            mixed[1],
            ["Самая большая смешанная пара — 9 и 10.", "9+10=19."],
        ),
    ]


def practice_18() -> list[dict]:
    grid = [[1, 4, 2], [3, 1, 5], [2, 6, 2]]
    best, worst = grid_ends(grid)
    return [
        checkbox(
            "Практика 18. Куда ходит робот",
            "Поле заполняют слева направо и сверху вниз. Что верно?",
            [
                ["В первую клетку робот уже стоит, ходов нет", True],
                ["В клетку первой строки приходят только слева", True],
                ["Можно ходить влево и вверх", False],
                ["В обычную клетку выбирают лучшее из двух входов", True],
            ],
            [
                "Старт — левый верхний угол.",
                "Сверху в первой строке никого нет.",
                "Назад робот не ходит. Этот пункт лишний.",
                "Сравнивают клетку сверху и клетку слева.",
            ],
        ),
        radio(
            "Практика 18. Максимум на поле 3×3",
            "Поле по строкам: 1 4 2 / 3 1 5 / 2 6 2. Робот идёт только вправо и вниз и собирает максимум. Сколько будет в правом нижнем углу?",
            [["12", False], ["14", True], ["16", False], ["18", False]],
            ["В углу сравнивают вход сверху и вход слева и берут больший.", "Максимум 14."],
            best,
        ),
        short(
            "Практика 18. Минимум на том же поле",
            "На том же поле робот собирает минимум. Сколько в правом нижнем углу?",
            worst,
            ["В каждой клетке берут меньший из двух входов.", "В углу получается 12."],
        ),
        short(
            "Практика 18. Максимум на поле из урока",
            "Поле 2 4 1 / 3 1 5 / 2 6 1. Какой максимум в правом нижнем углу?",
            14,
            ["Это поле из теории.", "Максимум 14."],
        ),
    ]


def practice_19_21() -> dict[int, list[dict]]:
    win, lose, _later = game_sets(15, (1,), (2,))
    assert min(win) == 8 and min(lose) == 7
    return {
        19: [
            checkbox(
                "Практика 19. Победа за один ход",
                "В куче камней ходы «прибавить 1» и «умножить на 2». Игра кончается, когда камней стало не меньше цели. Что верно?",
                [
                    ["Позиция выигрышная за ход, если какой-то ход сразу достигает цели", True],
                    ["Берут наименьшее такое число камней", True],
                    ["Позиция после цели тоже считается ответом", False],
                    ["Ход, который перелетает цель, тоже победный", True],
                ],
                [
                    "Достаточно одного удачного хода.",
                    "В ответ пишут минимальное.",
                    "Игра уже кончилась раньше. Этот пункт лишний.",
                    "Стало больше цели — тоже победа.",
                ],
            ),
            short(
                "Практика 19. Цель 15",
                "Ходы +1 и ×2. С какого наименьшего числа Петя побеждает первым же ходом, если цель — 15 камней?",
                min(win),
                ["×2 дотягивает до 15 начиная с 8.", "Меньше 8 ни +1, ни ×2 цель не берут."],
            ),
        ],
        20: [
            radio(
                "Практика 20. Проигрышная куча",
                "Цель 15, ходы +1 и ×2. Какое наименьшее число камней проигрышно: любой ход отдаёт сопернику победу сразу?",
                [["6", False], ["7", True], ["8", False], ["4", False]],
                ["Семёрка: 8 и 14, обе позиции уже выигрышные за ход.", "Шестёрка так не устроена."],
                min(lose),
            ),
            short(
                "Практика 20. Цель 10",
                "Ходы +1 и ×2, цель 10. Какое наименьшее число проигрышно при любом ходе?",
                4,
                ["Четвёрка ведёт в 5 и в 8.", "Обе эти кучи выигрываются одним ходом."],
            ),
        ],
        21: [
        short(
            "Практика 21. Два числа для цели 25",
            "Ходы +1, +2 и ×2, цель 25. Два наименьших числа, с которых побеждают вторым ходом. Запишите их подряд по возрастанию.",
            "610",
            ["Проигрышная куча — 12.", "Два меньших выигрыша вторым ходом — 6 и 10. Ответ 610."],
        ),
            short(
                "Практика 21. Два числа для цели 10",
                "Ходы +1 и ×2, цель 10. Два наименьших числа для победы вторым ходом, подряд.",
                "23",
                ["Проигрышная куча — 4.", "В неё ходят из 2 и из 3. Ответ 23."],
            ),
        ],
    }


def practice_22() -> list[dict]:
    done = schedule(
        [
            ("A", 3, ()),
            ("B", 5, ()),
            ("C", 2, ("A",)),
            ("D", 4, ("A", "B")),
            ("E", 6, ("C", "D")),
        ]
    )
    return [
        checkbox(
            "Практика 22. Когда процесс стартует",
            "Что верно про процессы, которые ждут друг друга?",
            [
                ["Без ожидания процесс стартует в нуле", True],
                ["Если ждут двоих, старт — по более позднему", True],
                ["Длительности просто складывают все подряд", False],
                ["Финиш равен старту плюс своей длительности", True],
            ],
            [
                "Независимый процесс не ждёт.",
                "Берут максимум финишей тех, кого ждут.",
                "Параллельные процессы не складываются. Этот пункт лишний.",
                "Своё время прибавляют после старта.",
            ],
        ),
        short(
            "Практика 22. Когда кончает E",
            "A длится 3, B длится 5. C=2 и ждёт только A. D=4 и ждёт A и B. E=6 и ждёт C и D. В какой момент кончает E?",
            done["E"],
            ["C кончает в 5, D кончает в 9.", "E стартует в 9 и длится 6, финиш 15."],
        ),
        short(
            "Практика 22. Цепочка из урока",
            "A=4, B=6, C=3 после A, D=5 после A и B, E=2 после C и D. Когда кончает E?",
            13,
            ["D кончает в 11, C в 7.", "E стартует в 11 и кончает в 13."],
        ),
    ]


def practice_23() -> list[dict]:
    plus_double = [lambda x: x + 1, lambda x: x * 2]
    return [
        checkbox(
            "Практика 23. Что считаем",
            "Исполнитель умеет +1 и ×2. Что верно?",
            [
                ["Разные команды — разные программы, даже если число совпало", True],
                ["Из 1 и +1, и ×2 ведут в 2, это две программы", True],
                ["Программы, задевшие запретное число, тоже считают", False],
                ["Считают слева направо, от старта к цели", True],
            ],
            [
                "Важна последовательность команд.",
                "Два способа попасть из 1 в 2.",
                "Запретное число выбрасывает программу. Этот пункт лишний.",
                "К цели идут по возрастанию.",
            ],
        ),
        short(
            "Практика 23. Сколько программ до 7",
            "Команды +1 и ×2, старт 1. Сколько программ получают 7?",
            ways(7, plus_double),
            ["До шестёрки программ 6, как в уроке.", "В семёрку ведёт только +1 из 6. Программ тоже 6."],
        ),
        short(
            "Практика 23. Запрещена семёрка",
            "Команды +1 и ×2, старт 1, цель 10, число 7 запрещено. Сколько программ?",
            8,
            ["Пути через 7 вычёркивают.", "Остаётся 8."],
        ),
        short(
            "Практика 23. Команды +1 и +2 до 8",
            "Команды только +1 и +2, старт 1. Сколько программ получают 8?",
            21,
            ["Это тот же подсчёт, что в уроке.", "Ответ 21."],
        ),
    ]


def practice_24() -> list[dict]:
    return [
        checkbox(
            "Практика 24. Что такое серия",
            "Что верно про серии в строке?",
            [
                ["Серия — одинаковые символы подряд", True],
                ["Одна буква — тоже серия длины 1", True],
                ["Две одинаковые буквы через другую складываются", False],
                ["Хвост строки тоже надо закрыть", True],
            ],
            [
                "Символ сменился — серия кончилась.",
                "Длина 1 допустима.",
                "Между ними чужая буква. Этот пункт лишний.",
                "Иначе потеряют конец строки.",
            ],
        ),
        short(
            "Практика 24. Самая длинная в AAABBC",
            "Какова длина самой длинной серии в строке AAABBC?",
            3,
            ["Три A, потом две B, потом одна C.", "Максимум 3."],
        ),
        short(
            "Практика 24. Самая длинная серия цифр",
            "В строке ab11c222d3 какова длина самой длинной серии цифр?",
            3,
            ["11 — длина 2, 222 — длина 3, одиночная 3 — длина 1.", "Максимум 3."],
        ),
        short(
            "Практика 24. Сколько раз ABC",
            "Сколько раз в строке ABCAAABBBCAAAAABCA встречается кусок ABC? Куски не накладываются друг на друга, считайте как обычный поиск подряд.",
            2,
            ["Первый ABC в начале.", "Второй начинается после серии A ближе к концу. Их два."],
        ),
    ]


def practice_25() -> list[dict]:
    numbers, total = mask_sum("3?6", 9)
    return [
        checkbox(
            "Практика 25. Как перебирают маску",
            "В маске один знак «?». Что верно?",
            [
                ["Вместо вопроса подставляют цифры от 0 до 9", True],
                ["Каждое полученное число проверяют на делимость", True],
                ["Ноль в вопрос подставлять нельзя", False],
                ["В ответ часто просят сумму подходящих чисел", True],
            ],
            [
                "Десять подстановок.",
                "Делитель дан в условии.",
                "Ноль — обычная цифра. Этот пункт лишний.",
                "Сумму считают после отбора.",
            ],
        ),
        radio(
            "Практика 25. Сколько чисел 3?6",
            "Сколько чисел вида 3?6 делятся на 9?",
            [["2", True], ["4", False], ["10", False], ["1", False]],
            [f"Подходят {numbers[0]} и {numbers[1]}.", "Их два."],
            2,
        ),
        short(
            "Практика 25. Сумма чисел 3?6",
            "Найдите сумму всех чисел вида 3?6, которые делятся на 9.",
            total,
            [f"Это {numbers[0]} и {numbers[1]}.", f"Сумма {total}."],
        ),
        short(
            "Практика 25. Сумма из урока 12?5",
            "Сумма чисел вида 12?5, которые делятся на 15.",
            3735,
            ["Подходят 1215, 1245 и 1275.", "Сумма 3735."],
        ),
    ]


def practice_26() -> list[dict]:
    count, largest = disk_pack(30, [9, 6, 5, 14, 4, 8])
    return [
        checkbox(
            "Практика 26. Как набивают диск",
            "Сначала берут как можно больше файлов, потом увеличивают самый большой в этом наборе. Что верно?",
            [
                ["Сначала файлы сортируют по возрастанию", True],
                ["Количество файлов после замены не меняют", True],
                ["Берут сначала самые большие, чтобы сумма была больше", False],
                ["Новый большой файл должен поместиться вместо прежнего крупнейшего", True],
            ],
            [
                "Мелочь даёт больше штук.",
                "Меняют состав, не число.",
                "Жадность по размеру уменьшает число файлов. Этот пункт лишний.",
                "Сумма без старого крупного плюс новый не больше диска.",
            ],
        ),
        short(
            "Практика 26. Сколько файлов на диск 30",
            "Диск 30. Файлы 9, 6, 5, 14, 4, 8. Сколько файлов удаётся записать, если нужно максимум штук?",
            count,
            ["По возрастанию: 4, 5, 6, 8. Сумма 23.", "Следующий 9 уже не входит. Файлов 4."],
        ),
        short(
            "Практика 26. Самый большой на диске 30",
            "На том же диске 30, при том же числе файлов, какой самый большой файл можно оставить в наборе?",
            largest,
            ["Убираем 8, остаётся 15.", "Вместо него встаёт 14: 15+14=29. Файл 9 меньше и не нужен."],
        ),
        short(
            "Практика 26. Диск 20 из урока",
            "Диск 20, файлы 9, 6, 5, 14, 4. Какой самый большой файл в наборе максимальной длины?",
            9,
            ["Три самых маленьких: 4, 5, 6.", "Шестёрку меняют на 9. Ответ 9."],
        ),
    ]


def practice_27() -> list[dict]:
    left = center([(1, 1), (1, 3), (3, 1)])
    right = center([(10, 10), (12, 10), (11, 13)])
    total = integer_parts_sum(left, right)
    return [
        checkbox(
            "Практика 27. Что такое центр",
            "Что верно про центр кучки?",
            [
                ["Это среднее арифметическое координат", True],
                ["Делят на число точек этой кучки", True],
                ["8,5 в этом уроке округляют до 9", False],
                ["Сомнительную точку отдают более близкому центру", True],
            ],
            [
                "Складывают и делят.",
                "Чужие точки в знаменатель не входят.",
                "Целая часть 8,5 равна 8. Этот пункт лишний.",
                "Сначала расстояние, потом пересчёт.",
            ],
        ),
        short(
            "Практика 27. Две новые кучки",
            "Кучка (1;1), (1;3), (3;1) и кучка (10;10), (12;10), (11;13). Сумма целых частей координат обоих центров?",
            total,
            [
                "Левый центр около (1,67; 1,67), целые части 1 и 1.",
                "Правый центр (11; 11). Сумма 24.",
            ],
        ),
        short(
            "Практика 27. Две тройки из урока",
            "Кучки (0;0), (0;4), (3;2) и (10;1), (11;4), (12;1). Сумма целых частей?",
            16,
            ["Центры (1; 2) и (11; 2).", "1+2+11+2=16."],
        ),
        short(
            "Практика 27. Целая часть 8,5",
            "Центр имеет икс 8,5. Какова его целая часть в этом уроке?",
            8,
            ["Дробь отбрасывают.", "Получается 8, не 9."],
        ),
    ]


def attach(number: int, lessons: list[dict]) -> None:
    path = ROOT / f"ege-n{number}" / "questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    theory = [item for item in data["lessons"] if item.get("type") == "theory"]
    if len(theory) != 1:
        raise SystemExit(f"ege-n{number}: теория не одна")
    merged = theory + lessons
    kinds = [item["type"] for item in merged]
    data["meta"]["scheme"] = {
        "theory": kinds.count("theory"),
        "checkbox": kinds.count("checkbox"),
        "radio": kinds.count("radio"),
        "short_answer": kinds.count("short_answer"),
        "total": len(merged),
    }
    data["lessons"] = merged
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def control_pack(slug: str, title: str, description: str, lessons: list[dict]) -> None:
    folder = ROOT / slug
    folder.mkdir(parents=True, exist_ok=True)
    intro = {
        "type": "theory",
        "title": title,
        "content": (
            f"<h1>{title}</h1>"
            "<p>Контрольная по пройденным номерам. Решайте по порядку. "
            "В ответ пишите число, без единиц измерения и без пробелов. "
            "Там, где просят два числа подряд, пишите их слитно по возрастанию.</p>"
            f"<p>{description}</p>"
        ),
        "comment": description,
        "images": [],
    }
    merged = [intro, *lessons]
    kinds = [item["type"] for item in merged]
    payload = {
        "meta": {
            "topic": title,
            "images_dir": "images/",
            "scheme": {
                "theory": 1,
                "checkbox": kinds.count("checkbox"),
                "radio": kinds.count("radio"),
                "short_answer": kinds.count("short_answer"),
                "total": len(merged),
            },
        },
        "lessons": merged,
    }
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "pack_id": f"{slug}-questions",
                "course_slug": "ege-informatika",
                "module_title": title,
                "create_module": True,
                "module_description": description,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (folder / "questions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    zip_path = ROOT / f"{slug}-import.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(folder / "manifest.json", "manifest.json")
        archive.write(folder / "questions.json", "questions.json")
    return zip_path


def controls() -> list[Path]:
    first = [
        short(
            "КР1. Номер пункта D",
            "У букв дороги: A — 3, B — 2, C — 2, D — 1. В таблице одна дорога только у пункта 2. Какой номер у D?",
            2,
            ["Одна дорога только у D и только у пункта 2.", "D = 2."],
        ),
        short(
            "КР1. Значение формулы",
            "A=1, B=0, C=1. Чему равно (A и B) или C? Истина — 1, ложь — 0.",
            1,
            ["A и B даёт 0.", "0 или C даёт 1."],
        ),
        short(
            "КР1. Сколько пятёрок",
            "Оценки: 5, 4, 5, 3, 5, 4. Сколько оценок «5»?",
            3,
            ["Пятёрки на первом, третьем и пятом месте.", "Их три."],
        ),
        short(
            "КР1. Равная длина кода",
            "Пять разных букв кодируют двоичными словами одной длины. Какая наименьшая длина слова?",
            3,
            ["Двух бит хватает только на 4 буквы.", "Нужны 3 бита."],
        ),
        short(
            "КР1. Алгоритм с чётностью",
            "Число 14 переводят в двоичную запись. Если оно чётное, справа дописывают 00, иначе 11. Полученную запись переводят обратно в десятичную. Какое число вышло?",
            int("111000", 2),
            ["14 в двоичной системе — 1110.", "Дописали 00: 111000, это 56."],
        ),
        short(
            "КР1. Точки внутри квадрата",
            "Квадрат со стороной 5 клеток. Сколько целых точек строго внутри?",
            16,
            ["(5−1)×(5−1).", "4×4=16."],
        ),
        short(
            "КР1. Размер картинки",
            "Картинка 8 на 8 точек, в палитре 16 цветов. Сколько байт занимает картинка без сжатия?",
            32,
            ["16 цветов — это 4 бита на точку.", "64×4=256 бит, это 32 байта."],
        ),
        short(
            "КР1. Слова из двух букв",
            "Алфавит из букв A и B. Сколько слов длины 3 можно составить? Буквы можно повторять.",
            8,
            ["На каждое место 2 варианта.", "2×2×2=8."],
        ),
        short(
            "КР1. Числа больше 10",
            "В столбце числа 10, 12, 7, 15, 10. Сколько из них строго больше 10?",
            2,
            ["Подходят 12 и 15.", "Десятки не больше десяти. Ответ 2."],
        ),
    ]
    second = [
        short(
            "КР2. Сколько раз ab",
            "Сколько раз в строке ababab встречается кусок ab? Считайте неперекрывающиеся вхождения подряд, как метод count.",
            "ababab".count("ab"),
            ["ab стоит на местах 1, 3 и 5.", "Их три."],
        ),
        short(
            "КР2. Пароль в битах",
            "Пароль из 8 символов, алфавит 16 символов. Сколько бит занимает один пароль?",
            32,
            ["16 символов — 4 бита на символ.", "8×4=32."],
        ),
        short(
            "КР2. Исполнитель",
            "Исполнитель начинает с 3. Команды по порядку: +1, ×2, +1. Какое число получилось?",
            9,
            ["3+1=4, 4×2=8, 8+1=9."],
        ),
        short(
            "КР2. Число в девятеричной",
            "Число 25 в девятеричной системе. Какое оно в десятичной?",
            2 * 9 + 5,
            ["2×9+5.", "Получается 23."],
        ),
        short(
            "КР2. Целые точки отрезка",
            "Сколько целых чисел x удовлетворяют 2 ≤ x ≤ 6?",
            5,
            ["Это 2, 3, 4, 5 и 6.", "Их пять."],
        ),
        short(
            "КР2. Рекурсия F(7)",
            "F(1)=1, дальше F(n)=F(n−1)+n. Чему равно F(7)?",
            f_plus_n(7),
            ["Строки доходят до 28.", "F(7)=28."],
        ),
        short(
            "КР2. Чётная пара",
            "Числа 4, 9, 2, 8, 1, 6. Наибольшая сумма соседней пары из двух чётных?",
            pair_stats([4, 9, 2, 8, 1, 6], lambda a, b: a % 2 == 0 and b % 2 == 0)[1],
            ["Соседние чётные — только 2 и 8.", "2+8=10."],
        ),
        short(
            "КР2. Минимум на поле",
            "Поле из двух строк: 1 2 и 3 1. Робот идёт только вправо и вниз и собирает минимум. Сколько в правом нижнем углу?",
            grid_ends([[1, 2], [3, 1]])[1],
            ["Путь через верх: 1+2+1=4.", "Путь через низ длиннее. Минимум 4."],
        ),
    ]
    third = [
        short(
            "КР3. Победа за один ход",
            "Ходы +1 и ×2, цель 10 камней. С какого наименьшего числа побеждают первым ходом?",
            5,
            ["Пятёрка умножается на 2 и даёт 10.", "Четвёрка так не умеет."],
        ),
        short(
            "КР3. Проигрышное число",
            "Те же ходы и цель 10. Какое наименьшее число проигрышно при любом ходе?",
            4,
            ["Из 4 оба хода ведут в выигрышные за один ход позиции.", "Ответ 4."],
        ),
        short(
            "КР3. Два числа вторым ходом",
            "Те же ходы и цель 10. Два наименьших числа для победы вторым ходом, запишите подряд.",
            23,
            ["Это 2 и 3.", "Слитно: 23."],
        ),
        short(
            "КР3. Финиш E",
            "A=3, B=5, C=2 после A, D=4 после A и B, E=6 после C и D. Когда кончает E?",
            15,
            ["E стартует после D, а D кончает в 9.", "9+6=15."],
        ),
        short(
            "КР3. Сколько программ",
            "Команды +1 и ×2, старт 1. Сколько программ получают 6?",
            6,
            ["Все шесть программ из урока.", "Ответ 6."],
        ),
        short(
            "КР3. Серия",
            "Длина самой длинной серии в строке AAABBC?",
            3,
            ["Три буквы A подряд.", "Длиннее серии нет."],
        ),
        short(
            "КР3. Сумма маски",
            "Сумма чисел вида 3?6, делящихся на 9.",
            702,
            ["Подходят 306 и 396.", "Сумма 702."],
        ),
        short(
            "КР3. Файл на диске 20",
            "Диск 20, файлы 9, 6, 5, 14, 4. Какой самый большой файл можно положить в набор с максимальным числом файлов?",
            9,
            ["В набор входят три файла.", "Самый большой среди таких наборов — 9."],
        ),
        short(
            "КР3. Центры двух троек",
            "Кучки (0;0), (0;4), (3;2) и (10;1), (11;4), (12;1). Сумма целых частей координат центров?",
            16,
            ["Центры (1; 2) и (11; 2).", "Сумма 16."],
        ),
    ]
    packs = [
        control_pack(
            "ege-kr1",
            "Контрольная 1. Задания 1–9",
            "Короткая проверка после первых девяти номеров.",
            first,
        ),
        control_pack(
            "ege-kr2",
            "Контрольная 2. Задания 10–18",
            "Проверка номеров с 10 по 18.",
            second,
        ),
        control_pack(
            "ege-kr3",
            "Контрольная 3. Задания 19–27",
            "Проверка номеров с 19 по 27.",
            third,
        ),
    ]
    READY.mkdir(parents=True, exist_ok=True)
    published = []
    for index, path in enumerate(packs, start=28):
        target = READY / f"{index:02d}-{path.name}"
        target.write_bytes(path.read_bytes())
        published.append(target)
    return published


def main() -> None:
    check_known()
    games = practice_19_21()
    mapping = {
        16: practice_16(),
        17: practice_17(),
        18: practice_18(),
        19: games[19],
        20: games[20],
        21: games[21],
        22: practice_22(),
        23: practice_23(),
        24: practice_24(),
        25: practice_25(),
        26: practice_26(),
        27: practice_27(),
    }
    for number, lessons in mapping.items():
        attach(number, lessons)
        print(f"ege-n{number}: +{len(lessons)}")
    for path in controls():
        print(path)


if __name__ == "__main__":
    main()
