import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.text import slugify
from unidecode import unidecode
from decimal import Decimal

from your_app.models import (
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
        title="Python Basics",
        description="Learn Python basics",
        is_active=True
    )
    course.technology.add(technology)
    return course


@pytest.fixture
def module(db, course):
    return Module.objects.create(
        course=course,
        title="Module 1",
        description="First module",
        order_index=1
    )


@pytest.fixture
def radio_question(db, module):
    return LessonRadioQuestion.objects.create(
        module=module,
        title="Test Question",
        question_text="What is Python?",
        order_index=1,
        points=5
    )


@pytest.fixture
def checkbox_question(db, module):
    return LessonCheckBoxQuestion.objects.create(
        module=module,
        title="Select all that apply",
        question_text="Which are Python data types?",
        order_index=2,
        points=10,
        min_correct_answers=1,
        max_correct_answers=3
    )


class TestTechnologyModel:
    def test_create_technology(self, technology):
        assert technology.name == "Python"
        assert str(technology) == "Python"

    def test_technology_unique_name(self, db):
        Technology.objects.create(name="Unique")
        with pytest.raises(IntegrityError):
            Technology.objects.create(name="Unique")

    def test_technology_ordering(self, db):
        Technology.objects.create(name="Zebra")
        Technology.objects.create(name="Apple")
        technologies = Technology.objects.all()
        assert technologies[0].name == "Apple"
        assert technologies[1].name == "Python"
        assert technologies[2].name == "Zebra"


class TestCourseModel:
    def test_create_course(self, course, technology):
        """Тест создания курса"""
        assert course.title == "Python Basics"
        assert course.slug == slugify(unidecode(course.title))
        assert course.is_active is True
        assert course.technology.count() == 1
        assert course.technology.first() == technology

    def test_course_slug_generation(self, db):
        course1 = Course.objects.create(
            title="Advanced Python Programming"
        )
        expected_slug = slugify(unidecode("advanced-python-programming"))
        assert course1.slug == expected_slug
        course2 = Course.objects.create(
            title="Продвинутый Python"
        )
        assert course2.slug == slugify(unidecode("Продвинутый Python"))

    def test_course_slug_unique(self, db):
        Course.objects.create(title="Same Title")
        course2 = Course(title="Same Title")
        with pytest.raises(IntegrityError):
            course2.save()

    def test_course_str_method(self, course):
        assert str(course) == "Python Basics"

    def test_course_ordering(self, db):
        from datetime import timedelta
        from django.utils import timezone
        course1 = Course.objects.create(title="First")
        course1.created_at = timezone.now() - timedelta(days=2)
        course1.save()
        course2 = Course.objects.create(title="Second")
        course2.created_at = timezone.now() - timedelta(days=1)
        course2.save()
        course3 = Course.objects.create(title="Third")
        courses = Course.objects.all()
        assert courses[0].title == "Third"
        assert courses[1].title == "Second"
        assert courses[2].title == "First"


class TestModuleModel:
    def test_create_module(self, module, course):
        assert module.course == course
        assert module.title == "Module 1"
        assert module.order_index == 1
        assert module.is_active is True

    def test_module_str_method(self, module):
        assert str(module) == "Python Basics - Module 1"

    def test_module_unique_order_in_course(self, module):
        with pytest.raises(IntegrityError):
            Module.objects.create(
                course=module.course,
                title="Duplicate Module",
                order_index=1  # Тот же индекс
            )

    def test_module_ordering(self, module, course):
        module2 = Module.objects.create(
            course=course,
            title="Module 2",
            order_index=2
        )
        module3 = Module.objects.create(
            course=course,
            title="Module 0",
            order_index=0
        )

    def test_module_auto_order_index(self, course):
        module1 = Module.objects.create(course=course, title="First")
        module2 = Module.objects.create(course=course, title="Second")


class TestLessonRadioQuestionModel:
    def test_create_radio_question(self, radio_question, module):
        assert radio_question.module == module
        assert radio_question.title == "Test Question"
        assert radio_question.points == 5
        assert radio_question.is_active is True

    def test_radio_question_str_method(self, radio_question):
        assert str(radio_question) == "Module 1 - Test Question"

    def test_radio_question_unique_order_in_module(self, radio_question):
        with pytest.raises(IntegrityError):
            LessonRadioQuestion.objects.create(
                module=radio_question.module,
                title="Duplicate",
                question_text="Text",
                order_index=1
            )

    def test_get_correct_answer_none(self, radio_question):
        assert radio_question.get_correct_answer() is None

    def test_get_correct_answer_with_answer(self, radio_question):
        answer = AnswerOption.objects.create(
            question=radio_question,
            text="Programming language",
            is_correct=True,
            order_index=1
        )
        correct = radio_question.get_correct_answer()
        assert correct == answer
        assert correct.text == "Programming language"


