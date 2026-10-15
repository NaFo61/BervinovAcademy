#!/usr/bin/env python3
"""Уроки 24–27 и сборка всех страниц 16–27.

Рядом с теорией пишет manifest.json, preview.html и questions.json —
как у пакетов 1–15.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_theory_lessons as base


def runs_of(text: str) -> list[tuple[str, int]]:
    groups: list[tuple[str, int]] = []
    for char in text:
        if groups and groups[-1][0] == char:
            groups[-1] = (char, groups[-1][1] + 1)
        else:
            groups.append((char, 1))
    return groups


def lesson_24() -> str:
    toy = "AABBBAA"
    toy_runs = runs_of(toy)
    assert max(length for _, length in toy_runs) == 3
    sample = "ABCAAABBBCAAAAABCA"
    sample_runs = runs_of(sample)
    assert max(length for char, length in sample_runs if char == "A") == 5
    assert sample.count("ABC") == 2
    digits = "a12b333c44d5555e6"
    digit_runs: list[int] = []
    current = 0
    for char in digits:
        if char.isdigit():
            current += 1
        elif current:
            digit_runs.append(current)
            current = 0
    if current:
        digit_runs.append(current)
    assert digit_runs == [2, 3, 2, 4, 1]
    letters = "ИНФОРМАТИКА"
    assert letters.count("И") == 2
    assert letters.count("А") == 2
    toy_rows = [
        (index, char, length) for index, (char, length) in enumerate(toy_runs, start=1)
    ]
    sample_rows = []
    for index, (char, length) in enumerate(sample_runs, start=1):
        flag = "да" if char == "A" and length == 5 else ""
        mark = f'<span class="mark">{flag}</span>' if flag else ""
        sample_rows.append((index, char, length, mark))
    return f"""
<h1>Задание 24 ЕГЭ: строка символов</h1>
<p class="intro">Дают длинную строку: буквы, иногда цифры. На экзамене в ней тысячи символов, смотрят программой. Руками разберём короткие, потому что программа делает те же шаги: идёт слева направо и помнит, какой кусок длится сейчас.</p>
<p class="intro">Кусок одинаковых символов подряд называют серией. В строке AABBBAA три серии: две A, три B, снова две A. Между сериями символ меняется. Одна буква — тоже серия, длины 1.</p>

<h2>Игрушка: самая длинная серия</h2>
<p>Строка <strong>{toy}</strong>. Идём по буквам и закрываем серию, как только буква сменилась.</p>
{base.table(["серия", "буква", "длина"], toy_rows)}
<p>Длины 2, 3 и 2. Самая большая — 3, это три B посередине. Две серии A по краям не складываются в четвёрку: между ними стоят другие буквы, это уже не подряд.</p>
<div class="answer">Самая длинная серия: <strong>3</strong></div>

<h2>План</h2>
<div class="box">
  <ol>
    <li>Ставим палец на первый символ. Длина текущей серии — 1.</li>
    <li>Пока следующий символ такой же, длину увеличиваем.</li>
    <li>Как только символ сменился, серия кончилась. Если её длина — рекорд, запоминаем. Новую начинаем с единицы.</li>
    <li>После последнего символа серия тоже кончается. Её учитываем, иначе потеряем хвост строки.</li>
  </ol>
</div>

<h2>Пример 1. Только серии буквы A</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> В строке {sample} какая самая длинная серия буквы A?</p>
<p>Серии других букв тоже выписываем. Иначе не видно, где A прервалась. В рекорд идут только строки с буквой A.</p>
<div class="table-scroll">
{base.table(["серия", "буква", "длина", "рекорд A"], sample_rows)}
</div>
<p>У A длины 1, 3, 5 и снова 1. Пять — это кусок AAAAA ближе к концу. Три B рядом рекорд буквы A не обновляют.</p>
<div class="answer">Самая длинная серия A: <strong>5</strong></div>
</div>

