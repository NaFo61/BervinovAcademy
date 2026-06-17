from django.shortcuts import get_object_or_404
from exams.models import ExamAttempt
from exams.serializers import ExamDetailSerializer, ExamShortSerializer
from exams.services import (
    ExamAccessError,
    finalize_attempt,
    get_exam_access,
    grant_exam_access,
    record_checkbox_answer,
    record_focus_event,
    record_radio_answer,
    record_theory_read,
    serialize_attempt,
    start_attempt,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import (
    CheckBoxAnswerOption,
    Exam,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
)
from mentoring.permissions import IsMentorOrAdmin
from progress.serializers import (
    CodeSubmissionCreateSerializer,
    CodeSubmissionSerializer,
)


class ExamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_pid = request.query_params.get("course_public_id")
        if not course_pid:
            return Response(
                {"detail": "Укажите course_public_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = Exam.objects.filter(
            course__public_id=course_pid,
            is_active=True,
        ).order_by("order_index")
        data = ExamShortSerializer(
            qs, many=True, context={"request": request}
        ).data
        return Response(data)


class ExamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_public_id):
        exam = get_object_or_404(
            Exam.objects.prefetch_related("prerequisite_modules"),
            public_id=exam_public_id,
            is_active=True,
        )
        return Response(
            ExamDetailSerializer(exam, context={"request": request}).data
        )


class ExamAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_public_id):
        exam = get_object_or_404(
            Exam, public_id=exam_public_id, is_active=True
        )
        return Response(get_exam_access(request.user, exam))


class ExamStartAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, exam_public_id):
        exam = get_object_or_404(
            Exam, public_id=exam_public_id, is_active=True
        )
        try:
            attempt = start_attempt(request.user, exam)
        except ExamAccessError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            serialize_attempt(attempt), status=status.HTTP_201_CREATED
        )


class ExamAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt.objects.select_related("exam", "exam__course"),
            public_id=attempt_public_id,
            user=request.user,
        )
        return Response(serialize_attempt(attempt))


class ExamAttemptSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        attempt = finalize_attempt(attempt, ExamAttempt.SubmitReason.MANUAL)
        return Response(serialize_attempt(attempt))


class ExamAttemptFocusEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        event_type = request.data.get("event_type", "visibility_hidden")
        result = record_focus_event(
            attempt,
            event_type=event_type,
            metadata=request.data.get("metadata"),
        )
        attempt.refresh_from_db()
        result["attempt"] = serialize_attempt(attempt)
        return Response(result)


class ExamAttemptTheoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        lesson_pid = request.data.get("lesson")
        lesson = get_object_or_404(
            LessonTheory,
            public_id=lesson_pid,
            exam=attempt.exam,
            is_active=True,
        )
        try:
            record_theory_read(attempt, lesson)
        except ExamAccessError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        attempt.refresh_from_db()
        return Response(serialize_attempt(attempt))


class ExamAttemptRadioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        question = get_object_or_404(
            LessonRadioQuestion,
            public_id=request.data.get("question"),
            exam=attempt.exam,
            is_active=True,
        )
        selected = get_object_or_404(
            RadioAnswerOption,
            public_id=request.data.get("selected_answer"),
            question=question,
        )
        try:
            record_radio_answer(attempt, question, selected)
        except ExamAccessError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        attempt.refresh_from_db()
        return Response(serialize_attempt(attempt))


class ExamAttemptCheckboxView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        question = get_object_or_404(
            LessonCheckBoxQuestion,
            public_id=request.data.get("question"),
            exam=attempt.exam,
            is_active=True,
        )
        pids = request.data.get("selected_answers") or []
        options = list(
            CheckBoxAnswerOption.objects.filter(
                public_id__in=pids,
                question=question,
            )
        )
        try:
            record_checkbox_answer(attempt, question, options)
        except ExamAccessError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        attempt.refresh_from_db()
        return Response(serialize_attempt(attempt))


class ExamAttemptCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_public_id):
        attempt = get_object_or_404(
            ExamAttempt,
            public_id=attempt_public_id,
            user=request.user,
        )
        payload = {
            "challenge": request.data.get("challenge"),
            "code": request.data.get("code"),
            "exam_attempt": str(attempt.public_id),
        }
        serializer = CodeSubmissionCreateSerializer(
            data=payload,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        from exams.services import record_coding_submission

        record_coding_submission(attempt, instance)
        attempt.refresh_from_db()
        out = CodeSubmissionSerializer(instance, context={"request": request})
        return Response(
            {
                "submission": out.data,
                "attempt": serialize_attempt(attempt),
            },
            status=status.HTTP_201_CREATED,
        )


class MentorExamAttemptsView(APIView):
    permission_classes = [IsMentorOrAdmin]

    def get(self, request):
        from exams.models import ExamFocusEvent

        course_pid = request.query_params.get("course_public_id")
        exam_pid = request.query_params.get("exam_public_id")
        qs = ExamAttempt.objects.select_related(
            "user",
            "exam",
            "exam__course",
        ).order_by("-started_at")
        if course_pid:
            qs = qs.filter(exam__course__public_id=course_pid)
        if exam_pid:
            qs = qs.filter(exam__public_id=exam_pid)

        rows = []
        for attempt in qs[:200]:
            focus_count = ExamFocusEvent.objects.filter(
                attempt=attempt
            ).count()
            rows.append(
                {
                    "public_id": str(attempt.public_id),
                    "exam_public_id": str(attempt.exam.public_id),
                    "exam_title": attempt.exam.title,
                    "course_public_id": str(attempt.exam.course.public_id),
                    "course_title": attempt.exam.course.title,
                    "student": {
                        "public_id": str(attempt.user.public_id),
                        "first_name": attempt.user.first_name,
                        "last_name": attempt.user.last_name,
                        "email": attempt.user.email,
                    },
                    "status": attempt.status,
                    "score": attempt.score,
                    "max_score": attempt.max_score,
                    "passed": attempt.passed,
                    "started_at": attempt.started_at.isoformat(),
                    "submitted_at": (
                        attempt.submitted_at.isoformat()
                        if attempt.submitted_at
                        else None
                    ),
                    "focus_events_count": focus_count,
                    "focus_warn_count": attempt.focus_warn_count,
                }
            )
        return Response(rows)


class MentorExamGrantView(APIView):
    permission_classes = [IsMentorOrAdmin]

    def post(self, request, exam_public_id):
        exam = get_object_or_404(
            Exam, public_id=exam_public_id, is_active=True
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user_pid = request.data.get("user_public_id")
        grant_type = request.data.get("grant_type", "retake")
        note = request.data.get("note", "")

        if grant_type not in ("unlock", "retake"):
            return Response(
                {"detail": "grant_type: unlock или retake"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(User, public_id=user_pid)
        grant = grant_exam_access(
            student,
            exam,
            granted_by=request.user,
            grant_type=grant_type,
            note=note,
        )
        from exams.serializers import ExamAccessGrantSerializer

        return Response(
            ExamAccessGrantSerializer(grant).data,
            status=status.HTTP_201_CREATED,
        )
