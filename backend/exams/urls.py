from django.urls import path

from .views import (
    ExamAccessView,
    ExamAttemptCheckboxView,
    ExamAttemptCodeView,
    ExamAttemptDetailView,
    ExamAttemptFocusEventView,
    ExamAttemptRadioView,
    ExamAttemptSubmitView,
    ExamAttemptTheoryView,
    ExamDetailView,
    ExamListView,
    ExamStartAttemptView,
    MentorExamAttemptsView,
    MentorExamGrantView,
)

app_name = "exams"

urlpatterns = [
    path("exams/", ExamListView.as_view(), name="exam-list"),
    path(
        "exams/<uuid:exam_public_id>/",
        ExamDetailView.as_view(),
        name="exam-detail",
    ),
    path(
        "exams/<uuid:exam_public_id>/access/",
        ExamAccessView.as_view(),
        name="exam-access",
    ),
    path(
        "exams/<uuid:exam_public_id>/start/",
        ExamStartAttemptView.as_view(),
        name="exam-start",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/",
        ExamAttemptDetailView.as_view(),
        name="attempt-detail",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/submit/",
        ExamAttemptSubmitView.as_view(),
        name="attempt-submit",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/focus/",
        ExamAttemptFocusEventView.as_view(),
        name="attempt-focus",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/theory/",
        ExamAttemptTheoryView.as_view(),
        name="attempt-theory",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/radio/",
        ExamAttemptRadioView.as_view(),
        name="attempt-radio",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/checkbox/",
        ExamAttemptCheckboxView.as_view(),
        name="attempt-checkbox",
    ),
    path(
        "exams/attempts/<uuid:attempt_public_id>/code/",
        ExamAttemptCodeView.as_view(),
        name="attempt-code",
    ),
    path(
        "mentoring/exams/attempts/",
        MentorExamAttemptsView.as_view(),
        name="mentor-attempts",
    ),
    path(
        "mentoring/exams/<uuid:exam_public_id>/grant/",
        MentorExamGrantView.as_view(),
        name="mentor-grant",
    ),
]
