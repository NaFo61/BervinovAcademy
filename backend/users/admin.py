# admin.py
from django.contrib import admin, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

from users.models import Mentor, Student, Specialization

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
            '<a href="../password/"><strong>this form</strong></a>.'
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

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

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


@admin.register(Specialization)
class SpecializationAdmin(ModelAdmin):
    list_display = (
        "type",
        "title",
        "is_active",
    )
    list_filter = ("type", "is_active")
    search_fields = ("title", "description")
    list_editable = ("is_active",)
    ordering = ("type", "title")
    icon = "tag"

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "type",
                    "title",
                    "description",
                    "is_active",
                )
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = (
        "id",
        "user_full_name",
        "user_email",
        "user_phone",
        "date_joined",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone",
    )
    list_filter = ("user__is_active",)
    ordering = ("-user__date_joined",)
    icon = "graduation-cap"

    @admin.display(description=_("Full name"))
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    @admin.display(description=_("Email"))
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_("Phone"))
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Data joined"))
    def date_joined(self, obj):
        return obj.user.date_joined


@admin.register(Mentor)
class MentorAdmin(ModelAdmin):
    list_display = (
        "id",
        "user_full_name",
        "specialization_display",
        "experience_years",
        "user_email",
        "user_phone",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "specialization__title",
        "user__email",
        "user__phone",
    )
    list_filter = (
        "experience_years",
        "user__is_active",
        "specialization__type",
    )
    ordering = ("-user__date_joined",)
    icon = "briefcase"
    autocomplete_fields = ("specialization",)

    fieldsets = (
        (
            _("Main information"),
            {"fields": ("user", "specialization", "experience_years")},
        ),
    )

    @admin.display(description=_("Full name"))
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    @admin.display(description=_("Email"))
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_("Phone"))
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Specialization"))
    def specialization_display(self, obj):
        if obj.specialization:
            return f"{obj.specialization.type}: {obj.specialization.title}"
        return "—"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'specialization'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "specialization":
            kwargs["queryset"] = Specialization.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)