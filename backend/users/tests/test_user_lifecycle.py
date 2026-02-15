"""
Тесты жизненного цикла модели User: save() и clean()
=====================================================
save()  — автоматическое выставление is_staff / is_superuser по роли
clean() — валидация контактных данных, уникальности и требований роли admin
"""

from django.core.exceptions import ValidationError
import pytest

from users.models import User

from .conftest import make_user

# ─────────────────────────────────────────────
# save(): роль → флаги доступа
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_student_role_clears_staff_and_superuser():
    user = make_user(role="student")
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_mentor_role_sets_staff_only():
    user = make_user(
        email="m@example.com", phone="+79006667788", role="mentor"
    )
    assert user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_admin_role_sets_staff_and_superuser(admin_user):
    assert admin_user.is_staff
    assert admin_user.is_superuser


@pytest.mark.django_db
def test_changing_role_from_mentor_to_student_resets_flags():
    user = make_user(
        email="change@example.com", phone="+79008880000", role="mentor"
    )
    assert user.is_staff

    user.role = "student"
    user.save()

    assert not user.is_staff
    assert not user.is_superuser


# ─────────────────────────────────────────────
# clean(): базовые контактные данные
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_clean_raises_if_no_email_and_no_phone():
    user = User(first_name="X", last_name="Y", role="student")
    with pytest.raises(ValidationError):
        user.clean()


@pytest.mark.django_db
def test_clean_passes_with_email_only():
    user = User(
        first_name="X", last_name="Y", email="ok@example.com", role="student"
    )
    # Не должно бросать исключение
    user.clean()


@pytest.mark.django_db
def test_clean_passes_with_phone_only():
    user = User(
        first_name="X", last_name="Y", phone="+79000000099", role="student"
    )
    user.clean()


# ─────────────────────────────────────────────
# clean(): требования роли admin
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_clean_admin_without_email_raises():
    user = User(
        first_name="A", last_name="B", phone="+79008889900", role="admin"
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "email" in exc_info.value.message_dict


def test_clean_admin_without_phone_raises():
    user = User(
        first_name="A", last_name="B", email="admin@example.com", role="admin"
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "phone" in exc_info.value.message_dict


def test_clean_superuser_flag_also_requires_email():
    user = User(
        first_name="A",
        last_name="B",
        phone="+79008889901",
        role="student",
        is_superuser=True,
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "email" in exc_info.value.message_dict


# ─────────────────────────────────────────────
# clean(): уникальность email и phone
# ─────────────────────────────────────────────


@pytest.mark.django_db
def test_clean_duplicate_email_raises():
    make_user(email="dup@example.com")
    duplicate = User(
        first_name="B", last_name="C", email="dup@example.com", role="student"
    )
    with pytest.raises(ValidationError) as exc_info:
        duplicate.clean()
    assert "email" in exc_info.value.message_dict


@pytest.mark.django_db
def test_clean_duplicate_phone_raises():
    make_user(phone="+79009990011")
    duplicate = User(
        first_name="B", last_name="C", phone="+79009990011", role="student"
    )
    with pytest.raises(ValidationError) as exc_info:
        duplicate.clean()
    assert "phone" in exc_info.value.message_dict


@pytest.mark.django_db
def test_clean_update_own_email_does_not_raise():
    """Обновление собственного email не должно блокироваться."""
    user = make_user(email="own@example.com")
    user.first_name = "Пётр"
    user.clean()  # не должно бросать исключение


@pytest.mark.django_db
def test_clean_update_own_phone_does_not_raise():
    """Обновление собственного phone не должно блокироваться."""
    user = make_user(phone="+79001230000")
    user.clean()  # не должно бросать исключение
