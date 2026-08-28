"""
Демо-контент: один курс «ЕГЭ-информатика» с 4 модулями.
"""

PLACEHOLDER_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def _v(extra=None):
    """Common video + solution stub fields."""
    base = {
        "video_url": PLACEHOLDER_VIDEO,
        "solution_text": (
            "<p>Разбор на видео — как на уроке: сначала условие, "
            "потом короткий код или таблица.</p>"
        ),
    }
    if extra:
        base.update(extra)
    return base


def _theory(title, content, comment=""):
    row = {
        "type": "theory",
        "title": title,
        "content": content,
        "video_url": PLACEHOLDER_VIDEO,
    }
    if comment:
        row["comment"] = comment
    return row


def _radio(title, question_text, answers, explanation="", points=3):
    return {
        "type": "radio",
        "title": title,
        "question_text": question_text,
        "explanation": explanation,
        "points": points,
        "answers": answers,
        **_v(),
    }


def _checkbox(title, question_text, answers, explanation="", points=4):
    return {
        "type": "checkbox",
        "title": title,
        "question_text": question_text,
        "explanation": explanation,
        "points": points,
        "answers": answers,
        **_v(),
    }


def _coding(
    title,
    description,
    instructions,
    initial_code,
    solution_template,
    test_cases,
    difficulty="beginner",
    points=10,
):
    return {
        "type": "coding",
        "title": title,
        "description": description,
        "instructions": instructions,
        "initial_code": initial_code,
        "solution_template": solution_template,
        "difficulty": difficulty,
        "points": points,
        "test_cases": test_cases,
        **_v(
            {"solution_text": f"<pre><code>{solution_template}</code></pre>"}
        ),
    }


def _short(title, question_text, correct_answer, explanation="", points=3):
    return {
        "type": "short_answer",
        "title": title,
        "question_text": question_text,
        "correct_answer": correct_answer,
        "answer_normalize": "strip_casefold",
        "explanation": explanation,
        "points": points,
        **_v(),
    }


def _graphs_pack() -> list:
    return [
        _theory(
            "Таблица дорог и матрица смежности",
            """<h2>Что рисуют на №1</h2>
<p>В КИМ дают таблицу: строки и столбцы — города, в клетке длина дороги или прочерк. Это уже граф: вершины — города, рёбра — дороги.</p>
<p>Матрица смежности для неориентированного графа симметрична. Единица (или длина) в клетке <em>i, j</em> значит, что между вершинами есть ребро. Нули на диагонали — петли обычно не считают.</p>
<h3>Как не завалить подсчёт</h3>
<ul>
<li>Ребро {A, B} в неориентированном графе считается <strong>один раз</strong>, хотя в матрице две единицы.</li>
<li>Степень вершины — сколько единиц в её строке (без петли).</li>
<li>Путь длины 2 из A в C ищут так: есть ли общий сосед. На черновике удобно выписать соседей столбцом.</li>
</ul>
<p>Не зубрите «формулу полного графа» вслепую. На экзамене чаще дают кривую таблицу с пятью городами и просят кратчайший маршрут или число дорог из пункта.</p>""",
            comment="После теории откройте матрицу 4×4 на листочке и посчитайте рёбра вручную — так быстрее, чем смотреть разбор.",
        ),
        _radio(
            "Сколько рёбер у K4",
            "Полный неориентированный граф на 4 вершинах. Сколько у него рёбер?",
            [
                ("4", False),
                ("6", True),
                ("8", False),
                ("12", False),
            ],
            explanation="Каждая пара вершин соединена: 4×3/2 = 6.",
        ),
        _radio(
            "Степень по строке матрицы",
            "В матрице смежности без петель строка вершины B: 1 0 1 1 0. Чему равна степень B?",
            [
                ("2", False),
                ("3", True),
                ("4", False),
                ("5", False),
            ],
            explanation="Считаем единицы в строке: три соседа.",
        ),
        _checkbox(
            "Что видно по матрице смежности",
            "Отметьте всё, что можно сразу прочитать из матрицы смежности неориентированного графа (без весов).",
            [
                ("Есть ли ребро между двумя вершинами", True),
                ("Степень вершины", True),
                ("Цвет вершин на картинке в учебнике", False),
                (
                    "Симметрична ли таблица (как проверка на ориентированность)",
                    True,
                ),
            ],
            explanation="Цвет картинки к матрице не относится. Остальное — да.",
        ),
        _checkbox(
            "Таблица дорог на ЕГЭ",
            "Что верно для типового №1 с таблицей расстояний между городами?",
            [
                ("Прочерк часто значит «дороги нет»", True),
                (
                    "Кратчайший путь не всегда прямое ребро: иногда дешевле через третий город",
                    True,
                ),
                (
                    "Достаточно сложить все числа в таблице и разделить на два",
                    False,
                ),
                (
                    "Имеет смысл набросать граф на черновике, а не считать в уме",
                    True,
                ),
            ],
            explanation="Сумма всех клеток — не ответ: там дубли и длины, не число маршрутов.",
        ),
        _coding(
            "Число рёбер по матрице",
            "Дана матрица смежности неориентированного графа без петель. Посчитайте число рёбер. Ребро {i, j} в матрице встречается дважды — считайте один раз.",
            "Сначала n — число вершин. Затем n строк по n чисел 0 или 1 через пробел.",
            "n = int(input())\n# считайте верхний треугольник матрицы\n",
            "n = int(input())\nedges = 0\nfor i in range(n):\n    row = list(map(int, input().split()))\n    for j in range(i + 1, n):\n        edges += row[j]\nprint(edges)",
            [
                {
                    "input_data": "3\n0 1 1\n1 0 1\n1 1 0\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "4\n0 1 0 0\n1 0 1 1\n0 1 0 0\n0 1 0 0\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n0\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
        ),
        _coding(
            "Степень вершины",
            "Вершины пронумерованы с 1. По матрице смежности выведите степень вершины k (число единиц в строке k, петлю не кладём — на диагонали нули).",
            "n и k. Затем матрица n×n.",
            "n, k = map(int, input().split())\n# ваш код\n",
            "n, k = map(int, input().split())\nrow = None\nfor i in range(n):\n    line = list(map(int, input().split()))\n    if i + 1 == k:\n        row = line\nprint(sum(row))",
            [
                {
                    "input_data": "4 2\n0 1 0 0\n1 0 1 1\n0 1 0 0\n0 1 0 0\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "3 1\n0 1 1\n1 0 0\n1 0 0\n",
                    "expected_output": "2",
                    "is_hidden": False,
                },
                {
                    "input_data": "2 2\n0 0\n0 0\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _coding(
            "Изолированные вершины",
            "Сколько вершин имеют степень 0?",
            "n, затем матрица n×n из 0 и 1.",
            "n = int(input())\n# ваш код\n",
            "n = int(input())\niso = 0\nfor _ in range(n):\n    row = list(map(int, input().split()))\n    if sum(row) == 0:\n        iso += 1\nprint(iso)",
            [
                {
                    "input_data": "3\n0 1 0\n1 0 0\n0 0 0\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "2\n0 1\n1 0\n",
                    "expected_output": "0",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n0\n",
                    "expected_output": "1",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            "Что рисуют таблицей дорог",
            "Одним словом: набор вершин и рёбер в задании с городами и дорогами.",
            "Граф",
            explanation="Таблица дорог — это граф: города-вершины, дороги-рёбра.",
        ),
        _short(
            "Рёбра у треугольника",
            "Сколько рёбер у полного графа на трёх вершинах (K3)? Только число.",
            "3",
            explanation="Треугольник: три ребра.",
        ),
        _short(
            "Степень в K5",
            "В полном графе на 5 вершинах какая степень у каждой вершины?",
            "4",
            explanation="Соединена со всеми, кроме себя: 4.",
        ),
        _short(
            "Формула полного графа",
            "Чему равно n(n−1)/2 при n = 6? Это число рёбер K6.",
            "15",
            explanation="6×5/2 = 15.",
        ),
    ]


def _coding_search_pack() -> list:
    return [
        _theory(
            "Условие Фано и поиск в тексте",
            """<h2>Код, который однозначно читается</h2>
<p>Условие Фано: <strong>ни одно кодовое слово не является началом другого</strong>. Тогда сообщение из 0 и 1 разбирается слева направо без развилок.</p>
<p>Пример. Код: A=0, B=10, C=11 — Фано выполняется. Код A=0, B=01 — уже нет: 0 начало 01, декодер не знает, остановиться после первого нуля или читать дальше.</p>
<h3>№10 — поиск в редакторе</h3>
<p>Типичный сюжет: в файле считают, сколько раз встречается кусок вроде <code>TIK</code> или сколько строк содержат слово. На компьютере экзамена это делается поиском, в нашем курсе — коротким Python: <code>s.count(...)</code> или цикл по строкам.</p>
<p>Путаница: «вхождений» и «строк, где встретилось». Это разные числа, если в одной строке слово дважды.</p>""",
            comment="На черновике выпишите кодовые слова столбиком и проверьте префиксы парами — быстрее, чем рисовать дерево.",
        ),
        _radio(
            "Какая пара ломает Фано",
            "Какая пара кодовых слов нарушает условие Фано?",
            [
                ("10 и 11", False),
                ("0 и 10", True),
                ("01 и 10", False),
                ("00 и 11", False),
            ],
            explanation="0 — префикс 10. Остальные пары друг другом не начинаются.",
        ),
        _radio(
            "Что считает s.count",
            "В Python для строки s выражение s.count('ab') считает…",
            [
                (
                    "число непересекающихся вхождений подстроки ab слева направо",
                    True,
                ),
                ("число различных букв в s", False),
                ("длину s минус 2", False),
                ("только вхождения с начала строки", False),
            ],
            explanation="count идёт слева и не считает перекрытия вроде 'aaa'.count('aa') → 1.",
        ),
        _checkbox(
            "Про Фано",
            "Отметьте верные утверждения.",
            [
                (
                    "Если Фано выполняется, сообщение из алфавита кода декодируется однозначно слева направо",
                    True,
                ),
                ("Равная длина всех слов автоматически даёт Фано", True),
                (
                    "Достаточно, чтобы слова были разными — префиксы можно не проверять",
                    False,
                ),
                (
                    "Дерево кода без внутренних пометок — удобная картинка того же условия",
                    True,
                ),
            ],
            explanation="Разные слова ещё не спасают: 0 и 01 разные, Фано нет. Равная длина — да, префиксов короче нет.",
        ),
        _checkbox(
            "Поиск в тексте",
            "Файл из нескольких строк. Что может быть ответом на №10?",
            [
                ("Сколько раз встречается кусок символов", True),
                ("Сколько строк содержат данное слово", True),
                ("Средняя зарплата автора файла", False),
                ("Длина самой длинной строки", True),
            ],
            explanation="Зарплата к поиску в редакторе не относится.",
        ),
        _coding(
            "Сколько раз встретился кусок",
            "Дана одна строка. Выведите, сколько раз в ней встречается подстрока pattern из второй строки. Считайте как str.count: без наложений.",
            "Строка 1 — текст. Строка 2 — образец.",
            "s = input()\np = input()\n# ваш код\n",
            "s = input()\np = input()\nprint(s.count(p))",
            [
                {
                    "input_data": "abababa\nab\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "aaaa\naa\n",
                    "expected_output": "2",
                    "is_hidden": False,
                },
                {
                    "input_data": "xyz\nqq\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
        ),
        _coding(
            "Строки с словом",
            "Сначала n. Затем n строк. Выведите, сколько из них содержат слово w (четвёртая строка ввода после n? Нет: w дано вторым после n, потом n строк текста).",
            "Первая строка: n. Вторая: слово w. Далее n строк.",
            "n = int(input())\nw = input()\n# ваш код\n",
            "n = int(input())\nw = input()\nprint(sum(1 for _ in range(n) if w in input()))",
            [
                {
                    "input_data": "3\nкот\nкотёнок\nпёс\nкот и кит\n",
                    "expected_output": "2",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\nab\nabab\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "2\nx\na\nb\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _coding(
            "Самая длинная строка",
            "n строк. Выведите длину самой длинной (в символах, как len).",
            "n, затем n строк.",
            "n = int(input())\n# ваш код\n",
            "n = int(input())\nprint(max(len(input()) for _ in range(n)))",
            [
                {
                    "input_data": "3\na\nabc\nab\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\nhello\n",
                    "expected_output": "5",
                    "is_hidden": False,
                },
                {
                    "input_data": "2\n\nx\n",
                    "expected_output": "1",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            "Префикс",
            "Является ли слово 10 началом слова 101? Ответьте да или нет.",
            "да",
            explanation="10 — префикс 101.",
        ),
        _short(
            "count без наложений",
            "Чему равно 'aaa'.count('aa') в Python?",
            "1",
            explanation="После первого 'aa' остаётся один символ.",
        ),
        _short(
            "Равная длина",
            "Все кодовые слова длины 3 из нулей и единиц. Фано выполняется? да/нет",
            "да",
            explanation="Одинаковая длина — ни одно слово не начало другого.",
        ),
    ]


def _spreadsheets_pack() -> list:
    return [
        _theory(
            "Электронные таблицы на ЕГЭ",
            """<h2>№9 — не бухгалтерия</h2>
<p>В файле три-четыре столбца чисел. Спрашивают, например: сколько строк, где среднее больше 50, или где ровно два числа чётные. На экзамене это Excel/Calc, у нас — Python: прочитали строку, разбили, посчитали.</p>
<p>Типичные формулы в таблице: <code>СУММ</code>, <code>СРЗНАЧ</code>, <code>СЧЁТЕСЛИ</code>. Диапазон A1:C2 — это 3 столбца × 2 строки = 6 ячеек. Ошибка «A1:C2 это 5» встречается каждый год.</p>
<h3>Как не запутаться в строке</h3>
<ul>
<li>Сначала выпишите, что именно считают: строки, ячейки или пары.</li>
<li>Чётность — по <code>n % 2 == 0</code>, не по последней цифре в уме, если число отрицательное.</li>
<li>Пустая клетка и ноль — разные вещи. В наших тестах пустых нет.</li>
</ul>""",
            comment="Откройте любой csv из трёх колонок и руками отметьте строки, где сумма > 100 — так условие №9 перестаёт быть страшным.",
        ),
        _radio(
            "Ячейки в диапазоне",
            "Сколько ячеек в диапазоне A1:C2?",
            [
                ("5", False),
                ("6", True),
                ("3", False),
                ("9", False),
            ],
            explanation="Столбцы A,B,C и строки 1–2: 3×2 = 6.",
        ),
        _radio(
            "Что делает СРЗНАЧ",
            "СРЗНАЧ(A1:A4) при значениях 2, 4, 6, 8 равна…",
            [
                ("5", True),
                ("20", False),
                ("8", False),
                ("4", False),
            ],
            explanation="(2+4+6+8)/4 = 5.",
        ),
        _checkbox(
            "Про формулы",
            "Что верно для работы с таблицей на ЕГЭ?",
            [
                ("Формулы в ячейках использовать можно", True),
                (
                    "Имеет смысл проверить одну строку вручную, прежде чем тянуть формулу вниз",
                    True,
                ),
                ("Нужен только Paint", False),
                (
                    "Число строк с условием и сумма по столбцу — разные постановки",
                    True,
                ),
            ],
            explanation="Paint к №9 не относится.",
        ),
        _checkbox(
            "Чётность в строке",
            "В строке три целых числа. Какие проверки осмысленны для типового задания?",
            [
                ("Ровно два числа чётные", True),
                ("Произведение больше 0 (одно отрицательное — уже нет)", True),
                ("Цвет заливки ячейки в файле", False),
                ("Максимум строки совпадает с первым числом", True),
            ],
            explanation="Цвет заливки в КИМ не спрашивают.",
        ),
        _coding(
            "Строки с суммой больше порога",
            "n строк по три целых через пробел. Сколько строк имеют сумму строго больше t? t дано первым числом после n? Формат: n, затем t, затем n строк.",
            "n, затем t, затем n строк по три числа.",
            "n = int(input())\nt = int(input())\n# ваш код\n",
            "n = int(input())\nt = int(input())\nprint(sum(1 for _ in range(n) if sum(map(int, input().split())) > t))",
            [
                {
                    "input_data": "3\n10\n1 2 3\n4 4 4\n10 0 0\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n0\n1 1 1\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "2\n100\n1 1 1\n2 2 2\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
        ),
        _coding(
            "Чётных в строке ровно два",
            "n строк по три целых. Сколько строк содержат ровно два чётных числа.",
            "n, затем n строк.",
            "n = int(input())\n# ваш код\n",
            "n = int(input())\nans = 0\nfor _ in range(n):\n    nums = list(map(int, input().split()))\n    if sum(x % 2 == 0 for x in nums) == 2:\n        ans += 1\nprint(ans)",
            [
                {
                    "input_data": "3\n1 2 4\n2 2 2\n1 3 5\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n2 1 4\n",
                    "expected_output": "1",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n2 4 6\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _coding(
            "Максимум по столбцу",
            "n строк по два числа: столбец A и столбец B. Выведите максимум столбца B.",
            "n, затем n строк по два целых.",
            "n = int(input())\n# ваш код\n",
            "n = int(input())\nmx = None\nfor _ in range(n):\n    a, b = map(int, input().split())\n    mx = b if mx is None else max(mx, b)\nprint(mx)",
            [
                {
                    "input_data": "3\n1 8\n2 3\n0 5\n",
                    "expected_output": "8",
                    "is_hidden": False,
                },
                {
                    "input_data": "1\n-1 -7\n",
                    "expected_output": "-7",
                    "is_hidden": False,
                },
                {
                    "input_data": "2\n0 0\n0 1\n",
                    "expected_output": "1",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            "Диапазон A1:B3",
            "Сколько ячеек в A1:B3?",
            "6",
            explanation="2 столбца × 3 строки.",
        ),
        _short(
            "Среднее четырёх",
            "Среднее арифметическое чисел 10, 10, 10, 22. Только число.",
            "13",
            explanation="52/4 = 13.",
        ),
        _short(
            "СЧЁТЕСЛИ идея",
            "В столбце пять чисел: 3, 8, 8, 1, 8. Сколько раз встречается 8?",
            "3",
            explanation="Три восьмёрки — как СЧЁТЕСЛИ на восьмёрку.",
        ),
    ]


def _control_pack() -> list:
    """Контрольная: 2 radio + 2 checkbox + 2 coding + 2 short, без теории."""
    return [
        _radio(
            "КР · рёбра K3",
            "Сколько рёбер у полного графа на 3 вершинах?",
            [
                ("2", False),
                ("3", True),
                ("4", False),
                ("6", False),
            ],
            explanation="K3 — треугольник, 3 ребра.",
        ),
        _radio(
            "КР · Фано",
            "Какое условие связано с однозначным декодированием слева направо?",
            [
                ("Ни одно кодовое слово не начало другого", True),
                (
                    "Все слова одной длины — единственный возможный способ",
                    False,
                ),
                ("Только двоичный алфавит", False),
                ("Чётная длина каждого слова", False),
            ],
            explanation="Это условие Фано. Равная длина — частный случай, не единственный.",
        ),
        _checkbox(
            "КР · графы и коды",
            "Что относится к темам графов и кодирования на ЕГЭ?",
            [
                ("Матрица смежности", True),
                ("Условие Фано", True),
                ("Только фильтры Instagram", False),
                ("Таблица дорог как граф", True),
            ],
            explanation="Соцсети к КИМ не относятся.",
        ),
        _checkbox(
            "КР · таблицы",
            "Что верно для электронных таблиц в ЕГЭ?",
            [
                ("Можно использовать формулы", True),
                ("Нужен только графический редактор", False),
                ("Часто смотрят число строк с условием", True),
                ("Запрещены любые числа", False),
            ],
            explanation="Формулы и подсчёт строк — да.",
        ),
        _coding(
            "КР · сумма двух",
            "Два целых на двух строках. Выведите сумму.",
            "Две строки — два числа.",
            "a = int(input())\nb = int(input())\n# ваш код\n",
            "a = int(input())\nb = int(input())\nprint(a + b)",
            [
                {
                    "input_data": "1\n2\n",
                    "expected_output": "3",
                    "is_hidden": False,
                },
                {
                    "input_data": "100\n200\n",
                    "expected_output": "300",
                    "is_hidden": False,
                },
            ],
        ),
        _coding(
            "КР · вхождения",
            "Две строки: текст и образец. Выведите text.count(pattern).",
            "Две строки.",
            "s = input()\np = input()\n# ваш код\n",
            "s = input()\np = input()\nprint(s.count(p))",
            [
                {
                    "input_data": "abab\nab\n",
                    "expected_output": "2",
                    "is_hidden": False,
                },
                {
                    "input_data": "qqq\nq\n",
                    "expected_output": "3",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            "КР · путь через соседа",
            "Города A—B и B—C соединены. Сколько рёбер в пути A→C через B?",
            "2",
            explanation="Два ребра: A-B и B-C.",
        ),
        _short(
            "КР · A1:C2",
            "Сколько ячеек в диапазоне A1:C2?",
            "6",
            explanation="3 столбца × 2 строки.",
        ),
    ]


EGE_INFORMATIKA = {
    "title": "ЕГЭ-информатика",
    "slug": "ege-informatika",
    "description": (
        "Разбираем то, что реально приходит на ЕГЭ: таблица дорог, "
        "матрица смежности, условие Фано, поиск куска в тексте и "
        "строки в электронной таблице. Python — чтобы проверить себя "
        "за 15 строк, не чтобы учить фреймворки. Четвёртый модуль — "
        "смешанная контрольная по трём темам."
    ),
    "technologies": ["ЕГЭ", "Информатика"],
    "modules": [
        {
            "title": "1-й урок ЕГЭ: Графы",
            "description": (
                "Города и дороги, матрица смежности, степень вершины, "
                "сколько рёбер на самом деле (типовое №1)."
            ),
            "lessons": _graphs_pack(),
        },
        {
            "title": "2-й урок ЕГЭ: Кодирование и поиск",
            "description": (
                "Префиксы и условие Фано (№4), поиск вхождений "
                "в тексте (№10)."
            ),
            "lessons": _coding_search_pack(),
        },
        {
            "title": "3-й урок ЕГЭ: Электронные таблицы",
            "description": (
                "Сколько ячеек в диапазоне, строки с условием, "
                "чётность и максимум столбца (№9)."
            ),
            "lessons": _spreadsheets_pack(),
        },
        {
            "title": "4-й урок ЕГЭ: Кодирование изображений",
            "description": (
                "Битовая глубина, палитра, размер файла и пиксели "
                "(типовое №7)."
            ),
            "lessons": [],
        },
        {
            "title": "Контрольная",
            "description": (
                "Смешали графы, коды и таблицы. Новой теории нет — "
                "только проверка, что рука помнит."
            ),
            "lessons": _control_pack(),
        },
    ],
}

COURSE_FIXTURES = [EGE_INFORMATIKA]

# Backward-compatible alias (старые импорты / тесты)
EGE_INFORMATICS = EGE_INFORMATIKA
