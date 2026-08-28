"""Импорт content-pack ZIP в модуль курса."""

import json
from pathlib import Path
import zipfile

from django.core.management import call_command
from django.core.management.base import CommandError
from fixture.content_pack import import_content_pack
import pytest

from content.models import (
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonShortAnswer,
    Module,
    RadioAnswerOption,
)


def _sample_questions():
    return {
        "meta": {"images_dir": "images/"},
        "lessons": [
            {
                "type": "radio",
                "title": "Pack radio 1",
                "question_text": "Pick one",
                "points": 3,
                "answers": [
                    ["wrong", False],
                    ["right", True],
                ],
            },
            {
                "type": "checkbox",
                "title": "Pack checkbox 1",
                "question_text": "Pick many",
                "points": 4,
                "answers": [
                    ["a", True],
                    ["b", False],
                ],
            },
            {
                "type": "short_answer",
                "title": "Pack short 1",
                "question_text": "Answer?",
                "correct_answer": "42",
                "points": 3,
            },
        ],
    }


def _build_zip(
    tmp_path: Path,
    *,
    manifest: dict,
    questions: dict,
    image: bytes | None = None,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    if image is not None:
        questions = json.loads(json.dumps(questions))
        questions["lessons"][0]["images"] = ["chart.png"]

    archive = tmp_path / "pack.zip"
    manifest_bytes = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
    questions_bytes = json.dumps(questions, ensure_ascii=False).encode("utf-8")

    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("questions.json", questions_bytes)
        if image is not None:
            zf.writestr("images/chart.png", image)

    return archive


@pytest.fixture
def ege_course(db):
    course = Course.objects.create(
        title="ЕГЭ-информатика",
        slug="ege-informatika",
        description="test",
        is_active=True,
    )
    module = Module.objects.create(
        course=course,
        title="1-й урок ЕГЭ: Графы",
        description="graphs",
        order_index=1,
        is_active=True,
    )
    return course, module


@pytest.mark.django_db
def test_import_content_pack_happy_path(tmp_path, ege_course):
    course, module = ege_course
    manifest = {
        "pack_id": "ege-n1-practice",
        "course_slug": course.slug,
        "module_title": module.title,
    }
    archive = _build_zip(
        tmp_path, manifest=manifest, questions=_sample_questions()
    )

    result = import_content_pack(archive=archive, dry_run=False)

    assert result.stats.created == 3
    assert result.stats.updated == 0
    assert LessonRadioQuestion.objects.filter(module=module).count() == 1
    assert LessonCheckBoxQuestion.objects.filter(module=module).count() == 1
    assert LessonShortAnswer.objects.filter(module=module).count() == 1

    radio = LessonRadioQuestion.objects.get(
        module=module, title="Pack radio 1"
    )
    assert radio.answers.filter(is_correct=True).count() == 1


@pytest.mark.django_db
def test_import_content_pack_idempotent(tmp_path, ege_course):
    course, module = ege_course
    manifest = {
        "pack_id": "ege-n1-practice",
        "course_slug": course.slug,
        "module_title": module.title,
    }
    questions = _sample_questions()
    archive = _build_zip(tmp_path, manifest=manifest, questions=questions)

    import_content_pack(archive=archive, dry_run=False)
    questions["lessons"][0]["answers"] = [["new-right", True], ["old", False]]
    archive2 = _build_zip(
        tmp_path / "second", manifest=manifest, questions=questions
    )

    result = import_content_pack(archive=archive2, dry_run=False)

    assert result.stats.created == 0
    assert result.stats.updated == 3
    assert LessonRadioQuestion.objects.filter(module=module).count() == 1
    radio = LessonRadioQuestion.objects.get(
        module=module, title="Pack radio 1"
    )
    assert (
        RadioAnswerOption.objects.filter(question=radio, is_correct=True)
        .get()
        .text
        == "new-right"
    )


@pytest.mark.django_db
def test_import_content_pack_dry_run(tmp_path, ege_course):
    course, module = ege_course
    manifest = {
        "pack_id": "ege-n1-practice",
        "course_slug": course.slug,
        "module_title": module.title,
    }
    archive = _build_zip(
        tmp_path, manifest=manifest, questions=_sample_questions()
    )

    result = import_content_pack(archive=archive, dry_run=True)

    assert result.dry_run is True
    assert result.stats.created == 3
    assert LessonRadioQuestion.objects.filter(module=module).count() == 0


@pytest.mark.django_db
def test_import_content_pack_management_command(tmp_path, ege_course):
    course, _module = ege_course
    module_title = "2-й урок ЕГЭ: Кодирование и поиск"
    Module.objects.create(
        course=course,
        title=module_title,
        description="codes",
        order_index=2,
        is_active=True,
    )
    manifest = {
        "pack_id": "ege-n4-practice",
        "course_slug": course.slug,
        "module_title": module_title,
    }
    archive = _build_zip(
        tmp_path, manifest=manifest, questions=_sample_questions()
    )

    call_command("import_content_pack", str(archive))

    target = Module.objects.get(course=course, title=module_title)
    assert LessonRadioQuestion.objects.filter(module=target).count() == 1


@pytest.mark.django_db
def test_import_missing_module_raises(tmp_path, ege_course):
    course, _module = ege_course
    manifest = {
        "pack_id": "missing-module",
        "course_slug": course.slug,
        "module_title": "Несуществующий модуль",
    }
    archive = _build_zip(
        tmp_path, manifest=manifest, questions=_sample_questions()
    )

    with pytest.raises(CommandError, match="не найден"):
        call_command("import_content_pack", str(archive))
