from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .models import Entitlement, Plan, PromoCode, PromoRedemption


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


class PromoRedemptionInline(TabularInline):
    model = PromoRedemption
    extra = 0
    autocomplete_fields = ("user", "entitlement")
    readonly_fields = ("public_id", "created_at")


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = (
        "code",
        "duration_days",
        "is_active",
        "expires_at",
        "redemption_count",
        "max_redemptions",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "note")
    readonly_fields = ("public_id", "created_at")
    autocomplete_fields = ("created_by",)
    inlines = (PromoRedemptionInline,)

    @admin.display(description=_("Использовано"))
    def redemption_count(self, obj):
        return obj.redemptions.count()


@admin.register(PromoRedemption)
class PromoRedemptionAdmin(ModelAdmin):
    list_display = ("promo", "user", "created_at")
    search_fields = (
        "promo__code",
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("promo", "user", "entitlement")
    readonly_fields = ("public_id", "created_at")
