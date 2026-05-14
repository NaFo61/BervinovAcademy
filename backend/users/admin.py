from django.contrib import admin, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

from users.models import Mentor, Specialization, Student

User = get_user_model()


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].help_text = _(
            "Пароли не хранятся в открытом виде, поэтому невозможно "
            "увидеть пароль этого пользователя, "
            "но вы можете изменить пароль, используя "
            '<a href="../password/"><strong>эту форму</strong></a>.'
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
                )
            },
        ),
        (_("Системная информация"), {"fields": ("last_login", "date_joined")}),
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
        Использовать специальную форму при создании пользователя
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
            messages.error(request, _("Пользователь не найден."))
            return redirect("..")

        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Пароль успешно изменен ✅"))
                return redirect(reverse("admin:users_user_changelist"))
            else:
                messages.error(request, _("Ошибка при изменении пароля."))
        else:
            form = AdminPasswordChangeForm(user)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Смена пароля"),
            "form": form,
            "user": user,
        }
        return render(request, "admin/auth/user/change_password.html", context)


@admin.register(Specialization)
class SpecializationAdmin(ModelAdmin):
    list_display = ("display_title", "is_active")
    search_fields = (
        "title_ru",
        "title_en",
        "description_ru",
        "description_en",
    )
    list_filter = ("is_active",)

    @admin.display(description=_("Название"), ordering="title")
    def display_title(self, obj):
        lang = getattr(self, "_current_language", "en")
        if lang == "ru":
            return obj.title_ru or obj.title or "-"
        return obj.title_en or obj.title or "-"

    def get_fieldsets(self, request, obj=None):
        self._current_language = request.LANGUAGE_CODE
        lang = self._current_language

        # -----------------------------------------------------
        # 🔥 1. Если создаём новую специализацию — показываем только:
        # title, description, is_active
        # -----------------------------------------------------
        if obj is None:
            return (
                (
                    _("Создание специализации"),
                    {"fields": ["title", "description", "is_active"]},
                ),
            )

        # -----------------------------------------------------
        # 🔥 2. Если редактируем — как раньше
        # -----------------------------------------------------
        if lang == "ru":
            main_fields = ["is_active", "title_ru", "description_ru"]
        else:
            main_fields = ["is_active", "title_en", "description_en"]

        main_title = _("Основная информация")

        fieldsets = (
            (main_title, {"fields": main_fields}),
            (
                _("Все языковые версии (редактирование)"),
                {
                    "fields": [
                        "title",
                        "description",
                        "title_ru",
                        "title_en",
                        "description_ru",
                        "description_en",
                    ],
                    "classes": ("collapse",),
                    "description": _(
                        "Здесь вы можете отредактировать все языковые версии."
                    ),
                },
            ),
        )

        return fieldsets

    def changelist_view(self, request, extra_context=None):
        self._current_language = request.LANGUAGE_CODE
        return super().changelist_view(request, extra_context)


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

    @admin.display(description=_("Полное имя"))
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    @admin.display(description=_("Email"))
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_("Телефон"))
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Дата регистрации"))
    def date_joined(self, obj):
        return obj.user.date_joined


@admin.register(Mentor)
class MentorAdmin(ModelAdmin):
    list_display = (
        "id",
        "user_full_name",
        "specialization_display",
        "experience_years",
        "technologies_list",
        "user_email",
        "user_phone",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "specialization__title",
        "user__email",
        "user__phone",
        "technology__name",
    )
    list_filter = (
        "experience_years",
        "user__is_active",
        "specialization__type",
        "technology",
    )
    ordering = ("-user__date_joined",)
    icon = "briefcase"
    autocomplete_fields = ("specialization",)
    filter_horizontal = ("technology",)

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "user",
                    "specialization",
                    "experience_years",
                    "technology",
                )
            },
        ),
    )

    @admin.display(description=_("Полное имя"))
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    @admin.display(description=_("Email"))
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_("Телефон"))
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Специализация"))
    def specialization_display(self, obj):
        if obj.specialization:
            return f"{obj.specialization.type}: {obj.specialization.title}"
        return "—"

    @admin.display(description=_("Технологии"))
    def technologies_list(self, obj):
        technologies = obj.technology.all()
        if not technologies:
            return "—"

        from django.urls import reverse
        from django.utils.html import format_html

        tech_links = []
        for tech in technologies[:3]:
            url = reverse("admin:content_technology_change", args=[tech.id])
            tech_links.append(f'<a href="{url}">{tech.name}</a>')

        result = ", ".join(tech_links)
        if technologies.count() > 3:
            result += (
                '<span style="color: #666;">'
                f"(+{technologies.count() - 3})"
                "</span>"
            )

        return format_html(result)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "specialization")
            .prefetch_related("technology")
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "specialization":
            kwargs["queryset"] = Specialization.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
