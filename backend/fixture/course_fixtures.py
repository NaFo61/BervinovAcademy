"""
Демо-контент: один курс «ЕГЭ-информатика» с 4 модулями.
"""

PLACEHOLDER_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def _v(extra=None):
    """Common video + solution stub fields."""
    base = {
        "video_url": PLACEHOLDER_VIDEO,
        "solution_text": "<p>Разбор (заглушка). Полное видео — в тарифе Pro.</p>",
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


def _module_lesson_pack(theme: str) -> list:
    """1 theory + 2 radio + 2 checkbox + 3 coding + 3 short-answer."""
    t = theme
    return [
        _theory(
            f"Теория: {t}",
            f"<p>Краткий теоретический блок по теме «{t}» (учебная заглушка).</p>"
            f"<p>Разберите определения, типовые приёмы и примеры из КИМ ЕГЭ.</p>",
            comment=f"После теории переходите к вопросам по теме «{t}».",
        ),
        _radio(
            f"Radio 1 · {t}",
            f"Какое утверждение верно для темы «{t}»?",
            [
                ("Верное утверждение A", True),
                ("Неверное B", False),
                ("Неверное C", False),
                ("Неверное D", False),
            ],
            explanation=f"Правильный вариант — A (тема: {t}).",
        ),
        _radio(
            f"Radio 2 · {t}",
            f"Выберите корректный ответ по теме «{t}».",
            [
                ("Вариант 1", False),
                ("Вариант 2", True),
                ("Вариант 3", False),
                ("Вариант 4", False),
            ],
            explanation="Верный ответ — вариант 2.",
        ),
        _checkbox(
            f"Checkbox 1 · {t}",
            f"Отметьте все верные утверждения ({t}).",
            [
                ("Верно 1", True),
                ("Неверно", False),
                ("Верно 2", True),
                ("Неверно 2", False),
            ],
            explanation="Верны утверждения 1 и 2.",
        ),
        _checkbox(
            f"Checkbox 2 · {t}",
            f"Какие свойства относятся к теме «{t}»?",
            [
                ("Свойство A", True),
                ("Свойство B", True),
                ("Свойство C", False),
                ("Свойство D", True),
            ],
            explanation="A, B и D — верные.",
        ),
        _coding(
            f"Задача 1 · {t}",
            f"Учебная задача по теме «{t}»: выведите сумму двух целых.",
            "Две строки — два числа.",
            "a = int(input())\nb = int(input())\n# ваш код\n",
            "a = int(input())\nb = int(input())\nprint(a + b)",
            [
                {
                    "input_data": "2\n3\n",
                    "expected_output": "5",
                    "is_hidden": False,
                },
                {
                    "input_data": "10\n-1\n",
                    "expected_output": "9",
                    "is_hidden": False,
                },
                {
                    "input_data": "0\n0\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
        ),
        _coding(
            f"Задача 2 · {t}",
            f"Учебная задача ({t}): выведите модуль числа.",
            "Одно целое число.",
            "n = int(input())\n# ваш код\n",
            "n = int(input())\nprint(abs(n))",
            [
                {
                    "input_data": "-5\n",
                    "expected_output": "5",
                    "is_hidden": False,
                },
                {
                    "input_data": "7\n",
                    "expected_output": "7",
                    "is_hidden": False,
                },
                {
                    "input_data": "0\n",
                    "expected_output": "0",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _coding(
            f"Задача 3 · {t}",
            f"Учебная задача ({t}): выведите максимум из двух чисел.",
            "Две строки — два числа.",
            "a = int(input())\nb = int(input())\n# ваш код\n",
            "a = int(input())\nb = int(input())\nprint(max(a, b))",
            [
                {
                    "input_data": "3\n8\n",
                    "expected_output": "8",
                    "is_hidden": False,
                },
                {
                    "input_data": "5\n5\n",
                    "expected_output": "5",
                    "is_hidden": False,
                },
                {
                    "input_data": "-2\n-9\n",
                    "expected_output": "-2",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            f"Краткий ответ 1 · {t}",
            f"Введите ответ-число по теме «{t}» (заглушка).",
            "42",
            explanation="Эталон: 42.",
        ),
        _short(
            f"Краткий ответ 2 · {t}",
            f"Введите кодовое слово по теме «{t}».",
            "Граф",
            explanation="Эталон: Граф (без учёта регистра и лишних пробелов).",
        ),
        _short(
            f"Краткий ответ 3 · {t}",
            f"Сколько базовых шагов в разборе темы «{t}»? (заглушка)",
            "3",
            explanation="Эталон: 3.",
        ),
    ]


def _control_pack() -> list:
    """Контрольная: 2 radio + 2 checkbox + 2 coding + 2 short, без теории."""
    return [
        _radio(
            "КР · Radio: графы",
            "Сколько рёбер у полного графа на 3 вершинах?",
            [
                ("2", False),
                ("3", True),
                ("4", False),
                ("6", False),
            ],
            explanation="K3 имеет 3 ребра.",
        ),
        _radio(
            "КР · Radio: кодирование",
            "Какое условие связано с однозначным декодированием (Фано)?",
            [
                ("Ни одно кодовое слово не начало другого", True),
                ("Все слова одной длины", False),
                ("Только двоичный алфавит", False),
                ("Чётная длина кода", False),
            ],
            explanation="Условие Фано: ни одно слово не префикс другого.",
        ),
        _checkbox(
            "КР · Checkbox: смешанно",
            "Что относится к темам графов и кодирования?",
            [
                ("Матрица смежности", True),
                ("Условие Фано", True),
                ("Только Excel-формулы", False),
                ("Таблица дорог ↔ граф", True),
            ],
            explanation="Excel — тема таблиц; остальное — графы/кодирование.",
        ),
        _checkbox(
            "КР · Checkbox: таблицы",
            "Что верно для работы с электронными таблицами на ЕГЭ?",
            [
                ("Можно использовать формулы", True),
                ("Нужен только Paint", False),
                ("Часто задание №9", True),
                ("Запрещены любые числа", False),
            ],
            explanation="Формулы и типовой №9 — верно.",
        ),
        _coding(
            "КР · Задача: сумма",
            "Выведите сумму двух целых (темы 1–3).",
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
            "КР · Задача: произведение",
            "Выведите произведение двух целых.",
            "Две строки — два числа.",
            "a = int(input())\nb = int(input())\n# ваш код\n",
            "a = int(input())\nb = int(input())\nprint(a * b)",
            [
                {
                    "input_data": "4\n5\n",
                    "expected_output": "20",
                    "is_hidden": False,
                },
                {
                    "input_data": "-2\n3\n",
                    "expected_output": "-6",
                    "is_hidden": True,
                },
            ],
            difficulty="easy",
        ),
        _short(
            "КР · Краткий ответ: №1",
            "В графе «города» кратчайший путь A→C через B занимает сколько рёбер? (заглушка)",
            "2",
            explanation="Эталон: 2.",
        ),
        _short(
            "КР · Краткий ответ: №9",
            "Сколько ячеек в диапазоне A1:C2? (заглушка)",
            "6",
            explanation="3 столбца × 2 строки = 6.",
        ),
    ]


EGE_INFORMATIKA = {
    "title": "ЕГЭ-информатика",
    "slug": "ege-informatika",
    "description": (
        "Подготовка к ЕГЭ по информатике: графы, кодирование и поиск, "
        "электронные таблицы и контрольная по пройденным темам. "
        "Python используется как инструмент экзамена."
    ),
    "technologies": ["ЕГЭ", "Информатика"],
    "modules": [
        {
            "title": "1-й урок ЕГЭ: Графы",
            "description": (
                "Анализ информационных моделей: таблица дорог, граф, "
                "матрица смежности (типовое задание №1)."
            ),
            "lessons": _module_lesson_pack("Графы"),
        },
        {
            "title": "2-й урок ЕГЭ: Кодирование и поиск",
            "description": (
                "Кодирование/декодирование (условие Фано, №4) и поиск "
                "в текстовом редакторе (№10)."
            ),
            "lessons": _module_lesson_pack("Кодирование и поиск"),
        },
        {
            "title": "3-й урок ЕГЭ: Электронные таблицы",
            "description": (
                "Электронные таблицы / Excel (№9); кратко — связанные "
                "таблицы и поиск (смежно №3)."
            ),
            "lessons": _module_lesson_pack("Электронные таблицы"),
        },
        {
            "title": "Контрольная",
            "description": (
                "Смешанная проверка тем модулей 1–3. Новой теории нет — "
                "только практика."
            ),
            "lessons": _control_pack(),
        },
    ],
}

COURSE_FIXTURES = [EGE_INFORMATIKA]

# Backward-compatible alias (старые импорты / тесты)
EGE_INFORMATICS = EGE_INFORMATIKA
