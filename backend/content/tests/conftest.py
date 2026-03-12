import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import (
    Technology, Course, Module, LessonTheory,
    LessonRadioQuestion, AnswerOption,
    LessonCheckBoxQuestion, CheckBoxAnswerOption
)


@pytest.fixture
def technology(db):
    return Technology.objects.create(name="Python")


@pytest.fixture
def course(db, technology):
    course = Course.objects.create(
        title="Test Course",
        description="Test Description",
        slug="test-course",
        is_active=True
    )
    course.technology.add(technology)
    return course


@pytest.fixture
def module(db, course):
    return Module.objects.create(
        course=course,
        title="Test Module",
        description="Module Description",
        order_index=1,
        is_active=True
    )


@pytest.fixture
def theory_lesson(db, module):
    return LessonTheory.objects.create(
        module=module,
        title="Test Theory Lesson",
        content="This is test content for theory lesson",
        order_index=1,
        is_active=True
    )


@pytest.fixture
def radio_question(db, module):
    return LessonRadioQuestion.objects.create(
        module=module,
        title="Test Radio Question",
        question_text="What is 2+2?",
        explanation="Basic math",
        order_index=1,
        points=5,
        is_active=True
    )


@pytest.fixture
def radio_answers(db, radio_question):
    answers = []
    for i, (text, is_correct) in enumerate([
        ("3", False),
        ("4", True),
        ("5", False),
        ("22", False)
    ], start=1):
        answer = AnswerOption.objects.create(
            question=radio_question,
            text=text,
            is_correct=is_correct,
            order_index=i
        )
        answers.append(answer)
    return answers


@pytest.fixture
def checkbox_question(db, module):
    return LessonCheckBoxQuestion.objects.create(
        module=module,
        title="Test Checkbox Question",
        question_text="Select even numbers:",
        explanation="Numbers divisible by 2",
        order_index=2,
        points=10,
        is_active=True
    )


@pytest.fixture
def checkbox_answers(db, checkbox_question):
    answers = []
    for i, (text, is_correct) in enumerate([
        ("1", False),
        ("2", True),
        ("3", False),
        ("4", True),
        ("5", False)
    ], start=1):
        answer = CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text=text,
            is_correct=is_correct,
            order_index=i
        )
        answers.append(answer)
    return answers


@pytest.fixture
def image_file():
    return SimpleUploadedFile(
        "test_image.jpg",
        b"file_content",
        content_type="image/jpeg"
    )


@pytest.fixture
def inactive_course(db, technology):
    course = Course.objects.create(
        title="Inactive Course",
        description="This course is inactive",
        slug="inactive-course",
        is_active=False
    )
    course.technology.add(technology)
    return course