class TestAnswerOptionModel:
    def test_create_answer(self, radio_question):
        answer = AnswerOption.objects.create(
            question=radio_question,
            text="Python is a programming language",
            is_correct=False,
            order_index=1
        )
        assert answer.question == radio_question
        assert answer.text == "Python is a programming language"
        assert answer.is_correct is False
        assert answer.order_index == 1

    def test_answer_str_method(self, radio_question):
        answer = AnswerOption.objects.create(
            question=radio_question,
            text="Programming language",
            order_index=1
        )
        assert "Programming language" in str(answer)
    
    def test_unique_correct_answer_constraint(self, radio_question):
        AnswerOption.objects.create(
            question=radio_question,
            text="Option 1",
            is_correct=True,
            order_index=1
        )

        with pytest.raises(IntegrityError):
            AnswerOption.objects.create(
                question=radio_question,
                text="Option 2",
                is_correct=True,
                order_index=2
            )

    def test_save_method_ensures_single_correct(self, radio_question):
        answer1 = AnswerOption.objects.create(
            question=radio_question,
            text="Correct 1",
            is_correct=True,
            order_index=1
        )
        answer2 = AnswerOption.objects.create(
            question=radio_question,
            text="Correct 2",
            is_correct=True,
            order_index=2
        )
        answer1.refresh_from_db()
        answer2.refresh_from_db()
        assert answer1.is_correct is False
        assert answer2.is_correct is True

        correct_count = AnswerOption.objects.filter(
            question=radio_question, 
            is_correct=True
        ).count()
        assert correct_count == 1

    def test_unique_order_in_question(self, radio_question):
        AnswerOption.objects.create(
            question=radio_question,
            text="Answer 1",
            order_index=1
        )
        with pytest.raises(IntegrityError):
            AnswerOption.objects.create(
                question=radio_question,
                text="Answer 2",
                order_index=1
            )


class TestLessonCheckBoxQuestionModel:
    def test_create_checkbox_question(self, checkbox_question, module):
        assert checkbox_question.module == module
        assert checkbox_question.title == "Select all that apply"
        assert checkbox_question.min_correct_answers == 1
        assert checkbox_question.max_correct_answers == 3
        assert checkbox_question.partial_points is False

    def test_checkbox_question_str_method(self, checkbox_question):
        assert str(checkbox_question) == "Module 1 - Select all that apply"

    def test_validate_answers_count(self, checkbox_question):
        for i in range(2):
            CheckBoxAnswerOption.objects.create(
                question=checkbox_question,
                text=f"Correct {i}",
                is_correct=True,
                order_index=i+1
            )
        assert checkbox_question.validate_answers_count() is True
        assert checkbox_question.get_correct_answers_count() == 2

    def test_validate_answers_count_out_of_range(self, checkbox_question):
        for i in range(4):
            CheckBoxAnswerOption.objects.create(
                question=checkbox_question,
                text=f"Correct {i}",
                is_correct=True,
                order_index=i+1
            )

        assert checkbox_question.validate_answers_count() is False
        assert checkbox_question.get_correct_answers_count() == 4

    def test_get_correct_answers(self, checkbox_question):
        answers = []
        for i in range(3):
            answers.append(CheckBoxAnswerOption.objects.create(
                question=checkbox_question,
                text=f"Answer {i}",
                is_correct=True,
                order_index=i+1
            ))

        CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Wrong",
            is_correct=False,
            order_index=4
        )
        correct = checkbox_question.get_correct_answers()
        assert correct.count() == 3
        assert all(a.is_correct for a in correct)

    def test_clean_method_validation(self, checkbox_question):
        checkbox_question.min_correct_answers = 5
        checkbox_question.max_correct_answers = 3
        with pytest.raises(ValidationError):
            checkbox_question.clean()


