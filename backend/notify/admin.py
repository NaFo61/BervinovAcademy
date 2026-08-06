from django.contrib import admin
from notify.models import PushSubscription
from unfold.admin import ModelAdmin


@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ("user", "endpoint", "created_at", "last_success_at")
    search_fields = ("user__email", "endpoint")
    readonly_fields = ("public_id", "created_at")
