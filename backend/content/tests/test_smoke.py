from django.contrib.admin.sites import site
from django.test import TestCase
import pytest

from content.models import Course, LessonTheory, Module, Technology


@pytest.mark.smoke
@pytest.mark.fast
class TestSmoke(TestCase):
    """Дымовые тесты для проверки работоспособности"""

    def test_models_import(self):
        """Проверка что все модели импортируются"""
        models = [Course, Technology, Module, LessonTheory]
        for model in models:
            assert model is not None
            assert model.__name__ in globals() or model.__name__ in locals()

    def test_admin_register(self):
        """Проверка что модели зарегистрированы в админке"""
        models = [Course, Technology, Module, LessonTheory]
        for model in models:
            assert (
                model in site._registry
            ), f"{model.__name__} не зарегистрирован в админке"

    def test_string_representation(self):
        """Быстрая проверка __str__ методов"""
        # Technology
        tech = Technology(name="Python")
        assert str(tech) == "Python"

        # Course
        course = Course(title="Django Course")
        assert str(course) == "Django Course"

        # Module
        module = Module(course=course, title="Basics")
        assert str(module) == "Django Course - Basics"

        # Lesson
        lesson = LessonTheory(module=module, title="Introduction")
        assert str(lesson) == "Basics - Introduction"

    def test_course_slug_generation(self):
        """Проверка создания slug без сохранения в БД"""
        course = Course(title="Test Course")
        course.save()  # Триггерит __str__ и save

        # Проверяем что slug создался и соответствует формату
        assert course.slug is not None
        assert isinstance(course.slug, str)
        assert len(course.slug) > 0

    def test_environment_variables(self):
        """Проверка что окружение настроено"""
        import django

        assert django.VERSION[:2] == (4, 2), "Не та версия Django"

        try:
            import unidecode

            assert unidecode is not None
        except ImportError:
            pytest.fail("Unidecode не установлен")
