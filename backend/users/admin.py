from django.contrib import admin, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(ModelAdmin):
    """Красивая и аккуратная админка для управления пользователями."""

    form = UserChangeForm
    add_form = UserCreationForm

    # Отображение в списке
    list_display = (
        "email",
        "phone",
        "first_name",
        "last_name",
        "role",
        "is_active",
    )
    list_filter = ("role", "is_active")
    search_fields = ("email", "phone", "first_name", "last_name")
    ordering = ("-date_joined",)

    # Поля на странице редактирования пользователя
    fieldsets = (
        (_("Основная информация"), {"fields": ("email", "phone", "password")}),
        (
            _("Личная информация"),
            {"fields": ("first_name", "last_name", "avatar", "bio")},
        ),
        (
            _("Права доступа"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Системная информация"),
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    # Форма добавления пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")

    # Красивый значок в боковом меню Unfold
    icon = "person"

    # =============================
    #   Поддержка смены пароля 🔐
    # =============================

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.user_change_password),
                name="user_change_password",
            ),
        ]
        return custom_urls + urls

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        # Полностью убираем подсказку "Raw passwords are not stored..."
        if db_field.name == "password":
            formfield.help_text = ""
            formfield.label = _("Пароль")
        return formfield

    def user_change_password(self, request, id, form_url=""):
        user = self.get_object(request, id)
        if not user:
            messages.error(request, _("Пользователь не найден."))
            return redirect("..")

        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Пароль успешно изменён ✅"))
                return redirect(
                    reverse("admin:users_user_changelist")
                )  # ✅ переход в список пользователей
            else:
                messages.error(request, _("Ошибка при смене пароля."))
        else:
            form = AdminPasswordChangeForm(user)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Изменение пароля"),
            "form": form,
            "user": user,
        }
        return render(request, "admin/auth/user/change_password.html", context)

    class Media:
        css = {"all": ("css/base.css",)}
