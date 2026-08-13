from django.urls import path

from .views import MySubscriptionView, ProPlanView, RedeemPromoView

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
    path(
        "subscriptions/redeem/",
        RedeemPromoView.as_view(),
        name="subscriptions-redeem",
    ),
]
