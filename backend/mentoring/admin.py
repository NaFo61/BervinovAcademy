from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AssistantSettings


@admin.register(AssistantSettings)
class AssistantSettingsAdmin(ModelAdmin):
    """Один базовый промпт на школу."""

    fields = ("base_prompt",)

    def has_add_permission(self, request):
        return not AssistantSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
