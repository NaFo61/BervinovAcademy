from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    BoardAsset,
    ChatMessage,
    Conference,
    ConferenceLessonSummary,
    ConferenceWhiteboard,
    DirectThread,
    UserBoard,
    UserNotification,
)


@admin.register(UserBoard)
class UserBoardAdmin(ModelAdmin):
    list_display = ("owner", "updated_by", "updated_at", "has_drawing")
    search_fields = (
        "owner__email",
        "owner__first_name",
        "owner__last_name",
        "updated_by__email",
    )
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner", "updated_by")
    fields = ("owner", "updated_by", "created_at", "updated_at")

    @admin.display(description="Рисунок сохранён", boolean=True)
    def has_drawing(self, obj):
        return bool(obj and obj.snapshot_json)


@admin.register(ConferenceWhiteboard)
class ConferenceWhiteboardAdmin(ModelAdmin):
    list_display = ("conference", "exported_by", "exported_at", "created_at")
    search_fields = (
        "conference__room_name",
        "exported_by__email",
    )
    readonly_fields = ("exported_at", "created_at")


@admin.register(ConferenceLessonSummary)
class ConferenceLessonSummaryAdmin(ModelAdmin):
    list_display = (
        "conference",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(BoardAsset)
class BoardAssetAdmin(ModelAdmin):
    list_display = (
        "public_id",
        "original_name",
        "size",
        "uploaded_by",
        "created_at",
    )
    search_fields = ("original_name", "uploaded_by__email")
    readonly_fields = ("public_id", "created_at")


@admin.register(Conference)
class ConferenceAdmin(ModelAdmin):
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
class UserNotificationAdmin(ModelAdmin):
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
class DirectThreadAdmin(ModelAdmin):
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
class ChatMessageAdmin(ModelAdmin):
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
