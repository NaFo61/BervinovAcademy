from django.contrib import admin
from unfold.admin import ModelAdmin

from tutoring.models import (
    AvailabilityWindow,
    LedgerEntry,
    LessonAccess,
    LessonTariff,
    PaymentClaim,
    TutoringLesson,
    TutorSettings,
)


@admin.register(LessonAccess)
class LessonAccessAdmin(ModelAdmin):
    list_display = ("user", "enabled", "granted_by", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("user__email", "user__phone", "user__first_name")
    raw_id_fields = ("user", "granted_by")


@admin.register(TutorSettings)
class TutorSettingsAdmin(ModelAdmin):
    list_display = ("user", "timezone")
    search_fields = ("user__email",)


@admin.register(AvailabilityWindow)
class AvailabilityWindowAdmin(ModelAdmin):
    list_display = ("mentor", "weekday", "start_time", "end_time")
    list_filter = ("weekday",)
    raw_id_fields = ("mentor",)


@admin.register(LessonTariff)
class LessonTariffAdmin(ModelAdmin):
    list_display = ("mentor", "duration_minutes", "price_kop")
    raw_id_fields = ("mentor",)


@admin.register(TutoringLesson)
class TutoringLessonAdmin(ModelAdmin):
    list_display = (
        "starts_at",
        "student",
        "mentor",
        "status",
        "price_kop",
    )
    list_filter = ("status",)
    raw_id_fields = ("student", "mentor")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(ModelAdmin):
    list_display = ("created_at", "student", "mentor", "kind", "amount_kop")
    list_filter = ("kind",)
    raw_id_fields = ("student", "mentor", "lesson")


@admin.register(PaymentClaim)
class PaymentClaimAdmin(ModelAdmin):
    list_display = ("created_at", "student", "mentor", "amount_kop", "status")
    list_filter = ("status",)
    raw_id_fields = ("student", "mentor")
