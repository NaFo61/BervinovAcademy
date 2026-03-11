import pytest

from users.models import User

from .conftest import make_user


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_user_with_email_only():
    user = make_user(email="ivan@academy.com", phone=None)
    assert user.email == "ivan@academy.com"
    assert user.is_active


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_user_with_phone_only():
    user = make_user(email=None, phone="+79123456789")
    assert user.phone == "+79123456789"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_user_without_email_and_phone_raises():
    with pytest.raises(ValueError):
        User.objects.create_user(
            email=None,
            phone=None,
            first_name="Иван",
            last_name="Иванов",
            password="password",
        )


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_user_normalizes_email():
    user = make_user(email="Ivan@ACADEMY.COM", phone=None)
    assert user.email == "ivan@academy.com"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.smoke
@pytest.mark.django_db
def test_create_superuser_sets_flags(admin_user):
    assert admin_user.is_staff
    assert admin_user.is_superuser
    assert admin_user.is_active
    assert admin_user.role == "admin"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_superuser_without_email_raises():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="",
            phone="+79123456789",
            password="password",
            first_name="Иван",
            last_name="Иванов",
        )


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_create_superuser_without_phone_raises():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="ivan@academy.com",
            phone=None,
            password="password",
            first_name="Иван",
            last_name="Иванов",
        )


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_get_by_natural_key_via_email():
    user = make_user(email="ivan@academy.com", phone=None)
    found = User.objects.get_by_natural_key("ivan@academy.com")
    assert found.pk == user.pk


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_get_by_natural_key_via_phone():
    user = make_user(email=None, phone="+79123456789")
    found = User.objects.get_by_natural_key("+79123456789")
    assert found.pk == user.pk


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.models
@pytest.mark.django_db
def test_get_by_natural_key_unknown_raises():
    with pytest.raises(User.DoesNotExist):
        User.objects.get_by_natural_key("ivan@academy.com")
