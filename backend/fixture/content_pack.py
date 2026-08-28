"""Импорт ZIP-пакета с вопросами в модуль курса (без полного seed)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from django.core.files.base import ContentFile
from django.db import transaction

from content.attachments import bind_parent
from content.container_lessons import CONTAINER_MODULE, next_order_in_container
from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Course,
    LessonAttachment,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonShortAnswer,
    LessonTheory,
    Module,
    RadioAnswerOption,
    TestCase,
)

SUPPORTED_TYPES = frozenset(
    {"checkbox", "radio", "short_answer", "theory", "coding"}
)
PACK_MARKER_RE = re.compile(r"<!--\s*content-pack:([a-z0-9_-]+)\s*-->")
PACK_MARKER_FMT = "<!-- content-pack:{pack_id} -->"


@dataclass
class ImportStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ImportResult:
    pack_id: str
    course_slug: str
    module_title: str
    dry_run: bool
    stats: ImportStats
    module_id: int | None = None


@dataclass
class PackPreview:
    pack_id: str
    course_slug: str
    module_title: str
    lesson_count: int
    lessons: list[dict]
    manifest: dict


class ContentPackError(Exception):
    """Ошибка валидации или импорта пакета."""


def pack_marker(pack_id: str) -> str:
    return PACK_MARKER_FMT.format(pack_id=pack_id)


def extract_pack_marker(description: str) -> str | None:
    if not description:
        return None
    match = PACK_MARKER_RE.search(description)
    return match.group(1) if match else None


def ensure_pack_marker(description: str, pack_id: str) -> str:
    marker = pack_marker(pack_id)
    if marker in (description or ""):
        return description
    base = (description or "").rstrip()
    if base:
        return f"{base}\n{marker}"
    return marker


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise ContentPackError("В архиве нет manifest.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentPackError(
            f"manifest.json: невалидный JSON — {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ContentPackError("manifest.json должен быть объектом")
    for key in ("pack_id", "course_slug", "module_title"):
        if not str(data.get(key, "")).strip():
            raise ContentPackError(f"manifest.json: обязательное поле «{key}»")
    return data


def load_questions(path: Path) -> tuple[list[dict], str]:
    if not path.is_file():
        raise ContentPackError("В архиве нет questions.json")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentPackError(
            f"questions.json: невалидный JSON — {exc}"
        ) from exc

    if isinstance(raw, list):
        lessons = raw
        meta = {}
    elif isinstance(raw, dict):
        meta = raw.get("meta") or {}
        lessons = raw.get("lessons")
        if lessons is None:
            raise ContentPackError(
                "questions.json: нужен массив «lessons» или корневой массив"
            )
    else:
        raise ContentPackError("questions.json: ожидается объект или массив")

    if not isinstance(lessons, list) or not lessons:
        raise ContentPackError("questions.json: список вопросов пуст")

    images_dir = str(meta.get("images_dir") or "images/").strip()
    if not images_dir.endswith("/"):
        images_dir = f"{images_dir}/"

    validated: list[dict] = []
    for index, item in enumerate(lessons, start=1):
        if not isinstance(item, dict):
            raise ContentPackError(
                f"questions.json: элемент #{index} не объект"
            )
        kind = str(item.get("type", "")).strip()
        if kind not in SUPPORTED_TYPES:
            raise ContentPackError(
                f"questions.json #{index}: неизвестный type «{kind}»"
            )
        if not str(item.get("title", "")).strip():
            raise ContentPackError(f"questions.json #{index}: пустой title")
        validated.append(item)

    return validated, images_dir


def validate_lesson_payload(kind: str, lesson: dict) -> None:
    title = lesson["title"]
    if kind in ("radio", "checkbox"):
        answers = lesson.get("answers") or []
        if not answers:
            raise ContentPackError(f"«{title}»: нужен массив answers")
        if kind == "radio" and sum(1 for row in answers if row[1]) != 1:
            raise ContentPackError(
                f"Radio «{title}»: ровно один правильный ответ"
            )
        if kind == "checkbox" and not any(row[1] for row in answers):
            raise ContentPackError(
                f"Checkbox «{title}»: нужен хотя бы один правильный ответ"
            )
    elif kind == "short_answer":
        if not str(lesson.get("correct_answer", "")).strip():
            raise ContentPackError(
                f"Short answer «{title}»: нужен correct_answer"
            )
    elif kind == "theory":
        if not str(lesson.get("content", "")).strip():
            raise ContentPackError(f"Theory «{title}»: нужен content")
    elif kind == "coding":
        for key in ("description", "instructions", "initial_code"):
            if not str(lesson.get(key, "")).strip():
                raise ContentPackError(
                    f"Coding «{title}»: обязательное поле «{key}»"
                )


def resolve_module(
    *, course: Course, manifest: dict, dry_run: bool = False
) -> Module | None:
    pack_id = manifest["pack_id"]
    module_title = manifest["module_title"]
    create_module = bool(manifest.get("create_module", False))

    for module in course.modules.all():
        if extract_pack_marker(module.description) == pack_id:
            return module

    module = course.modules.filter(title=module_title).first()
    if module:
        if not dry_run and extract_pack_marker(module.description) != pack_id:
            module.description = ensure_pack_marker(
                module.description, pack_id
            )
            module.save(update_fields=["description"])
        return module

    if not create_module:
        raise ContentPackError(
            f"Модуль «{module_title}» не найден в курсе «{course.slug}». "
            "Создайте модуль вручную или укажите create_module: true"
        )

    if dry_run:
        return None

    description = ensure_pack_marker(
        str(manifest.get("module_description") or ""),
        pack_id,
    )
    return Module.objects.create(
        course=course,
        title=module_title,
        description=description,
        is_active=True,
    )


def _lesson_common(lesson: dict) -> dict:
    data = {
        key: lesson[key]
        for key in ("comment", "solution_text", "video_url", "explanation")
        if lesson.get(key)
    }
    return data


def _find_lesson(module: Module | None, kind: str, title: str):
    if module is None:
        return None
    mapping = {
        "theory": LessonTheory,
        "radio": LessonRadioQuestion,
        "checkbox": LessonCheckBoxQuestion,
        "short_answer": LessonShortAnswer,
        "coding": CodingChallenge,
    }
    model = mapping[kind]
    return model.objects.filter(module=module, title=title).first()


def _upsert_radio(
    *, module: Module, lesson: dict, order_index: int, stats: ImportStats
):
    common = _lesson_common(lesson)
    existing = _find_lesson(module, "radio", lesson["title"])
    if existing:
        for key, value in common.items():
            setattr(existing, key, value)
        existing.question_text = lesson["question_text"]
        existing.points = lesson.get("points", 3)
        existing.is_active = True
        existing.order_index = order_index
        existing.save()
        existing.answers.all().delete()
        question = existing
        stats.updated += 1
    else:
        question = LessonRadioQuestion.objects.create(
            module=module,
            title=lesson["title"],
            question_text=lesson["question_text"],
            points=lesson.get("points", 3),
            order_index=order_index,
            is_active=True,
            **common,
        )
        stats.created += 1

    for i, (text, is_correct) in enumerate(lesson.get("answers", []), start=1):
        RadioAnswerOption.objects.create(
            question=question,
            text=text,
            is_correct=is_correct,
            order_index=i,
        )
    return question


def _upsert_checkbox(
    *, module: Module, lesson: dict, order_index: int, stats: ImportStats
):
    common = _lesson_common(lesson)
    existing = _find_lesson(module, "checkbox", lesson["title"])
    if existing:
        for key, value in common.items():
            setattr(existing, key, value)
        existing.question_text = lesson["question_text"]
        existing.points = lesson.get("points", 4)
        existing.is_active = True
        existing.order_index = order_index
        existing.save()
        existing.answers.all().delete()
        question = existing
        stats.updated += 1
    else:
        question = LessonCheckBoxQuestion.objects.create(
            module=module,
            title=lesson["title"],
            question_text=lesson["question_text"],
            points=lesson.get("points", 4),
            order_index=order_index,
            is_active=True,
            **common,
        )
        stats.created += 1

    for i, (text, is_correct) in enumerate(lesson.get("answers", []), start=1):
        CheckBoxAnswerOption.objects.create(
            question=question,
            text=text,
            is_correct=is_correct,
            order_index=i,
        )
    return question


def _upsert_short_answer(
    *, module: Module, lesson: dict, order_index: int, stats: ImportStats
):
    common = _lesson_common(lesson)
    existing = _find_lesson(module, "short_answer", lesson["title"])
    fields = {
        "question_text": lesson["question_text"],
        "correct_answer": lesson["correct_answer"],
        "answer_normalize": lesson.get(
            "answer_normalize",
            LessonShortAnswer.AnswerNormalize.STRIP_CASEFOLD,
        ),
        "points": lesson.get("points", 3),
        "is_active": True,
        "order_index": order_index,
        **common,
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.save()
        stats.updated += 1
        return existing

    question = LessonShortAnswer.objects.create(
        module=module,
        title=lesson["title"],
        **fields,
    )
    stats.created += 1
    return question


def _upsert_theory(
    *, module: Module, lesson: dict, order_index: int, stats: ImportStats
):
    common = _lesson_common(lesson)
    existing = _find_lesson(module, "theory", lesson["title"])
    fields = {
        "content": lesson["content"],
        "is_active": True,
        "order_index": order_index,
        **common,
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.save()
        stats.updated += 1
        return existing

    obj = LessonTheory.objects.create(
        module=module,
        title=lesson["title"],
        **fields,
    )
    stats.created += 1
    return obj


def _upsert_coding(
    *,
    module: Module,
    course: Course,
    lesson: dict,
    order_index: int,
    stats: ImportStats,
):
    common = _lesson_common(lesson)
    existing = _find_lesson(module, "coding", lesson["title"])
    fields = {
        "description": lesson["description"],
        "instructions": lesson["instructions"],
        "initial_code": lesson["initial_code"],
        "solution_template": lesson.get("solution_template", ""),
        "difficulty": lesson.get("difficulty", "beginner"),
        "points": lesson.get("points", 10),
        "time_limit_ms": lesson.get("time_limit_ms", 2000),
        "memory_limit_mb": lesson.get("memory_limit_mb", 256),
        "is_active": True,
        "order_index": order_index,
        **common,
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.course = course
        existing.save()
        existing.test_cases.all().delete()
        challenge = existing
        stats.updated += 1
    else:
        challenge = CodingChallenge.objects.create(
            course=course,
            module=module,
            title=lesson["title"],
            **fields,
        )
        stats.created += 1

    for i, tc in enumerate(lesson.get("test_cases", []), start=1):
        TestCase.objects.create(
            challenge=challenge,
            input_data=tc["input_data"],
            expected_output=tc["expected_output"],
            is_hidden=tc.get("is_hidden", False),
            order_index=i,
        )
    return challenge


def _lesson_images(lesson: dict) -> list[str]:
    names: list[str] = []
    single = lesson.get("image")
    if single:
        names.append(str(single))
    for item in lesson.get("images") or []:
        names.append(str(item))
    return names


def _attach_images(
    *, lesson_obj, kind: str, root: Path, images_dir: str, names: list[str]
):
    if not names:
        return

    lesson_obj.attachments.all().delete()
    folder = root / images_dir.rstrip("/")

    for name in names:
        rel = Path(name)
        src = folder / rel.name if not rel.is_absolute() else folder / rel
        if not src.is_file():
            raise ContentPackError(f"Картинка не найдена: {name}")

        attachment = LessonAttachment(
            original_name=src.name,
            content_type=_guess_content_type(src.suffix),
            size=src.stat().st_size,
        )
        bind_parent(attachment=attachment, kind=kind, lesson=lesson_obj)
        attachment.file.save(
            src.name,
            ContentFile(src.read_bytes()),
            save=True,
        )


def _guess_content_type(suffix: str) -> str:
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    return mapping.get(suffix.lower(), "application/octet-stream")


def _extract_archive(archive: Path) -> Path:
    archive = Path(archive)
    if not archive.is_file():
        raise ContentPackError(f"Файл не найден: {archive}")
    tmpdir = Path(tempfile.mkdtemp(prefix="content-pack-"))
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(tmpdir)
        return tmpdir
    except zipfile.BadZipFile as exc:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise ContentPackError(
            "Файл не является корректным ZIP-архивом"
        ) from exc
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


def _lesson_preview_row(lesson: dict, index: int) -> dict:
    kind = str(lesson.get("type", ""))
    row = {
        "index": index,
        "type": kind,
        "title": lesson.get("title", ""),
    }
    images = _lesson_images(lesson)
    if images:
        row["images"] = images
    return row


def inspect_content_pack(*, archive: Path) -> PackPreview:
    """Прочитать manifest и список уроков из ZIP без записи в БД."""
    tmpdir = _extract_archive(archive)
    try:
        manifest = load_manifest(tmpdir / "manifest.json")
        lessons, _images_dir = load_questions(tmpdir / "questions.json")
        for lesson in lessons:
            validate_lesson_payload(str(lesson["type"]), lesson)
        return PackPreview(
            pack_id=manifest["pack_id"],
            course_slug=manifest["course_slug"],
            module_title=manifest["module_title"],
            lesson_count=len(lessons),
            lessons=[
                _lesson_preview_row(lesson, index)
                for index, lesson in enumerate(lessons, start=1)
            ],
            manifest=manifest,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def import_result_to_dict(result: ImportResult) -> dict:
    stats = result.stats
    message = (
        f"Проверка: будет создано {stats.created}, "
        f"обновлено {stats.updated}."
        if result.dry_run
        else (
            f"Импорт завершён: создано {stats.created}, "
            f"обновлено {stats.updated}."
        )
    )
    if stats.skipped:
        message += f" Пропущено: {stats.skipped}."
    return {
        "pack_id": result.pack_id,
        "course_slug": result.course_slug,
        "module_title": result.module_title,
        "dry_run": result.dry_run,
        "module_id": result.module_id,
        "created": stats.created,
        "updated": stats.updated,
        "skipped": stats.skipped,
        "errors": stats.errors,
        "message": message,
    }


def preview_result_to_dict(
    preview: PackPreview, *, dry_run: ImportResult
) -> dict:
    data = import_result_to_dict(dry_run)
    data["manifest"] = preview.manifest
    data["lessons"] = preview.lessons
    data["lesson_count"] = preview.lesson_count
    return data


def import_content_pack(
    *, archive: Path, dry_run: bool = False
) -> ImportResult:
    archive = Path(archive)
    if not archive.is_file():
        raise ContentPackError(f"Файл не найден: {archive}")

    tmpdir = _extract_archive(archive)
    try:
        manifest = load_manifest(tmpdir / "manifest.json")
        lessons, images_dir = load_questions(tmpdir / "questions.json")

        for lesson in lessons:
            validate_lesson_payload(str(lesson["type"]), lesson)

        course = Course.objects.filter(slug=manifest["course_slug"]).first()
        if not course:
            raise ContentPackError(
                f"Курс «{manifest['course_slug']}» не найден. "
                "Сначала запустите ensure_ege_course или seed_data."
            )

        stats = ImportStats()
        if dry_run:
            module = resolve_module(
                course=course, manifest=manifest, dry_run=True
            )
            for lesson in lessons:
                if _find_lesson(module, lesson["type"], lesson["title"]):
                    stats.updated += 1
                else:
                    stats.created += 1
            return ImportResult(
                pack_id=manifest["pack_id"],
                course_slug=manifest["course_slug"],
                module_title=manifest["module_title"],
                dry_run=True,
                stats=stats,
                module_id=module.id if module else None,
            )

        with transaction.atomic():
            module = resolve_module(course=course, manifest=manifest)
            start_order = manifest.get("start_order_index")
            if start_order is None:
                start_order = next_order_in_container(
                    CONTAINER_MODULE, module.id
                )

            for offset, lesson in enumerate(lessons):
                kind = lesson["type"]
                order_index = int(start_order) + offset
                if kind == "radio":
                    obj = _upsert_radio(
                        module=module,
                        lesson=lesson,
                        order_index=order_index,
                        stats=stats,
                    )
                elif kind == "checkbox":
                    obj = _upsert_checkbox(
                        module=module,
                        lesson=lesson,
                        order_index=order_index,
                        stats=stats,
                    )
                elif kind == "short_answer":
                    obj = _upsert_short_answer(
                        module=module,
                        lesson=lesson,
                        order_index=order_index,
                        stats=stats,
                    )
                elif kind == "theory":
                    obj = _upsert_theory(
                        module=module,
                        lesson=lesson,
                        order_index=order_index,
                        stats=stats,
                    )
                elif kind == "coding":
                    obj = _upsert_coding(
                        module=module,
                        course=course,
                        lesson=lesson,
                        order_index=order_index,
                        stats=stats,
                    )
                else:
                    stats.skipped += 1
                    continue

                image_names = _lesson_images(lesson)
                if image_names:
                    _attach_images(
                        lesson_obj=obj,
                        kind=kind,
                        root=tmpdir,
                        images_dir=images_dir,
                        names=image_names,
                    )

        return ImportResult(
            pack_id=manifest["pack_id"],
            course_slug=manifest["course_slug"],
            module_title=manifest["module_title"],
            dry_run=False,
            stats=stats,
            module_id=module.id,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
