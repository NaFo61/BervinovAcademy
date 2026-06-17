from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import CodingChallenge, Course

from .permissions import IsMentorOrAdmin
from .services import (
    build_challenge_detail_for_mentor,
    build_code_submissions_payload,
    build_course_students,
    build_courses_overview,
    build_quiz_answers_payload,
)


class MentorCoursesOverviewView(APIView):
    """``GET /api/mentoring/courses/`` — статистика по всем курсам."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        return Response(build_courses_overview())


class MentorCourseStudentsView(APIView):
    """``GET /api/mentoring/courses/{course_public_id}/students/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request, course_public_id):
        try:
            course = Course.objects.get(
                public_id=course_public_id, is_active=True
            )
        except Course.DoesNotExist:
            return Response({"detail": "Курс не найден."}, status=404)
        return Response(
            {
                "course_public_id": str(course.public_id),
                "course_title": course.title,
                "students": build_course_students(course),
            }
        )


class MentorCodeSubmissionsView(APIView):
    """
    ``GET /api/mentoring/code-submissions/``

    Фильтры: ``course_public_id``, ``user_public_id``, ``challenge_public_id``
    """

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        data = build_code_submissions_payload(
            course_public_id=request.query_params.get("course_public_id"),
            user_public_id=request.query_params.get("user_public_id"),
            challenge_public_id=request.query_params.get(
                "challenge_public_id"
            ),
        )
        return Response(data)


class MentorQuizAnswersView(APIView):
    """
    ``GET /api/mentoring/quiz-answers/``

    Фильтры: ``course_public_id``, ``user_public_id``
    """

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        data = build_quiz_answers_payload(
            course_public_id=request.query_params.get("course_public_id"),
            user_public_id=request.query_params.get("user_public_id"),
        )
        return Response(data)


class MentorChallengeDetailView(APIView):
    """``GET /api/mentoring/challenges/{challenge_public_id}/`` — задача со всеми тестами."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request, challenge_public_id):
        try:
            challenge = (
                CodingChallenge.objects.select_related("module", "course")
                .prefetch_related("test_cases")
                .get(public_id=challenge_public_id, is_active=True)
            )
        except CodingChallenge.DoesNotExist:
            return Response({"detail": "Задача не найдена."}, status=404)
        return Response(build_challenge_detail_for_mentor(challenge))