<h2>Пример 2. Сколько раз подряд стоит ABC</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Сколько раз в строке {sample} подряд идут буквы A, B, C именно в этом порядке?</p>
<p>Это не серия одинаковых букв. Ищем окно из трёх символов и сдвигаем его на одну позицию. Позиции 1–3 — это ABC, одно вхождение. Дальше окна BCA, CAA, AAA и остальные, пока не дойдём до куска у конца: после пяти A стоит B, за ней C. Это второе ABC. Окна, которые только задевают эти буквы, сами ABC не являются и в счёт не идут.</p>
<div class="answer">Вхождений ABC: <strong>2</strong></div>
</div>

<h2>Пример 3. Самая длинная серия цифр</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> В строке {digits} какая самая длинная серия, состоящая только из цифр?</p>
<p>Буква обрывает серию цифр. До первой цифры серии нет. «12» — длина 2, буква b её закрывает. «333» — длина 3. «44» — длина 2. «5555» — длина 4. Одинокая «6» в конце — длина 1. Её нельзя выбросить только потому, что строка кончилась: по плану хвост тоже считается.</p>
{base.table(["серия цифр", "длина"], [("12", 2), ("333", 3), ("44", 2), ("5555", 4), ("6", 1)])}
<div class="answer">Самая длинная серия цифр: <strong>4</strong></div>
</div>

<h2>Пример 4. Буквы не обязательно подряд</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> В слове {letters} сколько букв И и сколько букв А?</p>
<p>Здесь серии не нужны. Буквы не обязаны стоять рядом. И стоит в начале и в слоге «ТИ» — две. А стоит в «МА» и перед последней К — тоже две. Если бы спросили самую частую букву, завели бы счётчик на каждую, тем же проходом слева направо.</p>
<div class="answer">И: <strong>2</strong>. А: <strong>2</strong>.</div>
</div>

<h2>Коротко, чтобы запомнить</h2>
<ol>
  <li>Серия — одинаковые символы подряд. Другой символ начинает новую серию.</li>
  <li>Рекорд проверяем, когда серия кончилась, и обязательно в конце строки.</li>
  <li>Вопрос «только про A» не отменяет чужие серии: они показывают разрывы.</li>
  <li>Кусок из разных букв, вроде ABC, ищут окном, а не счётчиком одинаковых.</li>
  <li>Длинный файл на экзамене — та же логика в программе.</li>
</ol>
<table class="code-table summary-table">
  <tr><th>Пример</th><th>Что спросили</th><th>Ответ</th></tr>
  <tr><td>игрушка</td><td>самая длинная серия в AABBBAA</td><td><strong>3</strong></td></tr>
  <tr><td>1</td><td>самая длинная серия A</td><td><strong>5</strong></td></tr>
  <tr><td>2</td><td>сколько раз ABC</td><td><strong>2</strong></td></tr>
  <tr><td>3</td><td>самая длинная серия цифр</td><td><strong>4</strong></td></tr>
  <tr><td>4</td><td>сколько И и А в слове ИНФОРМАТИКА</td><td><strong>2 и 2</strong></td></tr>
</table>
"""


def lesson_25() -> str:
    mask_rows = []
    good = []
    for digit in range(10):
        number = 1200 + digit * 10 + 5
        digit_sum = 1 + 2 + digit + 5
        ok = number % 15 == 0
        if ok:
            good.append(number)
        mark = '<span class="mark">да</span>' if ok else ""
        mask_rows.append((number, digit, digit_sum, "да" if digit_sum % 3 == 0 else "", mark))
    assert good == [1215, 1245, 1275]
    assert sum(good) == 3735
    second_rows = []
    second = []
    for digit in range(10):
        number = 200 + digit * 10 + 4
        digit_sum = 2 + digit + 4
        ok = number % 6 == 0
        if ok:
            second.append(number)
        mark = '<span class="mark">да</span>' if ok else ""
        second_rows.append((number, digit_sum, "да" if digit_sum % 3 == 0 else "", mark))
    assert second == [204, 234, 264, 294]
    assert sum(second) == 996
    return f"""
