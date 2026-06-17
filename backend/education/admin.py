from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = (
        "user",
        "course",
        "status",
        "started_at",
        "last_activity_at",
        "completed_at",
    )
    list_filter = ("status",)
    search_fields = (
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "course__title",
    )
    readonly_fields = (
        "public_id",
        "started_at",
        "last_activity_at",
    )
    autocomplete_fields = ("user", "course")
