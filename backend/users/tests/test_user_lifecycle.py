from django.core.exceptions import ValidationError
import pytest

from users.models import User
from .conftest import make_user


@pytest.mark.django_db
def test_student_role_clears_staff_and_superuser():
    user = make_user(role="student")
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_mentor_role_sets_staff_only():
    user = make_user(
        email="test@academy.com", phone="+79123456789", role="mentor"
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
        email="test@academy.com", phone="+79123456789", role="mentor"
    )
    assert user.is_staff

    user.role = "student"
    user.save()

    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_clean_raises_if_no_email_and_no_phone():
    user = User(first_name="Иван", last_name="Иванов", role="student")
    with pytest.raises(ValidationError):
        user.clean()


@pytest.mark.django_db
def test_clean_passes_with_email_only():
    user = User(
        first_name="Иван", last_name="Иванов", email="test@academy.com", role="student"
    )
    user.clean()


@pytest.mark.django_db
def test_clean_passes_with_phone_only():
    user = User(
        first_name="Иван", last_name="Иванов", phone="+79123456789", role="student"
    )
    user.clean()


@pytest.mark.django_db
def test_clean_admin_without_email_raises():
    user = User(
        first_name="Иван", last_name="Иванов", phone="+79123456789", role="admin"
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "email" in exc_info.value.message_dict


def test_clean_admin_without_phone_raises():
    user = User(
        first_name="Иван", last_name="Иванов", email="test@academy.com", role="admin"
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "phone" in exc_info.value.message_dict


def test_clean_superuser_flag_also_requires_email():
    user = User(
        first_name="Иван",
        last_name="Иванов",
        phone="+79123456789",
        role="student",
        is_superuser=True,
    )
    with pytest.raises(ValidationError) as exc_info:
        user.clean()
    assert "email" in exc_info.value.message_dict


@pytest.mark.django_db
def test_clean_duplicate_email_raises():
    make_user(email="test@academy.com")
    duplicate = User(
        first_name="Иван", last_name="Иванов", email="test@academy.com", role="student"
    )
    with pytest.raises(ValidationError) as exc_info:
        duplicate.clean()
    assert "email" in exc_info.value.message_dict


@pytest.mark.django_db
def test_clean_duplicate_phone_raises():
    make_user(phone="+79123456789")
    duplicate = User(
        first_name="Иван", last_name="Иванов", phone="+79123456789", role="student"
    )
    with pytest.raises(ValidationError) as exc_info:
        duplicate.clean()
    assert "phone" in exc_info.value.message_dict


@pytest.mark.django_db
def test_clean_update_own_email_does_not_raise():
    user = make_user(email="test@academy.com")
    user.first_name = "Пётр"
    user.clean()


@pytest.mark.django_db
def test_clean_update_own_phone_does_not_raise():
    user = make_user(phone="+79123456789")
    user.clean()
