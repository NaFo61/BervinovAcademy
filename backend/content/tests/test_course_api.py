"""Tests for course list API."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from content.models import Course, Technology


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestCourseListApi:
    def test_list_all_active_courses(
        self, api_client, course, inactive_course
    ):
        resp = api_client.get("/api/content/courses/")
        assert resp.status_code == status.HTTP_200_OK
        titles = {row["title"] for row in resp.data}
        assert "Test Course" in titles
        assert "Inactive Course" not in titles

    def test_filter_by_technology_name(self, api_client, course, technology):
        js = Technology.objects.create(name="JavaScript")
        other = Course.objects.create(
            title="JS Course",
            description="desc",
            slug="js-course",
            is_active=True,
        )
        other.technology.add(js)

        resp = api_client.get(
            "/api/content/courses/", {"technology": "Python"}
        )
        assert resp.status_code == status.HTTP_200_OK
        titles = {row["title"] for row in resp.data}
        assert titles == {"Test Course"}

    def test_filter_technology_case_insensitive(self, api_client, course):
        resp = api_client.get(
            "/api/content/courses/", {"technology": "python"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1
        assert resp.data[0]["title"] == "Test Course"

    def test_filter_unknown_technology_returns_empty(self, api_client, course):
        resp = api_client.get("/api/content/courses/", {"technology": "Rust"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []
