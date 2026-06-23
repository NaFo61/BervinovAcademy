"""
Демо-контент: два курса с модулями, уроками, правильными ответами и КР.
"""

EGE_INFORMATICS = {
    "title": "ЕГЭ по информатике",
    "description": (
        "Системная подготовка к ЕГЭ по информатике: системы счисления, логика, "
        "алгоритмы, программирование на Python и пробные задания в формате экзамена."
    ),
    "technologies": ["ЕГЭ", "Информатика", "Python"],
    "modules": [
        {
            "title": "Системы счисления и кодирование",
            "description": "Двоичная, восьмеричная и шестнадцатеричная системы, логические операции.",
            "lessons": [
                {
                    "type": "theory",
                    "title": "Двоичная система счисления",
                    "content": (
                        "<p>Двоичная система использует основание 2. Каждая цифра — степень двойки.</p>"
                        "<p>Пример: <code>1101₂ = 1·2³ + 1·2² + 0·2¹ + 1·2⁰ = 13₁₀</code></p>"
                    ),
                    "comment": "Запомните разряды: 8, 4, 2, 1 для 4-битного числа.",
                },
                {
                    "type": "theory",
                    "title": "Логические операции",
                    "content": (
                        "<p>Основные операции: И (∧), ИЛИ (∨), НЕ (¬), исключающее ИЛИ (⊕).</p>"
                        "<p>На ЕГЭ часто встречаются таблицы истинности и упрощение выражений.</p>"
                    ),
                },
                {
                    "type": "radio",
                    "title": "Перевод в двоичную систему",
                    "question_text": "Чему равно число 13₁₀ в двоичной записи?",
                    "explanation": "13 = 8 + 4 + 1, поэтому двоичная запись — 1101.",
                    "points": 3,
                    "solution_text": "<p>Делим на 2 и собираем остатки снизу вверх: 13 → 6 (1) → 3 (0) → 1 (1) → 0 (1).</p>",
                    "answers": [
                        ("1011", False),
                        ("1101", True),
                        ("1110", False),
                        ("1001", False),
                    ],
                },
                {
                    "type": "checkbox",
                    "title": "Свойства двоичных чисел",
                    "question_text": "Какие из утверждений верны для двоичной системы?",
                    "explanation": "В двоичной системе только цифры 0 и 1; основание равно 2.",
                    "points": 4,
                    "solution_text": "<p>Основание — 2. Цифры — 0 и 1. Каждый разряд — степень двойки.</p>",
                    "answers": [
                        ("Основание системы равно 2", True),
                        ("Используются цифры от 0 до 9", False),
                        ("Каждый разряд — степень двойки", True),
                        ("Число 10₂ равно десяти в десятичной системе", False),
                    ],
                },
                {
                    "type": "coding",
                    "title": "Двоичное представление",
                    "description": "По целому неотрицательному числу n выведите его двоичное представление без префикса 0b.",
                    "instructions": "Считайте одно число n и выведите bin(n)[2:].",
                    "initial_code": "n = int(input())\n# ваш код\n",
                    "solution_template": "n = int(input())\nprint(bin(n)[2:])",
                    "solution_text": "<pre><code>n = int(input())\nprint(bin(n)[2:])</code></pre>",
                    "difficulty": "beginner",
                    "points": 10,
                    "test_cases": [
                        {
                            "input_data": "13\n",
                            "expected_output": "1101",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "0\n",
                            "expected_output": "0",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "255\n",
                            "expected_output": "11111111",
                            "is_hidden": True,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Алгоритмы и программирование",
            "description": "Линейные алгоритмы, циклы, массивы — база для заданий 12–27.",
            "lessons": [
                {
                    "type": "theory",
                    "title": "Линейные алгоритмы и сложность",
                    "content": (
                        "<p>Линейный алгоритм проходит по данным один раз — сложность O(n).</p>"
                        "<p>Примеры: поиск в неотсортированном массиве, подсчёт суммы элементов.</p>"
                    ),
                },
                {
                    "type": "radio",
                    "title": "Сложность линейного поиска",
                    "question_text": "Какова временная сложность линейного поиска в массиве из n элементов?",
                    "explanation": "В худшем случае просматриваем все n элементов — O(n).",
                    "points": 2,
                    "answers": [
                        ("O(1)", False),
                        ("O(log n)", False),
                        ("O(n)", True),
                        ("O(n²)", False),
                    ],
                },
                {
                    "type": "checkbox",
                    "title": "Свойства алгоритма",
                    "question_text": "Какие свойства обязательны для корректного алгоритма?",
                    "explanation": "Классические свойства: дискретность, определённость, конечность, результативность, массовость.",
                    "points": 5,
                    "answers": [
                        ("Дискретность", True),
                        ("Случайность шагов", False),
                        ("Конечность", True),
                        ("Определённость", True),
                    ],
                },
                {
                    "type": "coding",
                    "title": "Сумма элементов",
                    "description": "Даны n и n целых чисел. Выведите их сумму.",
                    "instructions": "Первая строка — n, вторая — n чисел через пробел.",
                    "initial_code": "n = int(input())\nnums = list(map(int, input().split()))\n# ваш код\n",
                    "solution_template": "n = int(input())\nnums = list(map(int, input().split()))\nprint(sum(nums))",
                    "solution_text": "<pre><code>print(sum(nums))</code></pre>",
                    "difficulty": "easy",
                    "points": 15,
                    "test_cases": [
                        {
                            "input_data": "3\n1 2 3\n",
                            "expected_output": "6",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "1\n42\n",
                            "expected_output": "42",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "5\n-1 0 1 2 3\n",
                            "expected_output": "5",
                            "is_hidden": True,
                        },
                    ],
                },
            ],
        },
    ],
    "exam": {
        "title": "КР: Системы счисления и алгоритмы",
        "description": (
            "Промежуточная контрольная по первым двум модулям. "
            "Таймер 45 минут, свободная навигация между заданиями."
        ),
        "duration_minutes": 45,
        "lessons": [
            {
                "type": "theory",
                "title": "Памятка перед КР",
                "content": (
                    "<p>Перед стартом вспомните:</p><ul>"
                    "<li>Двоичная запись — степени двойки.</li>"
                    "<li>Линейный проход по массиву — O(n).</li>"
                    "<li>В коде проверяйте граничные случаи: n=0, n=1.</li>"
                    "</ul>"
                ),
            },
            {
                "type": "radio",
                "title": "Части ЕГЭ по информатике",
                "question_text": "Сколько основных частей в ЕГЭ по информатике?",
                "explanation": "Часть 1 — краткий ответ, часть 2 — развёрнутые задания и программы.",
                "points": 5,
                "answers": [
                    ("Одна", False),
                    ("Две", True),
                    ("Три", False),
                    ("Четыре", False),
                ],
            },
            {
                "type": "checkbox",
                "title": "Что разрешено на экзамене",
                "question_text": "Что обычно разрешено на ЕГЭ по информатике?",
                "explanation": "КЕГЭ и черновик разрешены; личные устройства — нет.",
                "points": 10,
                "answers": [
                    ("КЕГЭ (компьютер)", True),
                    ("Черновик", True),
                    ("Личный телефон", False),
                    ("Свой ноутбук", False),
                ],
            },
            {
                "type": "coding",
                "title": "Сумма двух чисел",
                "description": "По двум целым числам выведите их сумму.",
                "instructions": "Две строки — два числа.",
                "initial_code": "a = int(input())\nb = int(input())\n# ваш код\n",
                "solution_template": "a = int(input())\nb = int(input())\nprint(a + b)",
                "difficulty": "beginner",
                "points": 15,
                "test_cases": [
                    {
                        "input_data": "2\n3\n",
                        "expected_output": "5",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "10\n20\n",
                        "expected_output": "30",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "-1\n1\n",
                        "expected_output": "0",
                        "is_hidden": True,
                    },
                ],
            },
        ],
    },
}

PYTHON_FROM_ZERO = {
    "title": "Python с нуля",
    "description": (
        "Python для начинающих: синтаксис, типы данных, условия, циклы, функции "
        "и первые задачи с автопроверкой."
    ),
    "technologies": ["Python"],
    "modules": [
        {
            "title": "Первые шаги в Python",
            "description": "Установка, print(), переменные и базовые типы.",
            "lessons": [
                {
                    "type": "theory",
                    "title": "Знакомство с Python",
                    "content": (
                        "<p>Python — интерпретируемый язык с простым синтаксисом.</p>"
                        "<pre><code>print('Привет, мир!')</code></pre>"
                    ),
                    "comment": "Для практики используйте встроенный редактор на платформе.",
                },
                {
                    "type": "theory",
                    "title": "Переменные и типы",
                    "content": (
                        "<p>Основные типы: <code>int</code>, <code>float</code>, "
                        "<code>str</code>, <code>bool</code>, <code>list</code>.</p>"
                        "<pre><code>age = 16\npi = 3.14\nname = 'Анна'</code></pre>"
                    ),
                },
                {
                    "type": "radio",
                    "title": "Тип числа с плавающей точкой",
                    "question_text": "Что вернёт выражение type(3.14) в Python 3?",
                    "explanation": "Литерал с точкой — это float.",
                    "points": 2,
                    "solution_text": "<p><code>3.14</code> — вещественный литерал, тип <code>float</code>.</p>",
                    "answers": [
                        ("<class 'int'>", False),
                        ("<class 'float'>", True),
                        ("<class 'str'>", False),
                        ("<class 'decimal'>", False),
                    ],
                },
                {
                    "type": "checkbox",
                    "title": "Встроенные типы Python",
                    "question_text": "Какие из перечисленных — встроенные типы Python 3?",
                    "explanation": "list, dict, tuple, set и bool — встроенные. array — модуль array.",
                    "points": 4,
                    "answers": [
                        ("list", True),
                        ("dict", True),
                        ("array", False),
                        ("tuple", True),
                    ],
                },
                {
                    "type": "coding",
                    "title": "Приветствие",
                    "description": "Считайте имя и выведите «Привет, <имя>!»",
                    "instructions": "Одна строка — имя без пробелов.",
                    "initial_code": "name = input()\n# ваш код\n",
                    "solution_template": "name = input()\nprint(f'Привет, {name}!')",
                    "solution_text": "<pre><code>print(f'Привет, {name}!')</code></pre>",
                    "difficulty": "beginner",
                    "points": 10,
                    "test_cases": [
                        {
                            "input_data": "Анна\n",
                            "expected_output": "Привет, Анна!",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "Python\n",
                            "expected_output": "Привет, Python!",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "User\n",
                            "expected_output": "Привет, User!",
                            "is_hidden": True,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Условия и циклы",
            "description": "if/else, while, for и типовые задачи на ветвление.",
            "lessons": [
                {
                    "type": "theory",
                    "title": "Условный оператор if",
                    "content": (
                        "<pre><code>if x > 0:\n    print('положительное')\n"
                        "else:\n    print('не положительное')</code></pre>"
                    ),
                },
                {
                    "type": "radio",
                    "title": "Цикл for",
                    "question_text": "Какой цикл удобнее, когда известно число итераций?",
                    "explanation": "for перебирает последовательность или range(n).",
                    "points": 2,
                    "answers": [
                        ("while", False),
                        ("for", True),
                        ("do-while", False),
                        ("loop", False),
                    ],
                },
                {
                    "type": "checkbox",
                    "title": "Ключевые слова Python",
                    "question_text": "Какие слова являются ключевыми в Python?",
                    "explanation": "def, if, for — ключевые. function — нет в Python.",
                    "points": 3,
                    "answers": [
                        ("def", True),
                        ("function", False),
                        ("if", True),
                        ("for", True),
                    ],
                },
                {
                    "type": "coding",
                    "title": "Чётное или нечётное",
                    "description": "По целому n выведите «чётное» или «нечётное».",
                    "instructions": "Одно число на входе.",
                    "initial_code": "n = int(input())\n# ваш код\n",
                    "solution_template": "n = int(input())\nprint('чётное' if n % 2 == 0 else 'нечётное')",
                    "solution_text": "<pre><code>print('чётное' if n % 2 == 0 else 'нечётное')</code></pre>",
                    "difficulty": "beginner",
                    "points": 10,
                    "test_cases": [
                        {
                            "input_data": "4\n",
                            "expected_output": "чётное",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "7\n",
                            "expected_output": "нечётное",
                            "is_hidden": False,
                        },
                        {
                            "input_data": "0\n",
                            "expected_output": "чётное",
                            "is_hidden": True,
                        },
                    ],
                },
            ],
        },
    ],
    "exam": {
        "title": "КР: Основы Python",
        "description": (
            "Контрольная по переменным, типам, условиям и циклам. "
            "Доступна после прохождения обоих модулей."
        ),
        "duration_minutes": 40,
        "lessons": [
            {
                "type": "theory",
                "title": "Перед контрольной",
                "content": (
                    "<p>Проверьте:</p><ul>"
                    "<li><code>input()</code> всегда возвращает строку — приводите типы.</li>"
                    "<li>Отступы в Python обязательны.</li>"
                    "<li>Для вывода используйте <code>print</code>.</li>"
                    "</ul>"
                ),
            },
            {
                "type": "radio",
                "title": "Функция print",
                "question_text": "Что выведет print(type(5))?",
                "explanation": "Литерал 5 — целое число, type(5) — <class 'int'>.",
                "points": 5,
                "answers": [
                    ("<class 'int'>", True),
                    ("5", False),
                    ("int", False),
                    ("<class 'str'>", False),
                ],
            },
            {
                "type": "checkbox",
                "title": "Верные утверждения",
                "question_text": "Какие утверждения о Python 3 верны?",
                "explanation": "Индексация с 0; input() — строка; else есть у if.",
                "points": 8,
                "answers": [
                    ("Индексация списка начинается с 0", True),
                    ("input() возвращает строку", True),
                    ("У if нет ветки else", False),
                    ("Пробелы не влияют на выполнение", False),
                ],
            },
            {
                "type": "coding",
                "title": "Максимум из двух",
                "description": "По двум целым числам выведите большее.",
                "instructions": "Две строки — два числа.",
                "initial_code": "a = int(input())\nb = int(input())\n# ваш код\n",
                "solution_template": "a = int(input())\nb = int(input())\nprint(max(a, b))",
                "difficulty": "easy",
                "points": 15,
                "test_cases": [
                    {
                        "input_data": "3\n7\n",
                        "expected_output": "7",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "10\n2\n",
                        "expected_output": "10",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "5\n5\n",
                        "expected_output": "5",
                        "is_hidden": True,
                    },
                ],
            },
        ],
    },
}

COURSE_FIXTURES = [EGE_INFORMATICS, PYTHON_FROM_ZERO]
