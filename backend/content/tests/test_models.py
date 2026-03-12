import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from content.models import (
    Technology, Course, Module, LessonTheory,
    LessonRadioQuestion, AnswerOption,
    LessonCheckBoxQuestion, CheckBoxAnswerOption
)


class TestTechnologyModel:

    def test_create_technology(self, db):
        tech = Technology.objects.create(name="Django")
        assert tech.name == "Django"
        assert str(tech) == "Django"

    def test_technology_unique_name(self, db):
        Technology.objects.create(name="Python")
        with pytest.raises(IntegrityError):
            Technology.objects.create(name="Python")

    def test_technology_ordering(self, db):
        Technology.objects.create(name="Zebra")
        Technology.objects.create(name="Apple")
        technologies = Technology.objects.all()
        assert technologies[0].name == "Apple"
        assert technologies[1].name == "Zebra"


class TestCourseModel:

    def test_create_course(self, db, technology):
        course = Course.objects.create(
            title="Python Course",
            description="Learn Python",
            slug="python-course"
        )
        course.technology.add(technology)

        assert course.title == "Python Course"
        assert course.slug == "python-course"
        assert course.is_active is True
        assert technology in course.technology.all()
        assert str(course) == "Python Course"

    def test_course_slug_generation(self, db):
        course = Course.objects.create(
            title="Advanced Python Programming",
            description="Deep dive into Python"
        )
        assert course.slug == "advanced-python-programming"

    def test_course_unique_slug(self, db):
        Course.objects.create(
            title="Course 1",
            slug="same-slug"
        )
        with pytest.raises(IntegrityError):
            Course.objects.create(
                title="Course 2",
                slug="same-slug"
            )

    def test_course_ordering(self, db):
        course1 = Course.objects.create(title="Course 1")
        course2 = Course.objects.create(title="Course 2")
        courses = Course.objects.all()
        assert courses[0] == course2
        assert courses[1] == course1

    def test_course_technologies_list(self, db, technology):
        course = Course.objects.create(title="Test Course")
        course.technology.add(technology)
        assert course.technology.count() == 1
        assert course.technology.first().name == "Python"


class TestModuleModel:

    def test_create_module(self, db, course):
        module = Module.objects.create(
            course=course,
            title="Module 1",
            description="First module",
            order_index=1
        )
        assert module.title == "Module 1"
        assert module.order_index == 1
        assert module.course == course
        assert str(module) == f"{course.title} - Module 1"

    def test_module_unique_order_per_course(self, db, course):
        Module.objects.create(
            course=course,
            title="Module 1",
            order_index=1
        )
        with pytest.raises(IntegrityError):
            Module.objects.create(
                course=course,
                title="Module 2",
                order_index=1
            )

    def test_module_ordering(self, db, course):
        module2 = Module.objects.create(
            course=course,
            title="Module 2",
            order_index=2
        )
        module1 = Module.objects.create(
            course=course,
            title="Module 1",
            order_index=1
        )
        modules = Module.objects.all()
        assert modules[0] == module1
        assert modules[1] == module2

    def test_module_delete_reorders(self, db, course):
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
        module3 = Module.objects.create(
            course=course,
            title="Module 3",
            order_index=3
        )

        module2.delete()
        module3.refresh_from_db()
        assert module3.order_index == 2

    def test_cascade_delete_with_course(self, db, course):
        Module.objects.create(
            course=course,
            title="Module 1",
            order_index=1
        )
        course.delete()
        assert Module.objects.count() == 0


class TestLessonTheoryModel:

    def test_create_theory_lesson(self, db, module):
        lesson = LessonTheory.objects.create(
            module=module,
            title="Introduction",
            content="Welcome to the course",
            order_index=1
        )
        assert lesson.title == "Introduction"
        assert lesson.content == "Welcome to the course"
        assert lesson.is_active is True
        assert str(lesson) == f"{module.title} - Introduction"

    def test_lesson_unique_order_per_module(self, db, module):
        LessonTheory.objects.create(
            module=module,
            title="Lesson 1",
            content="Content 1",
            order_index=1
        )
        with pytest.raises(IntegrityError):
            LessonTheory.objects.create(
                module=module,
                title="Lesson 2",
                content="Content 2",
                order_index=1
            )

    def test_lesson_ordering(self, db, module):
        lesson2 = LessonTheory.objects.create(
            module=module,
            title="Lesson 2",
            content="Content 2",
            order_index=2
        )
        lesson1 = LessonTheory.objects.create(
            module=module,
            title="Lesson 1",
            content="Content 1",
            order_index=1
        )
        lessons = LessonTheory.objects.all()
        assert lessons[0] == lesson1
        assert lessons[1] == lesson2

    def test_lesson_delete_reorders(self, db, module):
        lesson1 = LessonTheory.objects.create(
            module=module,
            title="Lesson 1",
            content="Content 1",
            order_index=1
        )
        lesson2 = LessonTheory.objects.create(
            module=module,
            title="Lesson 2",
            content="Content 2",
            order_index=2
        )
        lesson3 = LessonTheory.objects.create(
            module=module,
            title="Lesson 3",
            content="Content 3",
            order_index=3
        )

        lesson2.delete()
        lesson3.refresh_from_db()
        assert lesson3.order_index == 2

    def test_lesson_clean_method(self, db, module):
        LessonTheory.objects.create(
            module=module,
            title="Lesson 1",
            content="Content 1",
            order_index=1
        )
        lesson3 = LessonTheory(
            module=module,
            title="Lesson 3",
            content="Content 3",
            order_index=3
        )

        with pytest.raises(ValidationError):
            lesson3.clean()


