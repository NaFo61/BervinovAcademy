"""Разборы №1 ЕГЭ: блоки теории и ответы из academy-blocks.json."""

from django.core.management import call_command
from fixture.ege_n1 import (
    EGE_N1_ANSWERS,
    apply_ege_n1_blocks,
    ensure_ege_n1_in_module,
    load_ege_n1_theory_lessons,
)
import pytest

from content.models import (
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
)


def test_pack_titles_and_answers_match_json():
    packs = load_ege_n1_theory_lessons()
    assert [row["title"] for row in packs] == list(EGE_N1_ANSWERS)
    for pack in packs:
        expected = EGE_N1_ANSWERS[pack["title"]]
        callout = next(
            item for item in pack["blocks"] if item["type"] == "callout"
        )
        assert expected in callout["html"]
        assert len([b for b in pack["blocks"] if b["type"] == "image"]) == 4


@pytest.mark.django_db
def test_apply_skips_missing_images(module):
    pack = load_ege_n1_theory_lessons()[0]
    theory = LessonTheory.objects.create(
        module=module,
        title=pack["title"],
        content="<p></p>",
        order_index=2,
        is_active=True,
    )
    apply_ege_n1_blocks(theory, pack["blocks"], pack["assets_dir"])
    theory.refresh_from_db()

    types = [block["type"] for block in theory.blocks]
    assert types[0] == "heading"
    assert "image" not in types
    assert types[-1] == "callout"
    assert theory.attachments.count() == 0
    assert EGE_N1_ANSWERS[pack["title"]] in theory.content


@pytest.mark.django_db
def test_apply_attaches_svg_when_file_present(module, tmp_path):
    blocks = [
        {"type": "heading", "text": "Шаг"},
        {
            "type": "image",
            "file": "img/demo.svg",
            "caption": "Схема",
        },
        {"type": "callout", "html": "<p>Ответ <b>26</b>.</p>"},
    ]
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "demo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        encoding="utf-8",
    )
    theory = LessonTheory.objects.create(
        module=module,
        title="Простое: какие номера у B и F",
        content="<p></p>",
        order_index=2,
        is_active=True,
    )
    apply_ege_n1_blocks(theory, blocks, tmp_path)
    theory.refresh_from_db()
    assert theory.attachments.count() == 1
    image = next(b for b in theory.blocks if b["type"] == "image")
    assert image["caption"] == "Схема"
    assert image["attachment_id"]


@pytest.mark.django_db
def test_ensure_keeps_quiz_answers_and_is_idempotent(module):
    intro = LessonTheory.objects.create(
        module=module,
        title="Таблица дорог и матрица смежности",
        content="<p>Вводная</p>",
        order_index=1,
        is_active=True,
    )
    radio = LessonRadioQuestion.objects.create(
        module=module,
        title="Сколько рёбер у K4",
        question_text="Полный неориентированный граф на 4 вершинах.",
        order_index=2,
        is_active=True,
        points=3,
    )
    RadioAnswerOption.objects.create(
        question=radio,
        text="6",
        is_correct=True,
        order_index=1,
    )

    first = ensure_ege_n1_in_module(module)
    second = ensure_ege_n1_in_module(module)

    assert len(first) == 6
    assert {row.pk for row in first} == {row.pk for row in second}
    assert (
        LessonTheory.objects.filter(module=module, is_active=True).count() == 7
    )

    radio.refresh_from_db()
    intro.refresh_from_db()
    assert radio.question_text == (
        "Полный неориентированный граф на 4 вершинах."
    )
    assert radio.answers.get().text == "6"
    assert radio.answers.get().is_correct is True

    assert intro.order_index == 1
    assert [row.order_index for row in second] == list(range(2, 8))
    assert radio.order_index == 8


@pytest.mark.django_db
def test_seed_graphs_module_has_n1_theory():
    call_command("seed_data", "--clear")
    from content.models import Course

    course = Course.objects.get(slug="ege-informatika")
    module = course.modules.get(title="1-й урок ЕГЭ: Графы")
    theories = list(
        module.lessons_theories.filter(is_active=True).order_by("order_index")
    )
    n1 = [row for row in theories if row.title in EGE_N1_ANSWERS]
    assert len(n1) == 6
    for lesson in n1:
        assert lesson.attachments.count() == 0
        assert EGE_N1_ANSWERS[lesson.title] in lesson.content
        assert any(block["type"] == "callout" for block in lesson.blocks)
        assert not any(block["type"] == "image" for block in lesson.blocks)

    radio = module.lessons_radio_questions.get(title="Сколько рёбер у K4")
    correct = radio.answers.filter(is_correct=True)
    assert correct.count() == 1
    assert correct.get().text == "6"