<h1>Задание 25 ЕГЭ: маска числа</h1>
<p class="intro">В маске часть цифр уже стоит на местах, а вместо неизвестной написан знак. Вопросительный знак — ровно одна цифра, от 0 до 9. Звёздочка, если встретится в другом варианте, значит «сколько угодно цифр, можно ни одной». К маске дают свойство: число делится на 15, на 6, на 12. Нужно найти все такие числа, иногда их сумму.</p>
<p class="intro">Когда неизвестна одна цифра, кандидатов десять. Их выписывают все. Сначала отсекают признаком делимости, потом оставшиеся делят и проверяют, что остаток ноль.</p>

<h2>Признаки, которые здесь нужны</h2>
<ul>
  <li>На 2: последняя цифра чётная.</li>
  <li>На 3: сумма цифр делится на 3.</li>
  <li>На 5: последняя цифра 0 или 5.</li>
  <li>На 6: сразу и на 2, и на 3.</li>
  <li>На 15: сразу и на 3, и на 5.</li>
</ul>
<div class="box">
  <p>Признак экономит время. Оставшиеся числа всё равно проверяют делением. Если признак сказал «да», а при делении вылез остаток, верят делению и заново считают сумму цифр.</p>
</div>

<h2>Пример 1. Маска 12?5, число делится на 15</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Найдите все числа маски 12?5, которые делятся на 15, и их сумму.</p>
<p>Знак «?» — одна цифра, кандидаты: 1205, 1215, …, 1295. Все кончаются на 5, на 5 делятся все. Осталось деление на 3. У 1205 сумма цифр 1+2+0+5 = 8, на 3 не делится. У 1215 сумма 9, делится. Проверка делением: 1215 / 15 = 81, остаток 0.</p>
<div class="table-scroll">
{base.table(["число", "вместо ?", "сумма цифр", "сумма делится на 3", "делится на 15"], mask_rows)}
</div>
<p>Подходят три числа: 1215, 1245 и 1275. Складываем 1215 + 1245 = 2460, плюс 1275 = 3735. Остальные семь в сумму не входят, хотя на 5 они тоже делятся.</p>
<div class="answer">Числа 1215, 1245, 1275. Сумма: <strong>3735</strong></div>
</div>

<h2>Пример 2. Маска 2?4, число делится на 6</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Трёхзначные числа маски 2?4, которые делятся на 6. Чему равна их сумма?</p>
<p>Последняя цифра 4, она чётная, на 2 делятся все десять. На 6 нужно ещё на 3. У 204 сумма цифр 6, 204 / 6 = 34. У 214 сумма 7, мимо. Дальше смотрим таблицу: годятся суммы 6, 9, 12 и 15.</p>
{base.table(["число", "сумма цифр", "делится на 3", "делится на 6"], second_rows)}
<p>204 + 234 = 438. 264 + 294 = 558. Вместе 438 + 558 = 996.</p>
<div class="answer">Числа 204, 234, 264, 294. Сумма: <strong>996</strong></div>
</div>

<h2>Коротко, чтобы запомнить</h2>
<ol>
  <li>«?» — ровно одна цифра. Если остальные позиции заданы, кандидатов десять.</li>
  <li>Сначала признак, потом деление тех, кто прошёл признак.</li>
  <li>«Делится на 15» — два условия сразу, на 3 и на 5. Одного мало.</li>
  <li>В сумму входят только прошедшие оба условия.</li>
</ol>
<table class="code-table summary-table">
  <tr><th>Пример</th><th>Что спросили</th><th>Ответ</th></tr>
  <tr><td>1</td><td>сумма чисел маски 12?5, кратных 15</td><td><strong>3735</strong></td></tr>
  <tr><td>2</td><td>сумма чисел маски 2?4, кратных 6</td><td><strong>996</strong></td></tr>
