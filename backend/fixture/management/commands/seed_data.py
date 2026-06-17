import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Course,
    Exam,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    RadioAnswerOption,
    Technology,
    TestCase,
)
from translations.models import TranslationMemory
from users.models import Mentor, Specialization, Student

User = get_user_model()


class Command(BaseCommand):
    help = "Наполняет базу тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить существующие данные перед наполнением",
        )
        parser.add_argument(
            "--courses-count",
            type=int,
            default=2,
            help="Количество создаваемых курсов (по умолчанию 2 — ЕГЭ)",
        )
        parser.add_argument(
            "--modules-per-course",
            type=int,
            default=3,
            help="Количество модулей на курс",
        )
        parser.add_argument(
            "--lessons-per-module",
            type=int,
            default=5,
            help="Количество уроков на модуль",
        )
        parser.add_argument(
            "--radio-questions-per-module",
            type=int,
            default=2,
            help="Количество radio-вопросов на модуль",
        )
        parser.add_argument(
            "--checkbox-questions-per-module",
            type=int,
            default=2,
            help="Количество checkbox-вопросов на модуль",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["clear"]:
                self.clear_data()

            self.create_superuser()
            self.create_specializations()
            specializations = list(Specialization.objects.all())

            # Создаем технологии ДО создания менторов
            technologies = self.create_technologies()

            self.create_mentors(specializations, technologies)
            self.create_students()

            # Создаем курсы и связанные данные
            self.create_courses(
                count=options["courses_count"],
                technologies=technologies,
                modules_per_course=options["modules_per_course"],
                lessons_per_module=options["lessons_per_module"],
                radio_questions_per_module=options[
                    "radio_questions_per_module"
                ],
                checkbox_questions_per_module=options[
                    "checkbox_questions_per_module"
                ],
            )

            self.stdout.write(self.style.SUCCESS("Данные успешно созданы"))

    def clear_data(self):
        User.objects.all().delete()
        Specialization.objects.all().delete()
        TranslationMemory.objects.all().delete()
        Course.objects.all().delete()
        from education.models import Enrollment

        Enrollment.objects.all().delete()
        Technology.objects.all().delete()
        Module.objects.all().delete()
        LessonTheory.objects.all().delete()
        LessonRadioQuestion.objects.all().delete()
        RadioAnswerOption.objects.all().delete()
        LessonCheckBoxQuestion.objects.all().delete()
        CheckBoxAnswerOption.objects.all().delete()
        CodingChallenge.objects.all().delete()
        TestCase.objects.all().delete()

    def create_superuser(self):
        User.objects.create_superuser(
            email="admin@academy.com",
            phone="+7 (999) 111-22-33",
            password="password",
            first_name="Админ",
            last_name="Админов",
            role="admin",
        )
        self.stdout.write(self.style.SUCCESS("Создан суперпользователь"))

    def generate_phone(self):
        operator_code = random.choice(["937", "999", "901", "902", "905"])
        number = "".join([str(random.randint(0, 9)) for _ in range(7)])
        return f"+7 ({operator_code}) {number[:3]}-{number[3:5]}-{number[5:]}"

    def create_specializations(self):
        specializations_data = [
            {
                "type": "web",
                "title": "Веб-разработка",
                "description": "Курсы по созданию современных веб-приложений",
            },
            {
                "type": "mobile",
                "title": "Мобильная разработка",
                "description": "Разработка приложений для iOS и Android",
            },
            {
                "type": "data",
                "title": "Data Science",
                "description": "Анализ данных и машинное обучение",
            },
            {
                "type": "design",
                "title": "UI/UX дизайн",
                "description": "Дизайн пользовательских интерфейсов и опыта",
            },
            {
                "type": "marketing",
                "title": "Digital маркетинг",
                "description": "Интернет-маркетинг и продвижение",
            },
            {
                "type": "business",
                "title": "Бизнес-аналитика",
                "description": "Аналитика данных для бизнес-решений",
            },
        ]

        for data in specializations_data:
            Specialization.objects.get_or_create(
                type=data["type"],
                defaults={
                    "title": data["title"],
                    "description": data["description"],
                    "is_active": True,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано {len(specializations_data)} специализаций"
            )
        )

    def create_mentors(self, specializations, technologies):
        """Создает менторов с технологиями"""
        russian_names = [
            ("Иван", "Иванов"),
            ("Петр", "Петров"),
            ("Сергей", "Сергеев"),
            ("Алексей", "Алексеев"),
            ("Дмитрий", "Дмитриев"),
            ("Андрей", "Андреев"),
            ("Михаил", "Михайлов"),
            ("Анна", "Аннова"),
            ("Елена", "Еленова"),
            ("Ольга", "Ольгова"),
        ]

        # Маппинг специализаций к соответствующим технологиям
        specialization_tech_map = {
            "web": [
                "JavaScript",
                "React",
                "Vue.js",
                "Node.js",
                "TypeScript",
                "HTML/CSS",
            ],
            "mobile": ["React Native", "Flutter", "Kotlin", "Swift", "Java"],
            "data": [
                "Python",
                "TensorFlow",
                "PyTorch",
                "Pandas",
                "NumPy",
                "Scikit-learn",
            ],
            "design": [
                "Figma",
                "Adobe XD",
                "Sketch",
                "Photoshop",
                "Illustrator",
            ],
            "marketing": [
                "SEO",
                "Google Analytics",
                "Facebook Ads",
                "Email Marketing",
            ],
            "business": ["Excel", "SQL", "Tableau", "Power BI", "Python"],
        }

        for i in range(5):
            has_email = random.choice([True, False])
            has_phone = not has_email if random.choice([True, False]) else True

            email = f"mentor{i + 1}@academy.com" if has_email else None
            phone = self.generate_phone() if has_phone else None

            while phone and User.objects.filter(phone=phone).exists():
                phone = self.generate_phone()

            if email and User.objects.filter(email=email).exists():
                continue

            first_name, last_name = russian_names[i]

            user = User.objects.create_user(
                email=email,
                phone=phone,
                password="password",
                first_name=first_name,
                last_name=last_name,
                role="mentor",
            )

            specialization = (
                random.choice(specializations) if specializations else None
            )

            # Создаем ментора
            mentor = Mentor.objects.create(
                user=user,
                specialization=specialization,
                experience_years=random.randint(3, 15),
            )

            # Добавляем технологии ментору
            if specialization:
                # Получаем технологии, связанные со специализацией ментора
                specialization_type = specialization.type
                relevant_tech_names = specialization_tech_map.get(
                    specialization_type, []
                )

                # Ищем соответствующие объекты Technology
                relevant_technologies = []
                for tech_name in relevant_tech_names:
                    # Пытаемся найти технологию по имени
                    tech = Technology.objects.filter(name=tech_name).first()
                    if tech:
                        relevant_technologies.append(tech)
                    else:
                        # Если технологии нет, создаем ее
                        tech = Technology.objects.create(name=tech_name)
                        relevant_technologies.append(tech)

                # Добавляем случайные технологии из общих технологий
                additional_technologies = random.sample(
                    list(technologies),
                    k=min(random.randint(1, 3), len(technologies)),
                )

                # Объединяем и добавляем все технологии ментору
                all_technologies = list(
                    set(relevant_technologies + additional_technologies)
                )
                mentor.technology.set(all_technologies[: random.randint(2, 5)])
            else:
                # Если нет специализации, добавляем случайные технологии
                mentor_technologies = random.sample(
                    list(technologies),
                    k=min(random.randint(2, 5), len(technologies)),
                )
                mentor.technology.set(mentor_technologies)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Создан ментор {first_name} {last_name} "
                    f"с {mentor.technology.count()} технологиями"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("Создано 5 менторов с технологиями")
        )

    def create_students(self):
        russian_names = [
            ("Александр", "Александров"),
            ("Владимир", "Владимиров"),
            ("Николай", "Николаев"),
            ("Артем", "Артемов"),
            ("Максим", "Максимов"),
            ("Кирилл", "Кириллов"),
            ("Екатерина", "Екатеринина"),
            ("Мария", "Мариева"),
            ("Наталья", "Натальева"),
            ("Светлана", "Светланова"),
        ]

        for i in range(10):
            has_email = random.choice([True, False])
            has_phone = not has_email if random.choice([True, False]) else True

            email = f"student{i + 1}@academy.com" if has_email else None
            phone = self.generate_phone() if has_phone else None

            while phone and User.objects.filter(phone=phone).exists():
                phone = self.generate_phone()

            if email and User.objects.filter(email=email).exists():
                continue

            first_name, last_name = russian_names[i]

            user = User.objects.create_user(
                email=email,
                phone=phone,
                password="password",
                first_name=first_name,
                last_name=last_name,
                role="student",
            )

            Student.objects.create(user=user)
        self.stdout.write(self.style.SUCCESS("Создано 10 студентов"))

    def create_technologies(self):
        technologies = [
            "ЕГЭ",
            "Информатика",
            "Математика",
            "Подготовка к экзаменам",
            "Python",
            "JavaScript",
            "React",
            "Django",
            "Vue.js",
            "Node.js",
            "TypeScript",
            "PostgreSQL",
            "MongoDB",
            "Docker",
            "Kubernetes",
            "AWS",
            "Flask",
            "FastAPI",
            "GraphQL",
            "Redis",
            "Celery",
            "TensorFlow",
            "PyTorch",
            "Pandas",
            "NumPy",
            "Scikit-learn",
            "Java",
            "Spring Boot",
            "Kotlin",
            "Swift",
            "Flutter",
            "React Native",
            "Go",
            "Rust",
            # Дополнительные технологии для разных специализаций
            "HTML/CSS",
            "Figma",
            "Adobe XD",
            "Sketch",
            "Photoshop",
            "Illustrator",
            "SEO",
            "Google Analytics",
            "Facebook Ads",
            "Email Marketing",
            "Excel",
            "SQL",
            "Tableau",
            "Power BI",
            "Unity",
            "C#",
            "C++",
            "PHP",
            "Laravel",
            "Ruby",
            "Rails",
        ]

        tech_objects = []
        for tech_name in technologies:
            tech, created = Technology.objects.get_or_create(
                name=tech_name, defaults={"name": tech_name}
            )
            tech_objects.append(tech)

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано/найдено {len(tech_objects)} технологий"
            )
        )
        return tech_objects

    def create_courses(
        self,
        count=10,
        technologies=None,
        modules_per_course=3,
        lessons_per_module=5,
        radio_questions_per_module=2,
        checkbox_questions_per_module=2,
    ):
        if technologies is None:
            technologies = list(Technology.objects.all())

        course_titles = [
            "ЕГЭ с нуля",
            "ЕГЭ по информатике",
            "ЕГЭ математика (профиль)",
            "ЕГЭ русский язык",
            "Пробные варианты ЕГЭ",
        ]

        course_descriptions = [
            "Полный старт подготовки к ЕГЭ: формат экзамена, стратегия "
            "набора баллов, тайм-менеджмент и разбор типовых ошибок.",
            "Системная подготовка к ЕГЭ по информатике: задания 1–27, "
            "теория, практика и пробные варианты с автопроверкой.",
            "Подготовка к профильной математике: алгебра, геометрия, "
            "задания части 1 и развёрнутые ответы части 2.",
            "Подготовка к ЕГЭ по русскому языку: орфография, пунктуация, "
            "сочинение и задания с кратким ответом.",
            "Сборник пробных вариантов ЕГЭ в формате реального экзамена "
            "с таймером и итоговым баллом.",
        ]

        for i in range(min(count, len(course_titles))):
            course = Course.objects.create(
                title=course_titles[i],
                description=course_descriptions[i],
                is_active=True,
            )

            # Теги: ЕГЭ-курсы получают релевантные технологии
            if "информатик" in course_titles[i].lower():
                preferred = [
                    t
                    for t in technologies
                    if t.name in ("ЕГЭ", "Информатика", "Python")
                ]
            elif "математ" in course_titles[i].lower():
                preferred = [
                    t for t in technologies if t.name in ("ЕГЭ", "Математика")
                ]
            else:
                preferred = [
                    t
                    for t in technologies
                    if t.name
                    in (
                        "ЕГЭ",
                        "Подготовка к экзаменам",
                        "Математика",
                        "Информатика",
                    )
                ]
            if not preferred:
                preferred = technologies
            course.technology.set(preferred[: min(3, len(preferred))])

            # Создаем модули для курса
            self.create_modules_for_course(
                course=course,
                count=modules_per_course,
                lessons_per_module=lessons_per_module,
                radio_questions_per_module=radio_questions_per_module,
                checkbox_questions_per_module=checkbox_questions_per_module,
            )
            self.create_exam_for_course(course)

            self.stdout.write(
                self.style.SUCCESS(f"Создан курс: {course_titles[i]}")
            )

    def create_modules_for_course(
        self,
        course,
        count=3,
        lessons_per_module=5,
        radio_questions_per_module=2,
        checkbox_questions_per_module=2,
        challenges_per_module=2,
    ):
        module_titles = [
            "Введение в ЕГЭ",
            "Задания с кратким ответом",
            "Задания повышенной сложности",
            "Пробные варианты",
            "Разбор ошибок",
            "Стратегия на максимум баллов",
            "Финальная подготовка",
            "Итоговый контроль",
        ]

        module_descriptions = [
            "Формат экзамена, правила и система оценивания",
            "Типовые задания части 1 и техника быстрого решения",
            "Задания части 2 и развёрнутые ответы",
            "Полноценные варианты в условиях экзамена",
            "Разбор частых ошибок и типичных ловушек",
            "Как распределить время и набрать целевой балл",
            "Повторение ключевых тем перед экзаменом",
            "Финальный тест для проверки готовности",
        ]

        lesson_titles = [
            "Что такое ЕГЭ и как устроен экзамен",
            "Система баллов и пересчёт",
            "Как составить план подготовки",
            "Тайм-менеджмент на экзамене",
            "Типовые задания части 1",
            "Задания на логику и анализ",
            "Развёрнутый ответ: структура",
            "Частые ошибки и как их избежать",
            "Работа с бланками ответов",
            "Пробный вариант: старт",
            "Разбор задания 5",
            "Разбор задания 12",
            "Разбор задания 17",
            "Разбор задания 23",
            "Итоговый пробный вариант",
        ]

        lesson_content = [
            "В этом уроке разберём структуру ЕГЭ, длительность и правила проведения.",
            "Узнаете, как первичные баллы переводятся в итоговую оценку.",
            "Составим индивидуальный план подготовки до экзамена.",
            "Научимся распределять время между частями экзамена.",
            "Разберём формат заданий с кратким ответом и типовые подходы.",
            "Потренируемся в задачах на логику и анализ данных.",
            "Разберём структуру развёрнутого ответа и критерии оценивания.",
            "Разберём типичные ошибки учеников и способы их избежать.",
            "Научимся правильно заполнять бланки и черновики.",
            "Начнём проходить пробный вариант в формате экзамена.",
            "Подробный разбор одного из ключевых заданий варианта.",
            "Разбор задания средней сложности с пошаговым решением.",
            "Разбор задания повышенной сложности.",
            "Разбор задания из второй части экзамена.",
            "Финальный пробный вариант для самопроверки перед ЕГЭ.",
        ]

        radio_questions_data = [
            {
                "title": "Основы языка программирования",
                "question": "Какой тип данных используется для хранения "
                "целых чисел?",
                "explanation": "int используется для хранения целых чисел в "
                "большинстве языков программирования.",
                "answers": [
                    ("int", True),
                    ("float", False),
                    ("str", False),
                    ("bool", False),
                ],
            },
            {
                "title": "Управляющие конструкции",
                "question": "Какая конструкция используется для выполнения "
                "кода при условии?",
                "explanation": "if - это условный оператор, выполняющий "
                "код при истинности условия.",
                "answers": [
                    ("for", False),
                    ("while", False),
                    ("if", True),
                    ("switch", False),
                ],
            },
            {
                "title": "Функции",
                "question": "Как называется функция, которая "
                "вызывает саму себя?",
                "explanation": "Рекурсивная функция - это функция, которая "
                "вызывает саму себя в своем теле.",
                "answers": [
                    ("Итеративная", False),
                    ("Рекурсивная", True),
                    ("Анонимная", False),
                    ("Вложенная", False),
                ],
            },
            {
                "title": "ООП",
                "question": "Какой принцип ООП позволяет скрывать "
                "внутреннюю реализацию?",
                "explanation": "Инкапсуляция скрывает детали реализации и "
                "предоставляет только интерфейс для "
                "взаимодействия.",
                "answers": [
                    ("Наследование", False),
                    ("Полиморфизм", False),
                    ("Инкапсуляция", True),
                    ("Абстракция", False),
                ],
            },
            {
                "title": "Базы данных",
                "question": "Какой язык используется для работы с "
                "реляционными базами данных?",
                "explanation": "SQL (Structured Query Language) - "
                "стандартный язык для работы с "
                "реляционными БД.",
                "answers": [
                    ("Python", False),
                    ("Java", False),
                    ("SQL", True),
                    ("HTML", False),
                ],
            },
        ]

        checkbox_questions_data = [
            {
                "title": "Типы данных в Python",
                "question": "Какие из перечисленных типов данных "
                "являются встроенными в Python?",
                "explanation": "В Python встроенными типами "
                "являются int, float, str, list, "
                "dict, tuple, set и bool.",
                "points": 2,
                "answers": [
                    ("int", True),
                    ("float", True),
                    ("array", False),
                    ("list", True),
                ],
            },
            {
                "title": "Фреймворки веб-разработки",
                "question": "Какие из перечисленных являются "
                "Python-фреймворками для веб-разработки?",
                "explanation": "Django, Flask и FastAPI - популярные "
                "Python-фреймворки. React - это "
                "JavaScript библиотека.",
                "points": 3,
                "answers": [
                    ("Django", True),
                    ("React", False),
                    ("Flask", True),
                    ("FastAPI", True),
                ],
            },
            {
                "title": "HTTP методы",
                "question": "Какие HTTP методы существуют?",
                "explanation": "GET, POST, PUT, DELETE - основные "
                "HTTP методы. SELECT - это SQL запрос.",
                "points": 2,
                "answers": [
                    ("GET", True),
                    ("POST", True),
                    ("SELECT", False),
                    ("DELETE", True),
                ],
            },
            {
                "title": "Системы контроля версий",
                "question": "Какие из перечисленных являются "
                "системами контроля версий?",
                "explanation": "Git и Mercurial - распределенные системы "
                "контроля версий. Docker - "
                "для контейнеризации.",
                "points": 2,
                "answers": [
                    ("Git", True),
                    ("Docker", False),
                    ("Mercurial", True),
                    ("Kubernetes", False),
                ],
            },
            {
                "title": "Базы данных",
                "question": "Какие из перечисленных "
                "являются NoSQL базами данных?",
                "explanation": "MongoDB и Redis - NoSQL базы данных. "
                "PostgreSQL и MySQL - реляционные.",
                "points": 2,
                "answers": [
                    ("PostgreSQL", False),
                    ("MongoDB", True),
                    ("MySQL", False),
                    ("Redis", True),
                ],
            },
        ]

        # Данные для задач программирования
        coding_challenges_data = [
            {
                "title": "Сумма двух чисел",
                "description": "Напишите функцию, которая принимает два числа и возвращает их сумму.",
                "instructions": "Реализуйте функцию `add(a, b)`, которая принимает два числа и возвращает их сумму.",
                "initial_code": "def add(a, b):\n    # Напишите ваш код здесь\n    pass",
                "solution_template": "def add(a, b):\n    return a + b",
                "difficulty": "beginner",
                "points": 5,
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {
                        "input_data": "1\n2",
                        "expected_output": "3",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "-1\n1",
                        "expected_output": "0",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "0\n0",
                        "expected_output": "0",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "100\n200",
                        "expected_output": "300",
                        "is_hidden": True,
                    },
                ],
            },
            {
                "title": "Проверка на четность",
                "description": "Напишите функцию, которая проверяет, является ли число четным.",
                "instructions": "Реализуйте функцию `is_even(n)`, которая возвращает True, если число четное, и False в противном случае.",
                "initial_code": "def is_even(n):\n    # Напишите ваш код здесь\n    pass",
                "solution_template": "def is_even(n):\n    return n % 2 == 0",
                "difficulty": "beginner",
                "points": 5,
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {
                        "input_data": "2",
                        "expected_output": "True",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "3",
                        "expected_output": "False",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "0",
                        "expected_output": "True",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "101",
                        "expected_output": "False",
                        "is_hidden": True,
                    },
                ],
            },
            {
                "title": "Поиск максимума",
                "description": "Напишите функцию, которая находит максимальное число в списке.",
                "instructions": "Реализуйте функцию `find_max(arr)`, которая принимает список чисел и возвращает максимальное значение.",
                "initial_code": "def find_max(arr):\n    # Напишите ваш код здесь\n    pass",
                "solution_template": "def find_max(arr):\n    if not arr:\n        return None\n    return max(arr)",
                "difficulty": "easy",
                "points": 10,
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {
                        "input_data": "[1, 2, 3, 4, 5]",
                        "expected_output": "5",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "[-1, -5, -2, -3]",
                        "expected_output": "-1",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "[42]",
                        "expected_output": "42",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "[10, 20, 30, 5, 25]",
                        "expected_output": "30",
                        "is_hidden": True,
                    },
                ],
            },
            {
                "title": "Факториал числа",
                "description": "Напишите рекурсивную функцию для вычисления факториала числа.",
                "instructions": "Реализуйте функцию `factorial(n)`, которая возвращает факториал числа n (n!).",
                "initial_code": "def factorial(n):\n    # Напишите ваш код здесь\n    pass",
                "solution_template": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                "difficulty": "easy",
                "points": 10,
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {
                        "input_data": "5",
                        "expected_output": "120",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "0",
                        "expected_output": "1",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "1",
                        "expected_output": "1",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "7",
                        "expected_output": "5040",
                        "is_hidden": True,
                    },
                ],
            },
            {
                "title": "Палиндром",
                "description": "Напишите функцию, которая проверяет, является ли строка палиндромом.",
                "instructions": "Реализуйте функцию `is_palindrome(s)`, которая возвращает True, если строка читается одинаково слева направо и справа налево.",
                "initial_code": "def is_palindrome(s):\n    # Напишите ваш код здесь\n    pass",
                "solution_template": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
                "difficulty": "medium",
                "points": 15,
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {
                        "input_data": "racecar",
                        "expected_output": "True",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "hello",
                        "expected_output": "False",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "A man a plan a canal panama",
                        "expected_output": "True",
                        "is_hidden": False,
                    },
                    {
                        "input_data": "Was it a car or a cat I saw",
                        "expected_output": "True",
                        "is_hidden": True,
                    },
                ],
            },
        ]

        for module_index in range(count):
            if module_index < len(module_titles):
                title = module_titles[module_index]
                description = module_descriptions[module_index]
            else:
                title = f"Модуль {module_index + 1}"
                description = f"Описание модуля {module_index + 1}"

            module = Module.objects.create(
                course=course,
                title=title,
                description=description,
                order_index=module_index + 1,
                is_active=random.choice([True, False, True]),
            )

            # Создаем теоретические уроки для модуля
            for lesson_index in range(lessons_per_module):
                LessonTheory.objects.create(
                    module=module,
                    title=lesson_titles[lesson_index % len(lesson_titles)],
                    content=lesson_content[lesson_index % len(lesson_content)],
                    order_index=lesson_index + 1,
                    is_active=random.choice([True, False, True]),
                )

            # Создаем radio-вопросы для модуля
            for radio_index in range(radio_questions_per_module):
                if radio_index < len(radio_questions_data):
                    question_data = radio_questions_data[radio_index]
                else:
                    question_data = {
                        "title": f"Radio вопрос {radio_index + 1}",
                        "question": f"Текст вопроса {radio_index + 1}?",
                        "explanation": f"Пояснение к вопросу "
                        f"{radio_index + 1}",
                        "answers": [
                            ("Вариант 1", random.choice([True, False])),
                            ("Вариант 2", random.choice([True, False])),
                            ("Вариант 3", random.choice([True, False])),
                            ("Вариант 4", random.choice([True, False])),
                        ],
                    }
                    correct_count = sum(
                        1 for a in question_data["answers"] if a[1]
                    )
                    if correct_count != 1:
                        question_data["answers"] = [
                            (text, i == 0)
                            for i, (text, _) in enumerate(
                                question_data["answers"]
                            )
                        ]

                radio_question = LessonRadioQuestion.objects.create(
                    module=module,
                    title=question_data["title"],
                    question_text=question_data["question"],
                    explanation=question_data["explanation"],
                    order_index=radio_index + 1,
                    is_active=random.choice([True, False, True]),
                    points=random.randint(1, 3),
                )

                for answer_index, (answer_text, is_correct) in enumerate(
                    question_data["answers"]
                ):
                    RadioAnswerOption.objects.create(
                        question=radio_question,
                        text=answer_text,
                        is_correct=is_correct,
                        order_index=answer_index + 1,
                    )

            # Создаем checkbox-вопросы для модуля
            for checkbox_index in range(checkbox_questions_per_module):
                if checkbox_index < len(checkbox_questions_data):
                    question_data = checkbox_questions_data[checkbox_index]
                else:
                    num_answers = random.randint(3, 5)
                    correct_count = random.randint(1, 3)
                    answers = []
                    for i in range(num_answers):
                        answers.append((f"Вариант {i+1}", i < correct_count))

                    question_data = {
                        "title": f"Checkbox вопрос {checkbox_index + 1}",
                        "question": f"Текст вопроса {checkbox_index + 1}?",
                        "explanation": f"Пояснение к вопросу "
                        f"{checkbox_index + 1}",
                        "points": random.randint(2, 5),
                        "answers": answers,
                    }

                checkbox_question = LessonCheckBoxQuestion.objects.create(
                    module=module,
                    title=question_data["title"],
                    question_text=question_data["question"],
                    explanation=question_data["explanation"],
                    order_index=checkbox_index + 1,
                    is_active=random.choice([True, False, True]),
                    points=question_data.get("points", random.randint(2, 5)),
                )

                for answer_index, (answer_text, is_correct) in enumerate(
                    question_data["answers"]
                ):
                    CheckBoxAnswerOption.objects.create(
                        question=checkbox_question,
                        text=answer_text,
                        is_correct=is_correct,
                        order_index=answer_index + 1,
                    )

            # Создаем задачи программирования для модуля
            for challenge_index in range(challenges_per_module):
                if challenge_index < len(coding_challenges_data):
                    challenge_data = coding_challenges_data[challenge_index]
                else:
                    # Случайная задача
                    difficulties = ["beginner", "easy", "medium", "hard"]
                    challenge_data = {
                        "title": f"Задача {challenge_index + 1}",
                        "description": f"Описание задачи {challenge_index + 1}",
                        "instructions": f"Инструкция для задачи {challenge_index + 1}",
                        "initial_code": "def solve():\n    pass",
                        "solution_template": "def solve():\n    return True",
                        "difficulty": random.choice(difficulties),
                        "points": random.randint(5, 30),
                        "time_limit_ms": random.choice([1000, 2000, 3000]),
                        "memory_limit_mb": random.choice([128, 256, 512]),
                        "test_cases": [
                            {
                                "input_data": f"input_{i}",
                                "expected_output": f"output_{i}",
                                "is_hidden": i > 0,
                            }
                            for i in range(1, 4)
                        ],
                    }

                cc_kwargs = {
                    "course": course,
                    "module": module,
                    "title": challenge_data["title"],
                    "description": challenge_data["description"],
                    "instructions": challenge_data["instructions"],
                    "initial_code": challenge_data["initial_code"],
                    "solution_template": challenge_data["solution_template"],
                    "difficulty": challenge_data["difficulty"],
                    "points": challenge_data["points"],
                    "time_limit_ms": challenge_data["time_limit_ms"],
                    "memory_limit_mb": challenge_data["memory_limit_mb"],
                    "order_index": challenge_index + 1,
                    "is_active": random.choice([True, False, True]),
                }
                challenge = CodingChallenge.objects.create(**cc_kwargs)

                # Создаем тестовые случаи для задачи
                for test_index, test_data in enumerate(
                    challenge_data["test_cases"]
                ):
                    TestCase.objects.create(
                        challenge=challenge,
                        input_data=test_data["input_data"],
                        expected_output=test_data["expected_output"],
                        is_hidden=test_data["is_hidden"],
                        order_index=test_index + 1,
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Создана задача: {challenge.title} с {challenge.test_cases.count()} тестами"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Создан модуль {module.title} с "
                    f"{lessons_per_module} уроками, "
                    f"{radio_questions_per_module} radio-вопросами, "
                    f"{checkbox_questions_per_module} checkbox-вопросами и "
                    f"{challenges_per_module} задачами"
                )
            )

    def create_exam_for_course(self, course):
        """Контрольная работа (КР) с мини-теорией и заданиями после модулей 1–2."""
        modules = list(course.modules.order_by("order_index"))
        if len(modules) < 2:
            return

        exam = Exam.objects.create(
            course=course,
            title="Контрольная работа",
            description=(
                "Промежуточная контрольная по материалам первых модулей. "
                "Таймер запускается после нажатия «Начать»."
            ),
            is_active=True,
            duration_minutes=30,
            navigation_mode=Exam.NavigationMode.FREE,
            tab_policy=Exam.TabPolicy.LOG_ONLY,
            tab_warn_limit=2,
            mentor_unlock_required=False,
            pass_score_percent=60,
        )
        exam.prerequisite_modules.set(modules[:2])
        exam.order_index = len(modules)
        exam.save(update_fields=["order_index"])

        LessonTheory.objects.create(
            exam=exam,
            title="Памятка перед КР",
            content=(
                "<p>Кратко повторите правила:</p>"
                "<ul>"
                "<li>Отвечайте на все задания — теория не даёт баллов, но открывает контекст.</li>"
                "<li>Можно переключаться между заданиями, пока не истекло время.</li>"
                "<li>После завершения сразу увидите результат.</li>"
                "</ul>"
            ),
            order_index=1,
            is_active=True,
        )

        radio = LessonRadioQuestion.objects.create(
            exam=exam,
            title="Формат ЕГЭ",
            question_text="Сколько основных частей в ЕГЭ по информатике?",
            explanation="В ЕГЭ по информатике две части: с кратким и развёрнутым ответом.",
            order_index=2,
            is_active=True,
            points=5,
        )
        for i, (text, correct) in enumerate(
            [
                ("Одна", False),
                ("Две", True),
                ("Три", False),
                ("Четыре", False),
            ],
            start=1,
        ):
            RadioAnswerOption.objects.create(
                question=radio,
                text=text,
                is_correct=correct,
                order_index=i,
            )

        checkbox = LessonCheckBoxQuestion.objects.create(
            exam=exam,
            title="Инструменты на экзамене",
            question_text="Что обычно разрешено использовать на ЕГЭ по информатике?",
            explanation="На экзамене доступны КЕГЭ и черновик; телефон запрещён.",
            order_index=3,
            is_active=True,
            points=10,
        )
        for i, (text, correct) in enumerate(
            [
                ("КЕГЭ (компьютер)", True),
                ("Черновик", True),
                ("Личный телефон", False),
                ("Свой ноутбук", False),
            ],
            start=1,
        ):
            CheckBoxAnswerOption.objects.create(
                question=checkbox,
                text=text,
                is_correct=correct,
                order_index=i,
            )

        challenge = CodingChallenge.objects.create(
            course=course,
            exam=exam,
            title="Сумма двух чисел",
            description="По двум целым числам выведите их сумму.",
            instructions="Считайте два числа и выведите сумму.",
            initial_code=(
                "a = int(input())\n" "b = int(input())\n" "# ваш код\n"
            ),
            solution_template="a = int(input())\nb = int(input())\nprint(a + b)",
            difficulty="beginner",
            points=15,
            time_limit_ms=2000,
            memory_limit_mb=256,
            order_index=4,
            is_active=True,
        )
        for i, (inp, out, hidden) in enumerate(
            [
                ("2\n3\n", "5", False),
                ("10\n20\n", "30", False),
                ("-1\n1\n", "0", True),
            ],
            start=1,
        ):
            TestCase.objects.create(
                challenge=challenge,
                input_data=inp,
                expected_output=out,
                is_hidden=hidden,
                order_index=i,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Создана КР «{exam.title}» для курса «{course.title}» "
                f"(пререквизиты: {modules[0].title}, {modules[1].title})"
            )
        )
