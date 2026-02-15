"""
Тесты CustomUserManager
=======================
Покрывает логику создания пользователей и поиска по естественному ключу:

  - create_user:        email / phone / нормализация / ошибки
  - create_superuser:   обязательные поля / выставляемые флаги
  - get_by_natural_key: поиск по email, phone, несуществующий логин
"""

import pytest

from users.models import User

from .conftest import make_user

# ─────────────────────────────────────────────
# create_user
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_create_user_with_email_only():
    user = make_user(email="test@mail.com", phone=None)
    assert user.email == "test@mail.com"
    assert user.is_active


@pytest.mark.django_db
def test_create_user_with_phone_only():
    user = make_user(email=None, phone="+79001234567")
    assert user.phone == "+79001234567"


@pytest.mark.django_db
def test_create_user_without_email_and_phone_raises():
    with pytest.raises(ValueError):
        User.objects.create_user(
            email=None,
            phone=None,
            first_name="X",
            last_name="Y",
            password="pass",
        )


@pytest.mark.django_db
def test_create_user_normalizes_email():
    user = make_user(email="Test@EXAMPLE.COM", phone=None)
    assert user.email == "Test@example.com"


# ─────────────────────────────────────────────
# create_superuser
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_create_superuser_sets_flags(admin_user):
    assert admin_user.is_staff
    assert admin_user.is_superuser
    assert admin_user.is_active
    assert admin_user.role == "admin"


@pytest.mark.django_db
def test_create_superuser_without_email_raises():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="",
            phone="+70000000002",
            password="adminpass",
            first_name="A",
            last_name="B",
        )


@pytest.mark.django_db
def test_create_superuser_without_phone_raises():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin2@example.com",
            phone=None,
            password="adminpass",
            first_name="A",
            last_name="B",
        )


# ─────────────────────────────────────────────
# get_by_natural_key
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_get_by_natural_key_via_email():
    user = make_user(email="find@example.com", phone=None)
    found = User.objects.get_by_natural_key("find@example.com")
    assert found.pk == user.pk


@pytest.mark.django_db
def test_get_by_natural_key_via_phone():
    user = make_user(email=None, phone="+79991112233")
    found = User.objects.get_by_natural_key("+79991112233")
    assert found.pk == user.pk


@pytest.mark.django_db
def test_get_by_natural_key_unknown_raises():
    with pytest.raises(User.DoesNotExist):
        User.objects.get_by_natural_key("nobody@nowhere.com")
