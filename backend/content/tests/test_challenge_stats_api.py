"""Tests for challenge course-stats API."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import CodingChallenge


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def course_with_challenges(db, technology, module):
    course = module.course
    course.slug = "python-backend"
    course.save(update_fields=["slug"])
    CodingChallenge.objects.create(
        module=module,
        course=course,
        title="Hello World",
        description="desc",
        instructions="inst",
        solution_template="pass",
        difficulty="easy",
        points=10,
        order_index=1,
        is_active=True,
    )
    CodingChallenge.objects.create(
        module=module,
        course=course,
        title="FizzBuzz",
        description="desc",
        instructions="inst",
        solution_template="pass",
        difficulty="medium",
        points=20,
        order_index=2,
        is_active=True,
    )
    return course


@pytest.mark.django_db
class TestChallengeCourseStatsApi:
    def test_course_stats_by_slug(self, api_client, course_with_challenges):
        resp = api_client.get(
            "/api/content/challenges/course-stats/",
            {"course_slug": "python-backend"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["course_slug"] == "python-backend"
        assert resp.data["total_challenges"] == 2
        assert resp.data["total_points"] == 30
        assert resp.data["by_difficulty"]["easy"] == 1
        assert resp.data["by_difficulty"]["medium"] == 1
        assert len(resp.data["by_module"]) == 1
        assert resp.data["by_module"][0]["count"] == 2

    def test_course_stats_by_public_id(
        self, api_client, course_with_challenges
    ):
        course = course_with_challenges
        resp = api_client.get(
            "/api/content/challenges/course-stats/",
            {"course_public_id": str(course.public_id)},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["total_challenges"] == 2

    def test_course_stats_missing_param(self, api_client):
        resp = api_client.get("/api/content/challenges/course-stats/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_course_stats_unknown_slug(self, api_client):
        resp = api_client.get(
            "/api/content/challenges/course-stats/",
            {"course_slug": "no-such-course"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_course_stats_empty_course(self, api_client, course):
        course.slug = "empty-course"
        course.save(update_fields=["slug"])
        resp = api_client.get(
            "/api/content/challenges/course-stats/",
            {"course_slug": "empty-course"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["total_challenges"] == 0
        assert resp.data["total_points"] == 0
