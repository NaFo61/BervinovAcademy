import pytest
from django.test import TestCase
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from users.models import User, Student, Mentor, Specialization


@pytest.mark.smoke
@pytest.mark.user
class TestUserSmoke(TestCase):
    """Дымовые тесты для проверки системы пользователей"""

    def test_user_models_import(self):
        """Проверка импорта всех моделей пользователя"""
        models = [User, Student, Mentor, Specialization]
        for model in models:
            assert model is not None

    def test_user_admin_register(self):
        """Проверка регистрации моделей пользователей в админке"""
        models = [User, Student, Mentor, Specialization]
        for model in models:
            assert model in site._registry, f"Модель {model.__name__} не в админке"

    def test_user_string_representation(self):
        """Проверка строкового представления (метод __str__)"""
        # Тест User
        user = User(first_name="Ivan", last_name="Ivanov", email="ivan@test.com")
        assert str(user) == "Ivan Ivanov (ivan@test.com)"

        # Тест Specialization
        spec = Specialization(title="Backend")
        assert str(spec) == "Backend"

        # Тест Student
        student = Student(user=user)
        assert str(student) == "Ivan Ivanov"

    def test_role_logic_on_save(self):
        """Проверка автоматического назначения прав при сохранении (метод save)"""
        # Студент не должен быть персоналом
        student_user = User(email="student@test.com", role="student")
        student_user.save()
        assert student_user.is_staff is False
        assert student_user.is_superuser is False

        # Админ всегда персонал и суперюзер
        admin_user = User(
            email="admin@test.com",
            phone="+123456",
            role="admin",
            first_name="Admin"
        )
        admin_user.save()
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True

    def test_validation_logic(self):
        """Проверка базовых правил валидации (метод clean)"""
        # Проверка, что нельзя создать админа без телефона
        admin_no_phone = User(email="admin2@test.com", role="admin")
        with pytest.raises(ValidationError):
            admin_no_phone.clean()

        # Проверка, что нельзя создать пользователя вообще без контактов
        empty_user = User(first_name="No", last_name="Contacts")
        with pytest.raises(ValidationError):
            empty_user.clean()

    def test_avatar_path_generation(self):
        """Проверка генерации пути для аватара"""
        user = User(email="path@test.com")
        path = user.upload_to("old_photo.jpg")

        assert path.startswith("avatars/path@test.com/")
        assert path.endswith(".jpg")
