"""Upsert единственного курса ЕГЭ без полного --clear (для prod)."""

from django.core.management.base import BaseCommand
from django.db import transaction
from fixture.course_fixtures import EGE_INFORMATIKA
from fixture.management.commands.seed_data import Command as SeedCommand

from content.models import Course, Module
from users.models import User


class Command(BaseCommand):
    help = (
        "Создаёт/обновляет курс «ЕГЭ-информатика» и деактивирует прочие "
        "активные курсы. Не очищает пользователей и прогресс."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            seed = SeedCommand()
            technologies = seed.create_technologies()
            tech_by_name = {t.name: t for t in technologies}
            mentor_user = (
                User.objects.filter(role="mentor").first()
                or User.objects.filter(role="admin").first()
            )

            fixture = EGE_INFORMATIKA
            slug = fixture["slug"]
            course, created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": fixture["title"],
                    "description": fixture["description"],
                    "is_active": True,
                    "mentor": mentor_user,
                },
            )
            if not created:
                course.title = fixture["title"]
                course.description = fixture["description"]
                course.is_active = True
                if mentor_user and not course.mentor_id:
                    course.mentor = mentor_user
                course.save()
                course.modules.all().delete()
                course.exams.all().delete()

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
                    seed._create_lesson(
                        course=course,
                        module=module,
                        exam=None,
                        lesson=lesson,
                        order_index=lesson_index,
                    )

            deactivated = (
                Course.objects.exclude(slug=slug)
                .filter(is_active=True)
                .update(is_active=False)
            )
            action = "создан" if created else "обновлён"
            self.stdout.write(
                self.style.SUCCESS(
                    f"Курс «{course.title}» {action}; "
                    f"модулей: {len(modules)}; "
                    f"деактивировано прочих: {deactivated}"
                )
            )