</table>
"""


def pack_files(disk: int, sizes: list[int]) -> tuple[list[int], int]:
    ordered = sorted(sizes)
    taken: list[int] = []
    total = 0
    for size in ordered:
        if total + size <= disk:
            taken.append(size)
            total += size
        else:
            break
    without_last = sum(taken[:-1])
    room = disk - without_last
    candidates = [size for size in ordered if taken[-1] <= size <= room]
    return taken, max(candidates)


def running_rows(disk: int, sizes: list[int]) -> str:
    ordered = sorted(sizes)
    rows = []
    total = 0
    stopped = False
    for size in ordered:
        if stopped or total + size > disk:
            rows.append((size, "не берём", total, disk - total))
            stopped = True
            continue
        total += size
        rows.append((size, "берём", total, disk - total))
    return base.table(["файл", "решение", "занято", "свободно"], rows)


def lesson_26() -> str:
    assert pack_files(10, [3, 6, 2, 4]) == ([2, 3, 4], 4)
    assert pack_files(100, [15, 8, 22, 7, 30, 11, 9, 18, 6, 25]) == (
        [6, 7, 8, 9, 11, 15, 18, 22],
        25,
    )
    assert pack_files(20, [9, 6, 5, 14, 4]) == ([4, 5, 6], 9)
    files = "15, 8, 22, 7, 30, 11, 9, 18, 6, 25"
    small = "9, 6, 5, 14, 4"
    return f"""
<h1>Задание 26 ЕГЭ: файлы на диске</h1>
<p class="intro">Есть диск известного объёма и набор файлов. Файл кладут целиком или не кладут никак. Спрашивают две вещи. Сколько файлов удастся записать, если хотим как можно больше штук. И какой самый большой файл можно при этом сохранить — не один на весь диск, а в наборе, где файлов столько же, сколько в самом плотном по количеству.</p>
<p class="intro">Больше всего штук набирается с самых маленьких. Крупный файл, положенный первым, съест место трёх мелких.</p>

<h2>Игрушка: диск на 10</h2>
<p>Файлы 3, 6, 2 и 4. Сортируем по возрастанию: 2, 3, 4, 6.</p>
{running_rows(10, [3, 6, 2, 4])}
<p>2+3+4 = 9, свободно 1. Шестёрка не входит. Файлов три. Второй вопрос: можно ли заменить кого-то из этих трёх так, чтобы крупнейший в наборе стал больше 4, а сумма всё ещё не превосходила 10?</p>
<p>Мелочь 2 и 3 оставляем, это 5, свободно 5. Четвёрка в эти пять входит, шестёрка нет: 5+6 = 11. Крупнее четвёрки положить нечего. Самый большой файл так и остаётся 4.</p>
<div class="answer">Файлов: <strong>3</strong>. Самый большой среди них: <strong>4</strong></div>

<h2>План</h2>
<div class="box">
  <ol>
    <li>Сортируем размеры по возрастанию.</li>
    <li>Берём с маленьких, пока следующий ещё входит. Это максимум штук.</li>
    <li>Для второго вопроса откладываем последний взятый: он самый крупный в этом наборе.</li>
    <li>Смотрим, какое самое большое число из всего списка всё ещё входит в освободившееся место.</li>
    <li>Один убрали, один положили. Количество файлов не меняется.</li>
  </ol>
</div>

<h2>Пример 1. Диск на 100</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Диск 100. Файлы: {files}. Сколько файлов можно записать? Какой наибольший размер файла достижим в наборе с этим же количеством?</p>
<p>Порядок такой: 6, 7, 8, 9, 11, 15, 18, 22, 25, 30.</p>
{running_rows(100, [15, 8, 22, 7, 30, 11, 9, 18, 6, 25])}
<p>Восемь файлов занимают 96, свободно 4. Число 25 уже не входит. Количество — 8.</p>
<p>Откладываем 22. Без него занято 74, свободно 26. В эти 26 входят 22 и 25. Тридцать не входит: 74+30 = 104. Заменяем 22 на 25. Файлов по-прежнему восемь, сумма 96 − 22 + 25 = 99.</p>
<div class="answer">Файлов: <strong>8</strong>. Наибольший файл в таком наборе: <strong>25</strong></div>
</div>

<h2>Пример 2. Замена видна на маленьком диске</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Диск 20. Файлы: {small}. Те же два числа в ответе.</p>
{running_rows(20, [9, 6, 5, 14, 4])}
<p>Три файла: 4+5+6 = 15. Если шестёрку уже положили, девятка не входит. Откладываем шестёрку. Остаются 4 и 5, занято 9, свободно 11. В одиннадцать входят 6 и 9. Четырнадцать не входит: 9+14 = 23. Берём 9. Набор 4, 5 и 9 занимает 18. Файлов по-прежнему три, крупнейший уже не 6, а 9.</p>
<div class="answer">Файлов: <strong>3</strong>. Наибольший файл в таком наборе: <strong>9</strong></div>
</div>