class TestRadioQuestionModel:

    def test_create_radio_question(self, db, module):
        question = LessonRadioQuestion.objects.create(
            module=module,
            title="Test Question",
            question_text="What is 2+2?",
            explanation="Basic math",
            points=5,
            order_index=1
        )
        assert question.title == "Test Question"
        assert question.points == 5
        assert question.get_correct_answer() is None
        assert str(question) == f"{module.title} - Test Question"

    def test_get_correct_answer(self, db, radio_question, radio_answers):
        correct = radio_question.get_correct_answer()
        assert correct is not None
        assert correct.text == "4"
        assert correct.is_correct is True


class TestAnswerOptionModel:

    def test_create_answer(self, db, radio_question):
        answer = AnswerOption.objects.create(
            question=radio_question,
            text="42",
            is_correct=False,
            order_index=1
        )
        assert answer.text == "42"
        assert answer.is_correct is False
        assert str(answer).startswith(radio_question.title[:50])

    def test_answer_ordering(self, db, radio_question):
        answer2 = AnswerOption.objects.create(
            question=radio_question,
            text="Answer 2",
            order_index=2
        )
        answer1 = AnswerOption.objects.create(
            question=radio_question,
            text="Answer 1",
            order_index=1
        )
        answers = AnswerOption.objects.all()
        assert answers[0] == answer1
        assert answers[1] == answer2


class TestCheckboxQuestionModel:

    def test_create_checkbox_question(self, db, module):
        question = LessonCheckBoxQuestion.objects.create(
            module=module,
            title="Checkbox Test",
            question_text="Select all that apply",
            points=10,
            order_index=1
        )
        assert question.title == "Checkbox Test"
        assert question.points == 10
        assert question.get_correct_answers().count() == 0
        assert str(question) == f"{module.title} - Checkbox Test"

    def test_get_correct_answers(self, db, checkbox_question, checkbox_answers):
        correct = checkbox_question.get_correct_answers()
        assert correct.count() == 2
        assert correct.filter(text="2").exists()
        assert correct.filter(text="4").exists()


class TestCheckboxAnswerOptionModel:

    def test_create_checkbox_answer(self, db, checkbox_question):
        answer = CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Option 1",
            is_correct=False,
            order_index=1
        )
        assert answer.text == "Option 1"
        assert answer.is_correct is False
        assert str(answer).startswith(checkbox_question.title[:50])

    def test_multiple_correct_answers_allowed(self, db, checkbox_question):
        answer1 = CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Answer 1",
            is_correct=True,
            order_index=1
        )
        answer2 = CheckBoxAnswerOption.objects.create(
            question=checkbox_question,
            text="Answer 2",
            is_correct=True,
            order_index=2
        )

        assert answer1.is_correct is True
        assert answer2.is_correct is True
        assert checkbox_question.get_correct_answers().count() == 2


class TestRelationships:

    def test_course_to_modules_relation(self, db, course):
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

        assert course.modules.count() == 2
        assert module1 in course.modules.all()
        assert module2 in course.modules.all()

    def test_module_to_lessons_relation(self, db, module):
        theory = LessonTheory.objects.create(
            module=module,
            title="Theory",
            content="Content",
            order_index=1
        )
        radio = LessonRadioQuestion.objects.create(
            module=module,
            title="Radio",
            question_text="Question",
            order_index=2
        )
        checkbox = LessonCheckBoxQuestion.objects.create(
            module=module,
            title="Checkbox",
            question_text="Question",
            order_index=3
        )

        assert module.lessons_theories.count() == 1
        assert module.lessons_radio_questions.count() == 1
        assert module.lessons_checkbox_questions.count() == 1
        assert theory in module.lessons_theories.all()
        assert radio in module.lessons_radio_questions.all()
        assert checkbox in module.lessons_checkbox_questions.all()

    def test_question_to_answers_relation(self, db, radio_question, radio_answers):
        assert radio_question.answers.count() == 4
        for answer in radio_answers:
            assert answer in radio_question.answers.all()


class TestValidation:

    def test_min_order_index_validator(self, db, module):
        with pytest.raises(ValidationError):
            lesson = LessonTheory(
                module=module,
                title="Invalid",
                content="Content",
                order_index=0
            )
            lesson.full_clean()

    def test_active_status_filtering(self, db, course, inactive_course):
        active_courses = Course.objects.filter(is_active=True)
        assert active_courses.count() == 1
        assert course in active_courses
        assert inactive_course not in active_courses