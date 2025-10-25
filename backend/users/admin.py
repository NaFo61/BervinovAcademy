from django.contrib import admin, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

User = get_user_model()


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].help_text = _(
            "Raw passwords are not stored, so there is no "
            "way to see this user's password, "
            "but you can change the password using "
            '<a href="../password/">this form</a>.'
        )


@admin.register(User)
class CustomUserAdmin(ModelAdmin):
    form = CustomUserChangeForm
    add_form = UserCreationForm

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
    readonly_fields = ("last_login", "date_joined")
    icon = "person"

    fieldsets = (
        (_("Main information"), {"fields": ("email", "phone", "password")}),
        (
            _("Personal information"),
            {"fields": ("first_name", "last_name", "avatar", "bio")},
        ),
        (
            _("Permissions"),
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
        (_("System information"), {"fields": ("last_login", "date_joined")}),
    )

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

    def user_change_password(self, request, id, form_url=""):
        user = self.get_object(request, id)
        if not user:
            messages.error(request, _("User not found."))
            return redirect("..")

        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Password successfully changed ✅"))
                return redirect(reverse("admin:users_user_changelist"))
            else:
                messages.error(request, _("Error while changing password."))
        else:
            form = AdminPasswordChangeForm(user)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Change password"),
            "form": form,
            "user": user,
        }
        return render(request, "admin/auth/user/change_password.html", context)