<h2>Коротко, чтобы запомнить</h2>
<ol>
  <li>Максимум штук даёт набор с самых маленьких файлов.</li>
  <li>Файл не режут. Не влез очередной в отсортированном списке — более крупные тоже не влезут.</li>
  <li>Второй вопрос не начинается с самого большого файла в одиночку: так штук станет меньше.</li>
  <li>Меняем только крупнейший в уже набранном комплекте.</li>
</ol>
<table class="code-table summary-table">
  <tr><th>Пример</th><th>Диск</th><th>Ответ</th></tr>
  <tr><td>игрушка</td><td>10</td><td><strong>3 файла, крупнейший 4</strong></td></tr>
  <tr><td>1</td><td>100</td><td><strong>8 файлов, крупнейший 25</strong></td></tr>
  <tr><td>2</td><td>20</td><td><strong>3 файла, крупнейший 9</strong></td></tr>
</table>
"""


def center(points: list[tuple[float, float]]) -> tuple[float, float]:
    count = len(points)
    return (sum(p[0] for p in points) / count, sum(p[1] for p in points) / count)


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def lesson_27() -> str:
    left = [(1, 2), (2, 1), (2, 3), (3, 2)]
    right = [(8, 8), (9, 7), (7, 9), (10, 8)]
    left_c = center(left)
    right_c = center(right)
    assert left_c == (2.0, 2.0)
    assert right_c == (8.5, 8.0)
    base_sum = int(left_c[0]) + int(left_c[1]) + int(right_c[0]) + int(right_c[1])
    assert base_sum == 20
    trio_a = [(0, 0), (0, 4), (3, 2)]
    trio_b = [(10, 1), (11, 4), (12, 1)]
    assert center(trio_a) == (1.0, 2.0)
    assert center(trio_b) == (11.0, 2.0)
    extra = (6.0, 1.0)
    assert dist(extra, left_c) < dist(extra, right_c)
    grown = center(left + [extra])
    assert abs(grown[0] - 2.8) < 1e-9
    assert abs(grown[1] - 1.8) < 1e-9
    assert int(grown[0]) + int(grown[1]) + int(right_c[0]) + int(right_c[1]) == 19

    def dot(x: float, y: float, label: str) -> str:
        sx = 28 + x * 32
        sy = 246 - y * 22
        return (
            f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="5" fill="#1a1a1a"/>'
            f'<text x="{sx + 8:.0f}" y="{sy - 6:.0f}" font-size="15" '
            f'font-style="italic" fill="#1a1a1a">{label}</text>'
        )

    names_l = ["A", "B", "C", "D"]
    names_r = ["E", "F", "G", "H"]
    parts = [dot(x, y, f"{name} ({x},{y})") for name, (x, y) in zip(names_l, left)]
    parts += [dot(x, y, f"{name} ({x},{y})") for name, (x, y) in zip(names_r, right)]
    parts.append(dot(6, 1, "P (6,1)"))
    picture = (
        '<svg class="graph-svg" viewBox="0 0 460 270" xmlns="http://www.w3.org/2000/svg">'
        + "".join(parts)
        + "</svg>"
    )
    left_rows = list(zip(names_l, [p[0] for p in left], [p[1] for p in left]))
    right_rows = list(zip(names_r, [p[0] for p in right], [p[1] for p in right]))
    return f"""
<h1>Задание 27 ЕГЭ: две кучки точек</h1>
<p class="intro">Дают много точек на плоскости. Глазом видно, что они сбились в две кучки, далеко друг от друга. У кучки есть центр: среднее арифметическое её координат. На экзамене точек сотни, среднее считает программа. Здесь кучки по четыре точки, чтобы было видно, что именно усредняют.</p>
<p class="intro">Ответом в этом уроке будет сумма целых частей четырёх чисел: икса и игрека первого центра, икса и игрека второго. Целая часть положительного числа — цифры до запятой. У 8,5 целая часть 8, не 9.</p>

