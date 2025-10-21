# users/admin.py
from django.contrib import admin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin

from .models import User

# Полностью отключаем Group из админки
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(ModelAdmin):
    list_display = [
        "email",
        "phone",
        "first_name",
        "last_name",
        "role",
        "is_active",
    ]

    list_filter = ["role", "is_active"]
    search_fields = ["email", "phone", "first_name", "last_name"]

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


# Убираем раздел "Пользователи и группы" из sidebar
UNFOLD = {
    "SITE_TITLE": "My Awesome Admin",
    "SITE_HEADER": "My Administration",
    # ... остальные настройки unfold
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,  # Показывать только нужные приложения
        "navigation": [
            {
                "title": "Пользователи",
                "items": [
                    {
                        "title": "Пользователи",
                        "icon": "person",
                        "link": "admin:users_user_changelist",
                    },
                ],
            },
        ],
    },
}
