from django.contrib import admin
from notify.models import PushSubscription, TelegramLinkToken
from unfold.admin import ModelAdmin


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(ModelAdmin):
    list_display = ("user", "token", "expires_at", "used_at", "created_at")
    search_fields = ("token", "user__email", "user__phone")
    readonly_fields = ("public_id", "created_at")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ("user", "endpoint", "created_at", "last_success_at")
    search_fields = ("user__email", "endpoint")
    readonly_fields = ("public_id", "created_at")
