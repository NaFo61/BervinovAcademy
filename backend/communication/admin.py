from django.contrib import admin

from .models import (
    ChatMessage,
    Conference,
    ConferenceWhiteboard,
    DirectThread,
    UserNotification,
)


@admin.register(ConferenceWhiteboard)
class ConferenceWhiteboardAdmin(admin.ModelAdmin):
    list_display = ("conference", "exported_by", "exported_at", "created_at")
    search_fields = (
        "conference__room_name",
        "exported_by__email",
    )
    readonly_fields = ("exported_at", "created_at")


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


@admin.register(DirectThread)
class DirectThreadAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "mentor",
        "student",
        "last_message_at",
        "created_at",
    )
    search_fields = (
        "mentor__email",
        "student__email",
        "mentor__first_name",
        "student__first_name",
    )
    readonly_fields = ("public_id", "created_at")
    raw_id_fields = ("mentor", "student")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "thread",
        "kind",
        "sender",
        "body_preview",
        "system_event",
        "is_deleted",
        "created_at",
    )
    list_filter = ("kind", "system_event", "is_deleted")
    search_fields = ("body", "sender__email", "thread__mentor__email")
    readonly_fields = ("public_id", "created_at", "edited_at")
    raw_id_fields = ("thread", "sender", "conference")

    @admin.display(description="Текст")
    def body_preview(self, obj):
        text = obj.body or ""
        return text[:80] + ("…" if len(text) > 80 else "")
