from typing import Any

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action

from translations.models import TranslationMemory


@admin.register(TranslationMemory)
class TranslationMemoryAdmin(ModelAdmin):
    list_display = (
        "short_source",
        "short_target",
        "source_lang",
        "target_lang",
        "context",
        "is_approved",
        "last_edited_by",
        "updated_at",
    )
    list_filter = (
        "source_lang",
        "target_lang",
        "is_approved",
        "context",
    )
    search_fields = ("source_text", "target_text", "context")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20
    ordering = ("-updated_at",)
    icon = "language"

    fieldsets = (
        (
            _("Translation info"),
            {
                "fields": (
                    "source_text",
                    "target_text",
                    ("source_lang", "target_lang"),
                    "context",
                    "is_approved",
                    "last_edited_by",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description=_("Source"))
    def short_source(self, obj: TranslationMemory):
        return (
            (obj.source_text[:60] + "…")
            if len(obj.source_text) > 60
            else obj.source_text
        )

    @admin.display(description=_("Target"))
    def short_target(self, obj: TranslationMemory):
        if not obj.target_text:
            return "—"
        return (
            (obj.target_text[:60] + "…")
            if len(obj.target_text) > 60
            else obj.target_text
        )

    @action(description=_("Mark as approved ✅"))
    def mark_as_approved(self, request: Any, queryset: Any) -> None:
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            _(f"{updated} translations marked as approved ✅"),
        )

    @action(description=_("Unapprove ❌"))
    def unapprove(self, request: Any, queryset: Any) -> None:
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            _(f"{updated} translations unapproved ❌"),
        )

    actions = ("mark_as_approved", "unapprove")

    def save_model(
        self, request: Any, obj: TranslationMemory, form: Any, change: bool
    ) -> None:
        if request.user.is_authenticated:
            obj.last_edited_by = request.user
        super().save_model(request, obj, form, change)
