import pytest

from users.models import User
from .conftest import make_user


@pytest.mark.django_db
def test_str_with_email(student_user):
    result = str(student_user)
    assert "Иван Иванов" in result
    assert "test@academy.com" in result


@pytest.mark.django_db
def test_str_with_phone_only():
    user = make_user(email=None, phone="+79123456789")
    assert "+79123456789" in str(user)


def test_str_no_contact_fallback():
    user = User(first_name="Иван", last_name="Иванов")
    assert "No contact" in str(user)


@pytest.mark.django_db
def test_get_full_name(student_user):
    assert student_user.get_full_name() == "Иван Иванов"


@pytest.mark.django_db
def test_get_short_name(student_user):
    assert student_user.get_short_name() == "Иван"


@pytest.mark.django_db
def test_get_username_prefers_email():
    user = make_user(phone="+79123456789")
    assert user.get_username() == "test@academy.com"


@pytest.mark.django_db
def test_get_username_falls_back_to_phone():
    user = make_user(email=None, phone="+79123456789")
    assert user.get_username() == "+79123456789"


@pytest.mark.django_db
def test_has_email_true(student_user):
    assert student_user.has_email


@pytest.mark.django_db
def test_has_email_false():
    user = make_user(email=None, phone="+79123456789")
    assert not user.has_email


@pytest.mark.django_db
def test_has_phone_true():
    user = make_user(phone="+79123456789")
    assert user.has_phone


@pytest.mark.django_db
def test_has_phone_false(student_user):
    assert not student_user.has_phone


@pytest.mark.django_db
def test_default_role_is_student(student_user):
    assert student_user.role == "student"


@pytest.mark.django_db
def test_is_student_true_others_false(student_user):
    assert student_user.is_student
    assert not student_user.is_mentor
    assert not student_user.is_admin


@pytest.mark.django_db
def test_is_mentor_true(mentor_user):
    assert mentor_user.is_mentor
    assert not mentor_user.is_student
    assert not mentor_user.is_admin


@pytest.mark.django_db
def test_is_admin_true_via_role(admin_user):
    assert admin_user.is_admin


@pytest.mark.django_db
def test_is_admin_true_via_superuser_flag(student_user):
    student_user.is_superuser = True
    assert student_user.is_admin
