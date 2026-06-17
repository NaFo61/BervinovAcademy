from django.urls import path

from .views import (
    MentorChallengeDetailView,
    MentorCodeSubmissionsView,
    MentorCoursesOverviewView,
    MentorCourseStudentsView,
    MentorQuizAnswersView,
)

app_name = "mentoring"

urlpatterns = [
    path(
        "mentoring/courses/",
        MentorCoursesOverviewView.as_view(),
        name="courses-overview",
    ),
    path(
        "mentoring/courses/<uuid:course_public_id>/students/",
        MentorCourseStudentsView.as_view(),
        name="course-students",
    ),
    path(
        "mentoring/challenges/<uuid:challenge_public_id>/",
        MentorChallengeDetailView.as_view(),
        name="challenge-detail",
    ),
    path(
        "mentoring/code-submissions/",
        MentorCodeSubmissionsView.as_view(),
        name="code-submissions",
    ),
    path(
        "mentoring/quiz-answers/",
        MentorQuizAnswersView.as_view(),
        name="quiz-answers",
    ),
]