<h2>Рисунок и таблица</h2>
<p>Слева A, B, C, D. Справа E, F, G, H. Точка P понадобится в примере 2, пока её в среднее не берём.</p>
{picture}
{base.table(["точка", "x", "y"], left_rows)}
{base.table(["точка", "x", "y"], right_rows)}

<h2>Центр каждой кучки</h2>
<p>Левая, икс: (1+2+2+3) / 4 = 8/4 = 2. Игрек: (2+1+3+2) / 4 = 8/4 = 2. Центр (2; 2).</p>
<p>Правая, икс: (8+9+7+10) / 4 = 34/4 = 8,5. Игрек: (8+7+9+8) / 4 = 32/4 = 8. Центр (8,5; 8).</p>
<p>Целые части 2, 2, 8 и 8. Сумма 20. Половинку у 8,5 не округляем вверх: в этом уроке дробь отбрасывают.</p>
<div class="answer">Сумма целых частей: <strong>20</strong></div>
<div class="box">
  <p><strong>План.</strong> Отделить кучки. Внутри одной сложить иксы и разделить на число её точек, то же сделать с игреками. Точку, которая висит между кучками, отдать той, до чьего центра ближе, и этот центр пересчитать. Потом взять целые части и сложить так, как просит вопрос.</p>
</div>

<h2>Пример 1. Две тройки</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> Кучка (0; 0), (0; 4), (3; 2) и кучка (10; 1), (11; 4), (12; 1). Сумма целых частей координат обоих центров?</p>
<p>Левая, икс: (0+0+3) / 3 = 1. Игрек: (0+4+2) / 3 = 2. Центр (1; 2). Правая, икс: (10+11+12) / 3 = 11. Игрек: (1+4+1) / 3 = 2. Центр (11; 2). Числа уже целые: 1+2+11+2 = 16.</p>
<div class="answer">Сумма: <strong>16</strong></div>
</div>

<h2>Пример 2. Точка между кучками</h2>
<div class="example">
<p class="question"><strong>Вопрос.</strong> К первому рисунку добавили P(6; 1). Её отдают ближайшему центру и центр пересчитывают. Какая теперь сумма целых частей?</p>
<p>Старые центры (2; 2) и (8,5; 8). От P до левого: вправо на 4, вниз на 1. Квадраты 16 и 1, сумма 17, расстояние — корень из 17, около 4,1. До правого: влево на 2,5 и вниз на 7. Квадраты 6,25 и 49, сумма 55,25, корень около 7,4. Ближе левая кучка. Правый центр не трогаем.</p>
<p>Слева теперь пять точек. Икс: (1+2+2+3+6) / 5 = 14/5 = 2,8. Игрек: (2+1+3+2+1) / 5 = 9/5 = 1,8. Целые части 2 и 1. Справа по-прежнему 8 и 8. Сумма 2+1+8+8 = 19.</p>
<p>Одна точка сдвинула целую часть игрека с 2 на 1. Её нельзя выбросить и нельзя усреднить сразу со всеми восемью: общий центр встал бы в пустое место между кучками и к делу бы не относился.</p>
<div class="answer">Сумма целых частей: <strong>19</strong></div>
</div>

<h2>Коротко, чтобы запомнить</h2>
<ol>
  <li>Центр — среднее арифметическое, не самая крайняя точка.</li>
  <li>Делим на число точек этой кучки, не на все точки листа.</li>
  <li>Сомнительную точку сравнивают с центрами по расстоянию и только потом пересчитывают.</li>
  <li>Целая часть 8,5 здесь равна 8.</li>
</ol>
<table class="code-table summary-table">
  <tr><th>Пример</th><th>Что спросили</th><th>Ответ</th></tr>
  <tr><td>рисунок</td><td>две кучки по четыре точки</td><td><strong>20</strong></td></tr>
  <tr><td>1</td><td>две тройки</td><td><strong>16</strong></td></tr>
  <tr><td>2</td><td>добавили точку (6; 1)</td><td><strong>19</strong></td></tr>
