from django.urls import path

from tutoring.views import (
    LessonAccessView,
    LessonActionView,
    LessonListView,
    MentorAvailabilityView,
    MentorStatsView,
    MentorTariffsView,
    MeView,
    PaymentClaimActionView,
    PaymentClaimListView,
    SlotListView,
)

urlpatterns = [
    path("tutoring/me/", MeView.as_view(), name="tutoring-me"),
    path("tutoring/slots/", SlotListView.as_view(), name="tutoring-slots"),
    path(
        "tutoring/lessons/", LessonListView.as_view(), name="tutoring-lessons"
    ),
    path(
        "tutoring/lessons/<uuid:public_id>/<str:action>/",
        LessonActionView.as_view(),
        name="tutoring-lesson-action",
    ),
    path(
        "tutoring/payment-claims/",
        PaymentClaimListView.as_view(),
        name="tutoring-claims",
    ),
    path(
        "tutoring/payment-claims/<uuid:public_id>/<str:action>/",
        PaymentClaimActionView.as_view(),
        name="tutoring-claim-action",
    ),
    path(
        "tutoring/availability/",
        MentorAvailabilityView.as_view(),
        name="tutoring-availability",
    ),
    path(
        "tutoring/tariffs/",
        MentorTariffsView.as_view(),
        name="tutoring-tariffs",
    ),
    path("tutoring/stats/", MentorStatsView.as_view(), name="tutoring-stats"),
    path(
        "tutoring/access/",
        LessonAccessView.as_view(),
        name="tutoring-access",
    ),
]
