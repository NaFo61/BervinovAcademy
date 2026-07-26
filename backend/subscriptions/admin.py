from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Entitlement, Plan


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ("code", "title", "duration_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "title")
    readonly_fields = ("public_id",)


@admin.register(Entitlement)
class EntitlementAdmin(ModelAdmin):
    list_display = (
        "user",
        "plan",
        "source",
        "starts_at",
        "ends_at",
        "expiry_reminder_sent_at",
        "revoked_at",
        "granted_by",
    )
    list_filter = ("source", "plan", "revoked_at")
    search_fields = (
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "note",
    )
    autocomplete_fields = ("user", "plan", "granted_by")
    readonly_fields = ("public_id",)
    actions = ("revoke_selected",)

    @admin.action(description=_("Отозвать выбранные выдачи"))
    def revoke_selected(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        self.message_user(
            request,
            _("Отозвано выдач: %(n)s") % {"n": updated},
            messages.SUCCESS,
        )
