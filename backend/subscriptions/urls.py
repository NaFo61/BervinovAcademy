from django.urls import path

from .views import MySubscriptionView, ProPlanView

urlpatterns = [
    path(
        "subscriptions/plans/pro/",
        ProPlanView.as_view(),
        name="subscriptions-pro-plan",
    ),
    path(
        "subscriptions/me/",
        MySubscriptionView.as_view(),
        name="subscriptions-me",
    ),
]
