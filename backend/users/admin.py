from django.contrib import admin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin

from users.models import User

admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(ModelAdmin):
    list_display = (
        "email",
        "phone",
        "first_name",
        "last_name",
        "role",
        "is_active",
    )

    list_filter = (
        "role",
        "is_active",
    )
    search_fields = (
        "email",
        "phone",
        "first_name",
        "last_name",
    )

    fieldsets = (
        ("Основная информация", {"fields": ("email", "phone", "password")}),
        (
            "Личная информация",
            {"fields": ("first_name", "last_name", "avatar", "bio")},
        ),
        (
            "Роли и права",
            {"fields": ("role", "is_active", "is_staff", "is_superuser")},
        ),
    )