</table>
"""


PACKS = {
    16: "Функция вызывает сама себя. Ответ считают столбиком от маленького n.",
    17: "Пары и тройки соседних чисел: сколько подходят и какая сумма больше.",
    18: "Робот ходит только вправо и вниз. В углу клетки уже лежит ответ.",
    19: "Игра в камни. Петя побеждает своим первым ходом.",
    20: "Петя сразу не побеждает, но любой его ход отдаёт победу Ване.",
    21: "Петя побеждает вторым ходом. В ответ два наименьших числа подряд.",
    22: "Процессы ждут друг друга. Общий конец — самый поздний финиш.",
    23: "Сколько разных программ приводят исполнителя из старта в цель.",
    24: "Строка символов. Самая длинная серия и поиск короткого куска.",
    25: "Маска числа. Неизвестная цифра и признак делимости.",
    26: "Файлы на диске: максимум штук и самый большой файл в этом наборе.",
    27: "Две кучки точек. Центр — среднее, в ответ идут целые части.",
}


def _split_theory(text: str) -> tuple[str, str, str]:
    style = re.search(r"<style>(.*?)</style>", text, re.S)
    body = re.search(r"<body>\s*(.*)\s*</body>", text, re.S)
    title = re.search(r"<h1>(.*?)</h1>", text, re.S)
    if not style or not body or not title:
        raise SystemExit("теория без style, body или h1")
    return style.group(1), body.group(1).strip(), title.group(1).strip()


def write_pack(number: int) -> None:
    folder = base.ROOT / f"ege-n{number}"
    style, body, title = _split_theory(
        (folder / "theory.html").read_text(encoding="utf-8")
    )
    comment = PACKS[number]
    manifest = {
        "pack_id": f"ege-n{number}-questions",
        "course_slug": "ege-informatika",
        "module_title": title,
        "create_module": True,
        "module_description": comment,
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    questions = {
        "meta": {
            "topic": f"ЕГЭ информатика, задание {number}",
            "images_dir": "images/",
            "scheme": {
                "theory": 1,
                "checkbox": 0,
                "radio": 0,
                "short_answer": 0,
                "total": 1,
            },
        },
        "lessons": [
            {
                "type": "theory",
                "title": title,
                "content": body,
                "comment": comment,
                "images": [],
            }
        ],
    }
    (folder / "questions.json").write_text(
        json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lead = (
        '<p class="intro">Страница для проверки. '
        "Ниже вся теория, как она пойдёт в урок.</p>"
    )
    preview_body = body.replace("<h1>", f"{lead}\n<h1>", 1)
    preview = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{style}</style>
</head>
<body>
{preview_body}
</body>
</html>
"""
    (folder / "preview.html").write_text(preview, encoding="utf-8")


def main() -> None:
    lessons = [
        (16, "Задание 16 ЕГЭ: рекурсия", base.lesson_16),
        (17, "Задание 17 ЕГЭ: последовательность чисел", base.lesson_17),
        (18, "Задание 18 ЕГЭ: робот на поле", base.lesson_18),
        (19, "Задание 19 ЕГЭ: игра, победа за один ход", base.lesson_19),
        (20, "Задание 20 ЕГЭ: Ваня побеждает сразу", base.lesson_20),
        (21, "Задание 21 ЕГЭ: победа вторым ходом", base.lesson_21),
        (22, "Задание 22 ЕГЭ: процессы", base.lesson_22),
        (23, "Задание 23 ЕГЭ: сколько программ", base.lesson_23),
        (24, "Задание 24 ЕГЭ: строка", lesson_24),
        (25, "Задание 25 ЕГЭ: маска числа", lesson_25),
        (26, "Задание 26 ЕГЭ: файлы на диске", lesson_26),
        (27, "Задание 27 ЕГЭ: две кучки точек", lesson_27),
    ]
    for number, title, builder in lessons:
        body = builder()
        for needle in ("<h1>", 'class="answer"', "Коротко, чтобы запомнить", "summary-table"):
            if needle not in body:
                raise SystemExit(f"{number}: нет {needle}")
        base.save(number, title, body)
        write_pack(number)


if __name__ == "__main__":
    main()
