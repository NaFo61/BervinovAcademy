"""Реестр уроков и доступ к курсу для редактора контента."""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from content.container_lessons import iter_module_lessons
from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonShortAnswer,
    LessonTheory,
    Module,
    RadioAnswerOption,
    TestCase,
)

LESSON_KINDS = ("theory", "radio", "checkbox", "short_answer", "coding")

_MODELS = {
    "theory": LessonTheory,
    "radio": LessonRadioQuestion,
    "checkbox": LessonCheckBoxQuestion,
    "short_answer": LessonShortAnswer,
    "coding": CodingChallenge,
}


def lesson_model(kind: str):
    model = _MODELS.get(kind)
    if not model:
        raise ValueError(f"Unknown lesson kind: {kind}")
    return model


def get_lesson(kind: str, public_id):
    model = lesson_model(kind)
    return get_object_or_404(model, public_id=public_id)


def course_for_lesson(instance) -> Course | None:
    if getattr(instance, "module_id", None) and instance.module_id:
        return instance.module.course
    if getattr(instance, "exam_id", None) and instance.exam_id:
        return instance.exam.course
    if getattr(instance, "course_id", None) and instance.course_id:
        return instance.course
    return None


def user_can_edit_course(user, course: Course) -> bool:
    """Admin — все курсы; ментор — только курсы, где он назначен ментором."""
    if not user or not user.is_authenticated:
        return False
    if (
        getattr(user, "is_admin", False)
        or getattr(user, "role", None) == "admin"
    ):
        return True
    if getattr(user, "role", None) != "mentor":
        return False
    return course.mentor_id == user.id


def build_course_editor_outline(course: Course) -> dict:
    modules = []
    for module in course.modules.filter(is_active=True).order_by(
        "order_index"
    ):
        lessons = []
        for kind, obj in iter_module_lessons(module, active_only=False):
            lessons.append(
                {
                    "kind": kind,
                    "public_id": str(obj.public_id),
                    "title": obj.title,
                    "order_index": obj.order_index,
                    "is_active": obj.is_active,
                }
            )
        modules.append(
            {
                "public_id": str(module.public_id),
                "title": module.title,
                "description": module.description,
                "order_index": module.order_index,
                "is_active": module.is_active,
                "lessons": lessons,
            }
        )

    exams = []
    for exam in course.exams.filter(is_active=True).order_by("order_index"):
        exams.append(
            {
                "public_id": str(exam.public_id),
                "title": exam.title,
                "order_index": exam.order_index,
            }
        )

    return {
        "public_id": str(course.public_id),
        "title": course.title,
        "slug": course.slug,
        "modules": modules,
        "exams": exams,
    }


def create_lesson_in_module(
    module: Module, kind: str, *, title: str
) -> object:
    lesson_model(kind)
    common = {"module": module, "title": title, "is_active": True}
    if kind == "theory":
        return LessonTheory.objects.create(
            **common,
            content="<p>Новый теоретический урок</p>",
        )
    if kind == "radio":
        q = LessonRadioQuestion.objects.create(
            **common,
            question_text="Текст вопроса",
            points=1,
        )
        for i, (text, ok) in enumerate(
            [("Вариант A", False), ("Вариант B", True)], start=1
        ):
            RadioAnswerOption.objects.create(
                question=q, text=text, is_correct=ok, order_index=i
            )
        return q
    if kind == "checkbox":
        q = LessonCheckBoxQuestion.objects.create(
            **common,
            question_text="Текст вопроса",
            points=1,
        )
        for i, (text, ok) in enumerate(
            [("Вариант 1", True), ("Вариант 2", False)], start=1
        ):
            CheckBoxAnswerOption.objects.create(
                question=q, text=text, is_correct=ok, order_index=i
            )
        return q
    if kind == "short_answer":
        return LessonShortAnswer.objects.create(
            **common,
            question_text="Введите ответ",
            correct_answer="",
            answer_normalize=LessonShortAnswer.AnswerNormalize.STRIP_CASEFOLD,
            points=1,
        )
    if kind == "coding":
        ch = CodingChallenge.objects.create(
            module=module,
            course=module.course,
            title=title,
            description="Описание задачи",
            instructions="Напишите решение.",
            initial_code="def solve():\n    pass\n",
            solution_template="def solve():\n    pass\n",
            is_active=True,
        )
        TestCase.objects.create(
            challenge=ch,
            input_data="",
            expected_output="",
            is_hidden=False,
        )
        return ch
    raise ValueError(kind)
