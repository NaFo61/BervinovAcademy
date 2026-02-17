import pytest

from users.models import Mentor, Specialization, Student
from .conftest import make_user


@pytest.fixture
def specialization(db):
    return Specialization.objects.create(type="web", title="Backend")


@pytest.fixture
def student(student_user):
    return Student.objects.create(user=student_user)


@pytest.fixture
def mentor(mentor_user, specialization):
    return Mentor.objects.create(
        user=mentor_user,
        specialization=specialization,
        experience_years=5,
    )


@pytest.mark.django_db
def test_student_str(student):
    assert "Иван Иванов" in str(student)


@pytest.mark.django_db
def test_student_related_name(student_user, student):
    assert student_user.student_profile == student


@pytest.mark.django_db
def test_student_cascade_delete(student_user, student):
    user_pk = student_user.pk
    student_user.delete()
    assert not Student.objects.filter(user_id=user_pk).exists()


def test_student_db_table():
    assert Student._meta.db_table == "students"


def test_student_verbose_name():
    assert str(Student._meta.verbose_name) == "Student"


def test_student_verbose_name_plural():
    assert str(Student._meta.verbose_name_plural) == "Students"


@pytest.mark.django_db
def test_specialization_str(specialization):
    assert str(specialization) == "Backend"


def test_specialization_default_type_is_web():
    spec = Specialization(title="Без типа")
    assert spec.type == "web"


@pytest.mark.django_db
def test_specialization_default_is_active():
    spec = Specialization.objects.create(type="data", title="DS")
    assert spec.is_active


@pytest.mark.django_db
def test_specialization_description_can_be_blank():
    spec = Specialization.objects.create(type="design", title="UX")
    assert spec.description == ""


@pytest.mark.parametrize(
    "key",
    ["web", "mobile", "data", "design", "marketing", "business", "other"],
)
def test_specialization_type_choices_contain(key):
    valid = [t[0] for t in Specialization.TYPE_CHOICES]
    assert key in valid


@pytest.mark.parametrize("key", ["pending", "completed", "failed"])
def test_specialization_status_choices_contain(key):
    valid = [s[0] for s in Specialization.STATUS_CHOICES]
    assert key in valid


def test_specialization_title_is_translatable():
    assert "title" in Specialization.translatable_fields


def test_specialization_description_is_translatable():
    assert "description" in Specialization.translatable_fields


def test_specialization_db_table():
    assert Specialization._meta.db_table == "specializations"


def test_specialization_ordering():
    assert Specialization._meta.ordering == ["type", "title"]


def test_specialization_verbose_name():
    assert str(Specialization._meta.verbose_name) == "Specialization"


def test_specialization_verbose_name_plural():
    assert str(Specialization._meta.verbose_name_plural) == "Specializations"


@pytest.mark.django_db
def test_mentor_str_with_specialization(mentor):
    result = str(mentor)
    assert "Иван Иванов" in result
    assert "Backend" in result


@pytest.mark.django_db
def test_mentor_str_without_specialization(mentor_user):
    mentor = Mentor.objects.create(user=mentor_user, specialization=None)
    assert "—" in str(mentor)


@pytest.mark.django_db
def test_mentor_related_name(mentor_user, mentor):
    assert mentor_user.mentor_profile == mentor


@pytest.mark.django_db
def test_mentor_cascade_delete_user(mentor_user, mentor):
    user_pk = mentor_user.pk
    mentor_user.delete()
    assert not Mentor.objects.filter(user_id=user_pk).exists()


@pytest.mark.django_db
def test_mentor_delete_specialization_sets_null(mentor, specialization):
    specialization.delete()
    mentor.refresh_from_db()
    assert mentor.specialization is None


@pytest.mark.django_db
def test_mentor_technology_m2m_empty_by_default(mentor):
    assert mentor.technology.count() == 0


@pytest.mark.django_db
def test_mentor_experience_years_optional():
    user = make_user(
        email="test@academy.com", phone="+79123456789", role="mentor"
    )
    mentor = Mentor.objects.create(user=user)
    assert mentor.experience_years is None


def test_mentor_db_table():
    assert Mentor._meta.db_table == "mentors"


def test_mentor_verbose_name():
    assert str(Mentor._meta.verbose_name) == "Mentor"


def test_mentor_verbose_name_plural():
    assert str(Mentor._meta.verbose_name_plural) == "Mentors"
