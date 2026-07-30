import pytest

from content.models import Course, Module, Technology
from users.models import User


@pytest.fixture
def mentor_user(db):
    return User.objects.create_user(
        email="mentor-panel@academy.com",
        phone="+79001112233",
        password="password",
        first_name="Ментор",
        last_name="Тестов",
        role="mentor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student-panel@academy.com",
        phone="+79004445566",
        password="password",
        first_name="Студент",
        last_name="Тестов",
        role="student",
    )


@pytest.fixture
def technology(db):
    return Technology.objects.create(name="Python Mentoring")


@pytest.fixture
def course(db, technology, mentor_user):
    course = Course.objects.create(
        title="Mentor Course",
        description="For mentor panel tests",
        slug="mentor-course",
        is_active=True,
        mentor=mentor_user,
    )
    course.technology.add(technology)
    return course


@pytest.fixture
def module(db, course):
    return Module.objects.create(
        course=course,
        title="Module 1",
        description="Desc",
        is_active=True,
    )
