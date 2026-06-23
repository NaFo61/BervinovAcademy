import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from fixture.course_fixtures import COURSE_FIXTURES

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

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["clear"]:
                self.clear_data()

            self.create_superuser()
            self.create_specializations()
            specializations = list(Specialization.objects.all())

            technologies = self.create_technologies()

            self.create_mentors(specializations, technologies)
            self.create_students()
            self.seed_course_fixtures(technologies)

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

    def seed_course_fixtures(self, technologies):
        tech_by_name = {t.name: t for t in technologies}
        mentor_user = User.objects.filter(role="mentor").first()

        for fixture in COURSE_FIXTURES:
            course = Course.objects.create(
                title=fixture["title"],
                description=fixture["description"],
                is_active=True,
                mentor=mentor_user,
            )
            tags = [
                tech_by_name[name]
                for name in fixture.get("technologies", [])
                if name in tech_by_name
            ]
            if tags:
                course.technology.set(tags)

            modules = []
            for module_index, module_data in enumerate(
                fixture.get("modules", []), start=1
            ):
                module = Module.objects.create(
                    course=course,
                    title=module_data["title"],
                    description=module_data.get("description", ""),
                    order_index=module_index,
                    is_active=True,
                )
                modules.append(module)
                for lesson_index, lesson in enumerate(
                    module_data.get("lessons", []), start=1
                ):
                    self._create_lesson(
                        course=course,
                        module=module,
                        exam=None,
                        lesson=lesson,
                        order_index=lesson_index,
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Модуль «{module.title}»: "
                        f"{len(module_data.get('lessons', []))} уроков"
                    )
                )

            exam_data = fixture.get("exam")
            if exam_data and len(modules) >= 2:
                self._create_exam(course, modules, exam_data)

            self.stdout.write(
                self.style.SUCCESS(f"Создан курс: {course.title}")
            )

    def _lesson_common(self, lesson: dict) -> dict:
        return {
            k: lesson[k] for k in ("comment", "solution_text") if lesson.get(k)
        }

    def _create_lesson(
        self,
        *,
        course,
        module=None,
        exam=None,
        lesson: dict,
        order_index: int,
    ):
        kind = lesson["type"]
        common = self._lesson_common(lesson)

        if kind == "theory":
            LessonTheory.objects.create(
                module=module,
                exam=exam,
                title=lesson["title"],
                content=lesson["content"],
                order_index=order_index,
                is_active=True,
                **common,
            )
            return

        if kind == "radio":
            question = LessonRadioQuestion.objects.create(
                module=module,
                exam=exam,
                title=lesson["title"],
                question_text=lesson["question_text"],
                explanation=lesson.get("explanation", ""),
                points=lesson.get("points", 3),
                order_index=order_index,
                is_active=True,
                **common,
            )
            answers = lesson.get("answers", [])
            if sum(1 for _, ok in answers if ok) != 1:
                raise ValueError(
                    f"Radio «{lesson['title']}»: ровно один правильный ответ"
                )
            for i, (text, is_correct) in enumerate(answers, start=1):
                RadioAnswerOption.objects.create(
                    question=question,
                    text=text,
                    is_correct=is_correct,
                    order_index=i,
                )
            return

        if kind == "checkbox":
            question = LessonCheckBoxQuestion.objects.create(
                module=module,
                exam=exam,
                title=lesson["title"],
                question_text=lesson["question_text"],
                explanation=lesson.get("explanation", ""),
                points=lesson.get("points", 4),
                order_index=order_index,
                is_active=True,
                **common,
            )
            answers = lesson.get("answers", [])
            if not any(ok for _, ok in answers):
                raise ValueError(
                    f"Checkbox «{lesson['title']}»: нужен хотя бы один правильный ответ"
                )
            for i, (text, is_correct) in enumerate(answers, start=1):
                CheckBoxAnswerOption.objects.create(
                    question=question,
                    text=text,
                    is_correct=is_correct,
                    order_index=i,
                )
            return

        if kind == "coding":
            challenge = CodingChallenge.objects.create(
                course=course,
                module=module,
                exam=exam,
                title=lesson["title"],
                description=lesson["description"],
                instructions=lesson["instructions"],
                initial_code=lesson["initial_code"],
                solution_template=lesson.get("solution_template", ""),
                difficulty=lesson.get("difficulty", "beginner"),
                points=lesson.get("points", 10),
                time_limit_ms=lesson.get("time_limit_ms", 2000),
                memory_limit_mb=lesson.get("memory_limit_mb", 256),
                order_index=order_index,
                is_active=True,
                solution_text=lesson.get("solution_text", ""),
                comment=lesson.get("comment", ""),
            )
            for i, tc in enumerate(lesson.get("test_cases", []), start=1):
                TestCase.objects.create(
                    challenge=challenge,
                    input_data=tc["input_data"],
                    expected_output=tc["expected_output"],
                    is_hidden=tc.get("is_hidden", False),
                    order_index=i,
                )
            return

        raise ValueError(f"Неизвестный тип урока: {kind}")

    def _create_exam(self, course, modules, exam_data: dict):
        exam = Exam.objects.create(
            course=course,
            title=exam_data["title"],
            description=exam_data.get("description", ""),
            is_active=True,
            duration_minutes=exam_data.get("duration_minutes", 45),
            navigation_mode=Exam.NavigationMode.FREE,
            tab_policy=Exam.TabPolicy.LOG_ONLY,
            tab_warn_limit=2,
            mentor_unlock_required=False,
            pass_score_percent=60,
            order_index=len(modules) + 1,
        )
        exam.prerequisite_modules.set(modules[:2])

        for lesson_index, lesson in enumerate(
            exam_data.get("lessons", []), start=1
        ):
            self._create_lesson(
                course=course,
                module=None,
                exam=exam,
                lesson=lesson,
                order_index=lesson_index,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"  КР «{exam.title}» (после: {modules[0].title}, {modules[1].title})"
            )
        )
