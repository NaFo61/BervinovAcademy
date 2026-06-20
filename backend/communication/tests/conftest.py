"""Fixtures for communication tests."""

import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def mentor_user(db):
    return User.objects.create_user(
        email="mentor-conf@academy.com",
        phone="+79001110001",
        password="password",
        first_name="Ментор",
        last_name="Созвон",
        role="mentor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student-conf@academy.com",
        phone="+79001110002",
        password="password",
        first_name="Студент",
        last_name="Созвон",
        role="student",
    )


@pytest.fixture
def mentor_client(mentor_user):
    client = APIClient()
    client.force_authenticate(user=mentor_user)
    return client


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client
