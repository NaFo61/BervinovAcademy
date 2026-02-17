from django.utils.translation import override
import pytest

from users.models import User


@pytest.fixture(autouse=True)
def set_english_language():
    with override("en"):
        yield


def make_user(**kwargs) -> User:

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
        email="test@academy.com",
        phone="+79010101010",
        role="mentor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="test@academy.com",
        phone="+70000000001",
        password="adminpass",
        first_name="Админ",
        last_name="Тестов",
    )
