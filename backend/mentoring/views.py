from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import CodingChallenge, Course
from users.models import User

from .assignment import (
    assign_mentor_to_student,
    list_assignable_mentors,
    mentor_brief,
    resolve_student_mentor,
)
from .assistant import generate_assistant_reply
from .permissions import IsMentorOrAdmin
from .services import (
    build_challenge_detail_for_mentor,
    build_code_submissions_payload,
    build_course_students,
    build_courses_overview,
    build_quiz_answers_payload,
)


class MentorCoursesOverviewView(APIView):
    """``GET /api/mentoring/courses/`` — статистика по курсам ментора (admin — все)."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        return Response(build_courses_overview(request.user))


class MentorCourseStudentsView(APIView):
    """``GET /api/mentoring/courses/{course_public_id}/students/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request, course_public_id):
        from content.editor_registry import user_can_edit_course

        try:
            course = Course.objects.get(
                public_id=course_public_id, is_active=True
            )
        except Course.DoesNotExist:
            return Response({"detail": "Курс не найден."}, status=404)
        if not user_can_edit_course(request.user, course):
            return Response({"detail": "Нет доступа к курсу."}, status=403)
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


class MyMentorView(APIView):
    """``GET /api/mentoring/my-mentor/`` — ментор текущего студента."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, "role", None) != "student":
            return Response({"detail": "Эндпоинт для студентов."}, status=403)
        mentor, source = resolve_student_mentor(request.user)
        return Response(
            {
                "mentor": mentor_brief(mentor),
                "source": source,
            }
        )


class AssignableMentorsView(APIView):
    """``GET /api/mentoring/assignable-mentors/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        rows = [mentor_brief(u) for u in list_assignable_mentors()]
        return Response({"results": rows})


class AssignStudentMentorView(APIView):
    """``POST /api/mentoring/students/{user_public_id}/assign-mentor/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request, user_public_id):
        try:
            student = User.objects.get(public_id=user_public_id)
        except User.DoesNotExist:
            return Response({"detail": "Студент не найден."}, status=404)

        if "mentor_public_id" not in request.data:
            return Response(
                {"mentor_public_id": "Обязательное поле (или null)."},
                status=400,
            )
        raw = request.data.get("mentor_public_id")
        mentor = None
        if raw not in (None, ""):
            try:
                mentor = User.objects.get(public_id=raw)
            except User.DoesNotExist:
                return Response(
                    {"mentor_public_id": "Ментор не найден."}, status=400
                )

        profile = assign_mentor_to_student(
            student=student, mentor=mentor, actor=request.user
        )
        resolved, source = resolve_student_mentor(student)
        return Response(
            {
                "user_public_id": str(student.public_id),
                "assigned_mentor": mentor_brief(profile.assigned_mentor),
                "resolved_mentor": mentor_brief(resolved),
                "source": source,
            }
        )


class AssistantChatView(APIView):
    """``POST /api/mentoring/assistant/chat/`` — вопрос по текущему уроку."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "comments"

    def post(self, request):
        message = request.data.get("message") or ""
        history = request.data.get("history") or []
        context = request.data.get("context") or {}
        if not isinstance(history, list):
            return Response({"history": "Ожидается список."}, status=400)
        if not isinstance(context, dict):
            return Response({"context": "Ожидается объект."}, status=400)
        result = generate_assistant_reply(
            message=str(message),
            history=history,
            context=context,
        )
        return Response(result)