class TestCheckBoxAnswerOptionModel:
    def test_create_checkbox_answer(self, checkbox_question):
        answer = CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Integer",
            is_correct=True,
            order_index=1
        )
        assert answer.question == checkbox_question
        assert answer.text == "Integer"
        assert answer.is_correct is True

    def test_multiple_correct_answers_allowed(self, checkbox_question):
        for i in range(3):
            CheckBoxAnswerOption.objects.create(
                question=checkbox_question,
                text=f"Correct {i}",
                is_correct=True,
                order_index=i+1
            )
        correct_count = CheckBoxAnswerOption.objects.filter(
            question=checkbox_question,
            is_correct=True
        ).count()
        assert correct_count == 3

    def test_save_method_warning_on_invalid_count(self, checkbox_question):
        checkbox_question.max_correct_answers = 2
        import warnings
        with pytest.warns(UserWarning):
            for i in range(3):
                CheckBoxAnswerOption.objects.create(
                    question=checkbox_question,
                    text=f"Correct {i}",
                    is_correct=True,
                    order_index=i+1
                )
    
    def test_unique_order_in_question(self, checkbox_question):
        CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Answer 1",
            order_index=1
        )
        with pytest.raises(IntegrityError):
            CheckBoxAnswerOption.objects.create(
                question=checkbox_question,
                text="Answer 2",
                order_index=1
            )


class TestLessonTheoryModel:
    def test_create_theory_lesson(self, module):
        theory = LessonTheory.objects.create(
            module=module,
            title="Introduction",
            content="This is the introduction content...",
            order_index=1
        )
        assert theory.module == module
        assert theory.title == "Introduction"
        assert theory.content == "This is the introduction content..."
        assert theory.order_index == 1
        assert theory.is_active is True

    def test_theory_str_method(self, module):
        theory = LessonTheory.objects.create(
            module=module,
            title="Variables",
            content="Content about variables",
            order_index=1
        )
        assert str(theory) == "Module 1 - Variables"

    def test_unique_order_in_module(self, module):
        LessonTheory.objects.create(
            module=module,
            title="First",
            content="Content",
            order_index=1
        )
        with pytest.raises(IntegrityError):
            LessonTheory.objects.create(
                module=module,
                title="Second",
                content="Content",
                order_index=1
            )


class TestCourseStructureIntegration:
    def test_full_course_hierarchy(self, course, technology):
        module1 = Module.objects.create(
            course=course,
            title="Module 1",
            order_index=1
        )
        module2 = Module.objects.create(
            course=course,
            title="Module 2",
            order_index=2
        )

        theory = LessonTheory.objects.create(
            module=module1,
            title="Theory 1",
            content="Theory content",
            order_index=1
        )

        radio_q = LessonRadioQuestion.objects.create(
            module=module1,
            title="Radio Q",
            question_text="Question?",
            order_index=2,
            points=5
        )

        checkbox_q = LessonCheckBoxQuestion.objects.create(
            module=module2,
            title="Checkbox Q",
            question_text="Check question?",
            order_index=1,
            points=10
        )

        AnswerOption.objects.create(
            question=radio_q,
            text="Correct answer",
            is_correct=True,
            order_index=1
        )

        for i in range(3):
            CheckBoxAnswerOption.objects.create(
                question=checkbox_q,
                text=f"Option {i}",
                is_correct=True if i == 0 else False,
                order_index=i+1
            )

        assert course.modules.count() == 2
        assert module1.lessons_theories.count() == 1
        assert module1.lessons_radio_questions.count() == 1
        assert module2.lessons_checkbox_questions.count() == 1
        assert radio_q.get_correct_answer().text == "Correct answer"
        assert checkbox_q.get_correct_answers_count() == 1

    def test_cascade_delete_protection(self, course, module):
        course_id = course.id
        module_id = module.id
        course.delete()
        assert Module.objects.filter(id=module_id).count() == 0


class TestModelManagers:
    def test_active_courses_only(self, course):
        Course.objects.create(
            title="Inactive Course",
            description="Should not appear",
            is_active=False
        )

        active_courses = Course.objects.filter(is_active=True)
        assert active_courses.count() == 1
        assert active_courses.first().title == "Python Basics"

    def test_active_modules_only(self, module):
        Module.objects.create(
            course=module.course,
            title="Inactive Module",
            is_active=False,
            order_index=2
        )

        active_modules = Module.objects.filter(is_active=True)
        assert active_modules.count() == 1
        assert active_modules.first().title == "Module 1"

    def test_course_technologies_relation(self, course, technology):
        tech2 = Technology.objects.create(name="Django")
        course.technology.add(tech2)
        assert course.technology.count() == 2
        assert list(course.technology.values_list('name', flat=True)) == ["Django", "Python"]


class TestValidators:
    """Тесты для валидаторов"""
    
    def test_min_value_validator(self, course):
        """Тест MinValueValidator"""
        with pytest.raises(ValidationError) as excinfo:
            module = Module(
                course=course,
                title="Invalid Module",
                order_index=0
            )
            module.full_clean()

    def test_points_positive(self, radio_question):
        radio_question.points = 0

    def test_radio_question_without_answers(self, radio_question):
        assert radio_question.get_correct_answer() is None
