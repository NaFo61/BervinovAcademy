from django.contrib import admin
from unfold.admin import ModelAdmin

from notify.models import PushSubscription, TelegramLinkToken


@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ("user", "endpoint", "created_at", "last_success_at")
    search_fields = ("user__email", "endpoint")
    readonly_fields = ("public_id", "created_at")


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "created_at")
    search_fields = ("user__email", "user__telegram_username")
    readonly_fields = ("public_id", "token", "created_at")
