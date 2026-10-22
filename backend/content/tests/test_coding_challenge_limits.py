"""Валидаторы лимитов CodingChallenge."""

from django.core.exceptions import ValidationError
import pytest

from content.models import CodingChallenge, Course


def _challenge(**kwargs):
    course = kwargs.pop("course")
    defaults = {
        "title": "lim",
        "description": "d",
        "instructions": "i",
        "solution_template": "print()",
        "course": course,
        "time_limit_ms": 2000,
        "memory_limit_mb": 256,
    }
    defaults.update(kwargs)
    return CodingChallenge(**defaults)


@pytest.mark.django_db
def test_time_and_memory_within_caps():
    course = Course.objects.create(title="Lim", slug="lim-caps")
    ch = _challenge(course=course, time_limit_ms=5000, memory_limit_mb=256)
    ch.full_clean()


@pytest.mark.django_db
def test_time_limit_above_cap_invalid():
    course = Course.objects.create(title="Lim2", slug="lim-caps-2")
    ch = _challenge(course=course, time_limit_ms=50_000)
    with pytest.raises(ValidationError):
        ch.full_clean()


@pytest.mark.django_db
def test_memory_limit_above_cap_invalid():
    course = Course.objects.create(title="Lim3", slug="lim-caps-3")
    ch = _challenge(course=course, memory_limit_mb=2048)
    with pytest.raises(ValidationError):
        ch.full_clean()
