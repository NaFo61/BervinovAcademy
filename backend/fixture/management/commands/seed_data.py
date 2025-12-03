import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from users.models import Mentor, Specialization, Student

User = get_user_model()
fake = Faker("ru_RU")


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

            self.create_mentors(specializations)
            self.create_students()

            self.stdout.write(self.style.SUCCESS("Данные созданы"))

    def clear_data(self):
        User.objects.all().delete()
        Specialization.objects.all().delete()

    def create_superuser(self):
        User.objects.create_superuser(
            email="admin@academy.com",
            phone="+7 (999) 111-22-33",
            password="password",
            first_name="Админ",
            last_name="Админов",
            role="admin",
        )

    def generate_phone(self):
        operator_code = random.choice(["937", "999", "901", "902", "905"])
        number = "".join([str(random.randint(0, 9)) for _ in range(7)])
        return f"+7 ({operator_code}) {number[:3]}-{number[3:5]}-{number[5:]}"

    def create_specializations(self):
        specializations_data = [
            {"type": "web", "title": "Веб-разработка"},
            {"type": "mobile", "title": "Мобильная разработка"},
            {"type": "data", "title": "Data Science"},
            {"type": "design", "title": "UI/UX дизайн"},
            {"type": "marketing", "title": "Digital маркетинг"},
            {"type": "business", "title": "Бизнес-аналитика"},
        ]

        for data in specializations_data:
            Specialization.objects.get_or_create(
                type=data["type"],
                defaults={
                    "title": data["title"],
                    "description": fake.text(max_nb_chars=200),
                    "is_active": True,
                },
            )

    def create_mentors(self, specializations):
        for i in range(5):
            has_email = random.choice([True, False])
            has_phone = not has_email if random.choice([True, False]) else True

            email = f"mentor{i + 1}@academy.com" if has_email else None
            phone = self.generate_phone() if has_phone else None

            while phone and User.objects.filter(phone=phone).exists():
                phone = self.generate_phone()

            if email and User.objects.filter(email=email).exists():
                continue

            user = User.objects.create_user(
                email=email,
                phone=phone,
                password="password",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="mentor",
            )

            specialization = (
                random.choice(specializations) if specializations else None
            )
            Mentor.objects.create(
                user=user,
                specialization=specialization,
                experience_years=random.randint(3, 15),
            )

    def create_students(self):
        for i in range(10):
            has_email = random.choice([True, False])
            has_phone = not has_email if random.choice([True, False]) else True

            email = f"student{i + 1}@academy.com" if has_email else None
            phone = self.generate_phone() if has_phone else None

            while phone and User.objects.filter(phone=phone).exists():
                phone = self.generate_phone()

            if email and User.objects.filter(email=email).exists():
                continue
            user = User.objects.create_user(
                email=email,
                phone=phone,
                password="password",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="student",
            )

            Student.objects.create(user=user)
