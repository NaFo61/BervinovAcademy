"""Импорт ZIP-пакета с вопросами в модуль курса."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from fixture.content_pack import ContentPackError, import_content_pack


class Command(BaseCommand):
    help = (
        "Импортирует ZIP с manifest.json и questions.json в модуль курса. "
        "Повторный импорт того же pack_id обновляет вопросы по title+type."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "archive",
            type=str,
            help="Путь к ZIP-архиву (manifest.json + questions.json)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только проверка: без записи в БД",
        )

    def handle(self, *args, **options):
        archive = Path(options["archive"]).expanduser().resolve()
        dry_run = options["dry_run"]

        try:
            result = import_content_pack(archive=archive, dry_run=dry_run)
        except ContentPackError as exc:
            raise CommandError(str(exc)) from exc

        stats = result.stats
        mode = "DRY-RUN" if result.dry_run else "OK"
        self.stdout.write(
            self.style.SUCCESS(
                f"[{mode}] pack={result.pack_id} "
                f"course={result.course_slug} "
                f"module={result.module_title} "
                f"created={stats.created} updated={stats.updated} "
                f"skipped={stats.skipped}"
            )
        )
