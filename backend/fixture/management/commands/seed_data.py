import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Course, LessonTheory, Module, Technology
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
            default=10,
            help="Количество создаваемых курсов",
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

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["clear"]:
                self.clear_data()

            self.create_superuser()
            self.create_specializations()
            specializations = list(Specialization.objects.all())

            # Создаем технологии ДО создания менторов
            technologies = self.create_technologies()

            self.create_mentors(
                specializations, technologies
            )  # ✅ Передаем технологии
            self.create_students()

            # Создаем курсы и связанные данные
            self.create_courses(
                count=options["courses_count"],
                technologies=technologies,
                modules_per_course=options["modules_per_course"],
                lessons_per_module=options["lessons_per_module"],
            )

            self.stdout.write(self.style.SUCCESS("Данные успешно созданы"))

    def clear_data(self):
        User.objects.all().delete()
        Specialization.objects.all().delete()
        TranslationMemory.objects.all().delete()
        Course.objects.all().delete()
        Technology.objects.all().delete()
        Module.objects.all().delete()
        LessonTheory.objects.all().delete()

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
            self.stdout.write(self.style.SUCCESS("Создано 5 менторов"))

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
    ):
        if technologies is None:
            technologies = list(Technology.objects.all())

        course_titles = [
            "Полный курс Python-разработчика",
            "Современная веб-разработка на React",
            "Data Science и машинное обучение",
            "Full Stack разработка на Django",
            "Разработка мобильных приложений на Flutter",
            "DevOps и облачные вычисления",
            "Продвинутый JavaScript и Node.js",
            "Основы UI/UX дизайна",
            "Основы кибербезопасности",
            "Разработка Blockchain и Web3",
            "Основы искусственного интеллекта",
            "Разработка игр на Unity",
            "Стратегия цифрового маркетинга",
            "Бизнес-аналитика на Python",
            "Паттерны архитектуры ПО",
        ]

        course_descriptions = [
            "Изучите Python с нуля до продвинутого уровня с "
            "реальными проектами",
            "Освойте современную веб-разработку с использованием React, "
            "Redux и современных инструментов",
            "Полное руководство по Data Science, статистике и "
            "алгоритмам машинного обучения",
            "Создавайте полноценные веб-приложения с использованием "
            "Django и React",
            "Создавайте красивые мобильные приложения для iOS и Android с "
            "использованием Flutter",
            "Изучите практики DevOps, Docker, Kubernetes и облачные "
            "платформы",
            "Глубокое погружение в продвинутые концепции JavaScript и "
            "серверную разработку",
            "Изучите принципы дизайна пользовательского интерфейса и "
            "пользовательского опыта",
            "Поймите основы кибербезопасности и лучшие практики",
            "Изучите технологию блокчейн, смарт-контракты и "
            "децентрализованные приложения",
            "Введение в концепции ИИ, нейронные сети и глубокое обучение",
            "Создавайте 2D и 3D игры с использованием игрового движка Unity",
            "Освойте стратегии цифрового маркетинга и онлайн-рекламы",
            "Изучите бизнес-аналитику с использованием Python и "
            "инструментов визуализации данных",
            "Поймите паттерны архитектуры программного обеспечения "
            "и проектирование систем",
        ]

        for i in range(min(count, len(course_titles))):
            course = Course.objects.create(
                title=course_titles[i],
                description=course_descriptions[i],
                is_active=random.choice([True, False, True]),  # Чаще активные
            )

            # Добавляем технологии к курсу
            course_technologies = random.sample(
                technologies, k=min(random.randint(2, 5), len(technologies))
            )
            course.technology.set(course_technologies)

            # Создаем модули для курса
            self.create_modules_for_course(
                course=course,
                count=modules_per_course,
                lessons_per_module=lessons_per_module,
            )

            self.stdout.write(
                self.style.SUCCESS(f"Создан курс: {course_titles[i]}")
            )

    def create_modules_for_course(self, course, count=3, lessons_per_module=5):
        module_titles = [
            "Введение и основы",
            "Основные концепции и техники",
            "Продвинутые темы и лучшие практики",
            "Реальные проекты и приложения",
            "Деплой и поддержка",
            "Оптимизация производительности",
            "Безопасность и тестирование",
            "Будущие тренды и развитие карьеры",
        ]

        module_descriptions = [
            "Изучите основы и фундаментальные концепции предмета",
            "Освойте основные техники и важные концепции",
            "Изучите продвинутые темы и лучшие практики индустрии",
            "Работайте над реальными проектами и практическими приложениями",
            "Узнайте, как развертывать и поддерживать приложения в "
            "продакшене",
            "Оптимизируйте производительность и улучшайте эффективность",
            "Реализуйте меры безопасности и стратегии тестирования",
            "Изучите будущие тренды и подготовьтесь к развитию карьеры",
        ]

        lesson_titles = [
            "Введение в тему",
            "Настройка среды разработки",
            "Базовый синтаксис и структура",
            "Работа с переменными и типами данных",
            "Управление потоком и циклы",
            "Функции и методы",
            "Объектно-ориентированное программирование",
            "Обработка ошибок и отладка",
            "Работа с файлами и вводом-выводом",
            "Введение в библиотеки и фреймворки",
            "Подключение к базам данных",
            "Разработка и использование API",
            "Тестирование и TDD",
            "Стратегии развертывания",
            "Мониторинг производительности",
            "Лучшие практики безопасности",
            "Ревью кода и совместная работа",
            "Структура проекта и архитектура",
            "Непрерывная интеграция/развертывание",
            "Советы по карьере и подготовка к собеседованию",
        ]

        lesson_content = [
            "В этом уроке мы представим основные концепции и цели курса.",
            "Узнайте, как настроить среду разработки со всеми необходимыми "
            "инструментами и конфигурациями.",
            "Поймите основные правила синтаксиса и структуру программы "
            "языка.",
            "Изучите различные типы данных и научитесь эффективно работать "
            "с переменными.",
            "Освойте операторы управления потоком и различные типы циклов для "
            "логики программы.",
            "Научитесь создавать переиспользуемые функции и методы для "
            "организации кода.",
            "Поймите принципы объектно-ориентированного программирования и "
            "паттерны проектирования.",
            "Изучите техники отладки и обработки ошибок в ваших приложениях.",
            "Изучите операции с файлами и механизмы ввода-вывода в "
            "программировании.",
            "Познакомьтесь с популярными библиотеками и фреймворками, "
            "используемыми в индустрии.",
            "Узнайте, как подключаться к базам данных и выполнять "
            "CRUD-операции.",
            "Поймите, как создавать и использовать RESTful API.",
            "Освойте методологии тестирования и подход разработки через "
            "тестирование.",
            "Изучите различные стратегии развертывания веб-приложений.",
            "Поймите, как мониторить и оптимизировать производительность "
            "приложения.",
            "Изучите лучшие практики безопасности и распространенные "
            "уязвимости.",
            "Поймите процессы ревью кода и рабочие процессы совместной "
            "разработки.",
            "Узнайте о структуре проекта и архитектурных паттернах.",
            "Освойте пайплайны CI/CD и инструменты автоматизации.",
            "Получите советы по карьере и рекомендации для технических "
            "собеседований.",
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
                is_active=random.choice([True, False, True]),  # Чаще активные
            )

            # Создаем уроки для модуля
            for lesson_index in range(lessons_per_module):
                LessonTheory.objects.create(
                    module=module,
                    title=lesson_titles[lesson_index % len(lesson_titles)],
                    content=lesson_content[lesson_index % len(lesson_content)],
                    order_index=lesson_index + 1,
                    is_active=random.choice([True, False, True]),
                    # Чаще активные
                )
