from django.contrib import admin

from .models import Conference, UserNotification


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "mentor",
        "guest",
        "status",
        "created_at",
        "started_at",
        "ended_at",
    )
    list_filter = ("status",)
    search_fields = (
        "room_name",
        "mentor__email",
        "guest__email",
    )
    readonly_fields = ("public_id", "room_name", "created_at")


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "user",
        "kind",
        "title",
        "created_at",
        "read_at",
    )
    list_filter = ("kind",)
    search_fields = ("user__email", "title")
    readonly_fields = ("public_id", "created_at")
