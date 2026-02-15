from django.utils.translation import override
import pytest

from users.models import User


@pytest.fixture(autouse=True)
def set_english_language():
    with override("en"):
        yield


def make_user(**kwargs) -> User:
    """Создаёт и сохраняет пользователя с минимальными данными.

    По умолчанию — студент с email. Переопределяй только нужные поля:

        make_user(email=None, phone="+79001234567")
        make_user(email="m@example.com", phone="+79000000001", role="mentor")
    """
    defaults = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "role": "student",
    }
    defaults.update(kwargs)
    return User.objects.create_user(password="strongpass123", **defaults)


@pytest.fixture
def student_user(db):
    return make_user()


@pytest.fixture
def mentor_user(db):
    return make_user(
        email="mentor@example.com",
        phone="+79010101010",
        role="mentor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        phone="+70000000001",
        password="adminpass",
        first_name="Админ",
        last_name="Тестов",
    )
