from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action, display

from content.models import (
    AnswerOption,
    CheckBoxAnswerOption,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    Technology,
)


@admin.register(Technology)
class TechnologyAdmin(ModelAdmin):
    """Admin for technologies"""

    list_display = ("name", "courses_count", "is_used")
    search_fields = ("name",)
    list_per_page = 20
    ordering = ("name",)
    icon = "science"

    @admin.display(
        description=_("Number of courses"), ordering="courses_count"
    )
    def courses_count(self, obj):
        count = obj.courses.count()
        url = (
            reverse("admin:content_course_changelist")
            + f"?technology__id__exact={obj.id}"
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description=_("Is used"), boolean=True)
    def is_used(self, obj):
        return obj.courses.exists()


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    """Admin for courses"""

    list_display = (
        "title",
        "technologies_list",
        "modules_count",
        "is_active",
        "created_at",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "technology",
        "created_at",
    )
    search_fields = ("title", "description", "technology__name")
    list_per_page = 20
    ordering = ("-created_at",)
    filter_horizontal = ("technology",)
    readonly_fields = ("created_at", "courses_stats")
    prepopulated_fields = {"slug": ("title",)}
    icon = "school"

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "image",
                    "technology",
                    "is_active",
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("courses_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Technologies"))
    def technologies_list(self, obj):
        technologies = obj.technology.all()
        if not technologies:
            return "—"

        tech_links = []
        for tech in technologies[:3]:  # Show only first 3 technologies
            url = reverse(
                "admin:content_technology_change", args=[tech.id]
            )  # Исправлено
            tech_links.append(f'<a href="{url}">{tech.name}</a>')

        result = ", ".join(tech_links)
        if technologies.count() > 3:
            result += (
                '<span style="color: #666;">('
                f"+{technologies.count() - 3})</span>"
            )

        return format_html(result)

    @admin.display(description=_("Modules"))
    def modules_count(self, obj):
        count = obj.modules.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545;">{}</span>', count
            )

        url = (
            reverse("admin:content_module_changelist")
            + f"?course__id__exact={obj.id}"
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description=_("Statistics"))
    def courses_stats(self, obj):
        modules = obj.modules.count()
        lessons = LessonTheory.objects.filter(module__course=obj).count()

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.25rem;">
                <strong style="color: var(--primary-text);">
                {_('Modules')}:
                </strong>
                <span style="color: var(--secondary-text);">
                {modules}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Lessons')}:
                </strong>
                <span style="color: var(--secondary-text);">{lessons}</span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @display(description=_("Actions"), label=True)
    def actions_column(self, obj):
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;" title="{view_title}">
                    👁️
                </a>
                <a href="{edit}" style="color: #198754;" title="{edit_title}">
                    ✏️
                </a>
            </div>
            """,
            view=reverse(
                "admin:content_course_change", args=[obj.id]
            ),  # Исправлено
            edit=reverse(
                "admin:content_course_change", args=[obj.id]
            ),  # Исправлено
            view_title=_("View"),
            edit_title=_("Edit"),
        )

    @action(description=_("Activate courses ✅"), permissions=["change"])
    def activate_courses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} courses activated ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Deactivate courses ❌"), permissions=["change"])
    def deactivate_courses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} courses deactivated ❌"),
            messages.WARNING,
        )

    @action(description=_("Clone course"), permissions=["add"])
    def clone_course(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                _("Select only one course to clone"),
                messages.ERROR,
            )
            return

        course = queryset.first()
        course.pk = None
        course.title = f"{course.title} ({_('Copy')})"
        course.slug = f"{course.slug}-copy"
        course.is_active = False
        course.save()

        # Copy technologies
        course.technology.set(course.technology.all())

        self.message_user(
            request,
            _("Course successfully cloned"),
            messages.SUCCESS,
        )

    actions = ["activate_courses", "deactivate_courses", "clone_course"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("technology", "modules")


class LessonTheoryInline(TabularInline):
    """Inline for theory lessons"""

    model = LessonTheory
    extra = 1
    ordering = ("order_index",)
    show_change_link = True

    fields = ("title", "content_preview", "order_index", "is_active")
    readonly_fields = ("content_preview",)

    @admin.display(description=_("Content"))
    def content_preview(self, obj):
        if not obj.content:
            return "—"
        preview = (
            obj.content[:100] + "..."
            if len(obj.content) > 100
            else obj.content
        )
        return format_html('<span title="{}">{}</span>', obj.content, preview)


class LessonRadioQuestionInline(TabularInline):
    """Inline for radio questions in module"""

    model = LessonRadioQuestion
    extra = 1
    ordering = ("order_index",)
    show_change_link = True
    fields = (
        "title",
        "question_preview",
        "points",
        "order_index",
        "is_active",
    )
    readonly_fields = ("question_preview",)
    classes = ["collapse"]

    @admin.display(description=_("Question"))
    def question_preview(self, obj):
        if not obj.question_text:
            return "—"
        preview = (
            obj.question_text[:100] + "..."
            if len(obj.question_text) > 100
            else obj.question_text
        )
        return format_html(
            '<span title="{}">{}</span>', obj.question_text, preview
        )


class LessonCheckBoxQuestionInline(TabularInline):
    """Inline for checkbox questions in module"""

    model = LessonCheckBoxQuestion
    extra = 1
    ordering = ("order_index",)
    show_change_link = True
    fields = (
        "title",
        "question_preview",
        "points",
        "order_index",
        "is_active",
    )
    readonly_fields = ("question_preview",)
    classes = ["collapse"]

    @admin.display(description=_("Question"))
    def question_preview(self, obj):
        if not obj.question_text:
            return "—"
        preview = (
            obj.question_text[:100] + "..."
            if len(obj.question_text) > 100
            else obj.question_text
        )
        return format_html(
            '<span title="{}">{}</span>', obj.question_text, preview
        )


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    """Admin for modules"""

    list_display = (
        "title",
        "course_link",
        "lessons_count",
        "order_index",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "course",
    )
    search_fields = ("title", "description", "course__title")
    list_per_page = 20
    ordering = ("course", "order_index")
    readonly_fields = ("lessons_count_display",)
    icon = "list_alt"

    inlines = [
        LessonTheoryInline,
        LessonRadioQuestionInline,
        LessonCheckBoxQuestionInline,
    ]

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                    "order_index",
                    "is_active",
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("lessons_count_display",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Course"), ordering="course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.course.id]
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, obj.course.title)

    @admin.display(description=_("Lessons"))
    def lessons_count(self, obj):
        count = obj.lessons_theories.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545;">{}</span>', count
            )

        url = (
            reverse("admin:content_lessontheory_changelist")
            + f"?module__id__exact={obj.id}"
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description=_("Statistics"))
    def lessons_count_display(self, obj):
        theory_count = obj.lessons_theories.count()
        radio_count = obj.lessons_radio_questions.count()
        checkbox_count = obj.lessons_checkbox_questions.count()
        total = theory_count + radio_count + checkbox_count

        stats_html = f"""
            <div style="
                padding: 0.75rem;
                background: var(--primary-bg);
                border-radius: 0.375rem;
                border: 1px solid var(--border-color);
                font-size: 0.875rem;
            ">
                <div style="margin-bottom: 0.25rem;">
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #0d6efd;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Theory')}:</strong> {theory_count}
                </div>
                <div style="margin-bottom: 0.25rem;">
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #198754;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Radio')}:</strong> {radio_count}
                </div>
                <div>
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #ffc107;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Checkbox')}:</strong> {checkbox_count}
                </div>
                <hr style="margin: 0.5rem 0;
                border-color: var(--border-color);">
                <div>
                    <strong>{_('Total')}:</strong> {total}
                </div>
            </div>
            """
        return format_html(stats_html)

    @display(description=_("Actions"), label=True)
    def actions_column(self, obj):
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;" title="{view_title}">
                    👁️
                </a>
                <a href="{edit}" style="color: #198754;" title="{edit_title}">
                    ✏️
                </a>
            </div>
            """,
            view=reverse(
                "admin:content_module_change", args=[obj.id]
            ),  # Исправлено
            edit=reverse(
                "admin:content_module_change", args=[obj.id]
            ),  # Исправлено
            view_title=_("View"),
            edit_title=_("Edit"),
        )

    @action(description=_("Activate modules ✅"), permissions=["change"])
    def activate_modules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} modules activated ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Deactivate modules ❌"), permissions=["change"])
    def deactivate_modules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} modules deactivated ❌"),
            messages.WARNING,
        )

    actions = ["activate_modules", "deactivate_modules"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("course").prefetch_related(
            "lessons_theories"
        )


@admin.register(LessonTheory)
class LessonTheoryAdmin(ModelAdmin):
    """Admin for theory lessons"""

    list_display = (
        "title",
        "module_link",
        "course_link",
        "content_preview",
        "order_index",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "content",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("created_info",)
    icon = "article"

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "module",
                    "title",
                    "content",
                    "order_index",
                    "is_active",
                ),
            },
        ),
        (
            _("Additional information"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Content"))
    def content_preview(self, obj):
        if not obj.content:
            return "—"
        preview = (
            obj.content[:100] + "..."
            if len(obj.content) > 100
            else obj.content
        )
        return format_html('<span title="{}">{}</span>', obj.content, preview)

    @admin.display(description=_("Module"), ordering="module__title")
    def module_link(self, obj):
        url = reverse(
            "admin:content_module_change", args=[obj.module.id]
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Course"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )  # Исправлено
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Information"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Course')}:
                </strong>
                <span style="color:
                var(--secondary-text); margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Module')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Actions"), label=True)
    def actions_column(self, obj):
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;" title="{view_title}">
                    👁️
                </a>
                <a href="{edit}" style="color: #198754;" title="{edit_title}">
                    ✏️
                </a>
            </div>
            """,
            view=reverse(
                "admin:content_lessontheory_change", args=[obj.id]
            ),  # Исправлено
            edit=reverse(
                "admin:content_lessontheory_change", args=[obj.id]
            ),  # Исправлено
            view_title=_("View"),
            edit_title=_("Edit"),
        )

    @action(description=_("Activate lessons ✅"), permissions=["change"])
    def activate_lessons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} lessons activated ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Deactivate lessons ❌"), permissions=["change"])
    def deactivate_lessons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} lessons deactivated ❌"),
            messages.WARNING,
        )

    actions = ["activate_lessons", "deactivate_lessons"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("module", "module__course")


class AnswerOptionInline(TabularInline):
    """Inline for radio question answers"""

    model = AnswerOption
    extra = 2
    max_num = 10
    ordering = ("order_index",)
    fields = ("text", "is_correct", "order_index")
    classes = ["collapse"]

    def get_extra(self, request, obj=None, **kwargs):
        """Show 4 extra forms if no object exists"""
        if not obj:
            return 4
        return self.extra


class CheckBoxAnswerOptionInline(TabularInline):
    """Inline for checkbox question answers"""

    model = CheckBoxAnswerOption
    extra = 2
    max_num = 10
    ordering = ("order_index",)
    fields = ("text", "is_correct", "order_index")
    classes = ["collapse"]

    def get_extra(self, request, obj=None, **kwargs):
        """Show 4 extra forms if no object exists"""
        if not obj:
            return 4
        return self.extra


@admin.register(LessonRadioQuestion)
class LessonRadioQuestionAdmin(ModelAdmin):
    """Admin for radio button questions"""

    list_display = (
        "title",
        "module_link",
        "course_link",
        "answers_count",
        "correct_answer_preview",
        "points",
        "order_index",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "question_text",
        "explanation",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("question_stats", "created_info")
    icon = "radio_button_checked"

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "module",
                    "title",
                    "question_text",
                    "explanation",
                    "points",
                ),
            },
        ),
        (
            _("Order and status"),
            {
                "fields": (
                    "order_index",
                    "is_active",
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("question_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Additional information"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [AnswerOptionInline]

    @admin.display(description=_("Module"), ordering="module__title")
    def module_link(self, obj):
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Course"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Answers"))
    def answers_count(self, obj):
        count = obj.answers.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: 500;">⚠️ {}</span>',
                _("No answers"),
            )

        correct = obj.answers.filter(is_correct=True).count()
        if correct == 0:
            return format_html(
                '<span style="color: #ffc107;">{} {} (⚠️ {})</span>',
                count,
                _("answers"),
                _("no correct"),
            )
        elif correct > 1:
            return format_html(
                '<span style="color: #ffc107;">{} {} (⚠️ {} {})</span>',
                count,
                _("answers"),
                correct,
                _("correct"),
            )

        return format_html(
            '<span style="color: #198754;">{} {}</span>', count, _("answers")
        )

    @admin.display(description=_("Correct answer"))
    def correct_answer_preview(self, obj):
        correct = obj.get_correct_answer()
        if not correct:
            return format_html(
                '<span style="color: #dc3545;">❌ {}</span>',
                _("No correct answer"),
            )

        preview = (
            correct.text[:50] + "..."
            if len(correct.text) > 50
            else correct.text
        )
        return format_html(
            '<span style="color: #198754;">✅ {}</span>', preview
        )

    @admin.display(description=_("Statistics"))
    def question_stats(self, obj):
        total_answers = obj.answers.count()
        correct_answers = obj.answers.filter(is_correct=True).count()

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #0d6efd;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Total answers')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {total_answers}
                </span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #198754;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Correct answers')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {correct_answers}
                </span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @admin.display(description=_("Information"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Course')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Module')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Actions"), label=True)
    def actions_column(self, obj):
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;" title="{view_title}">
                    👁️
                </a>
                <a href="{edit}" style="color: #198754;" title="{edit_title}">
                    ✏️
                </a>
            </div>
            """,
            view=reverse(
                "admin:content_lessonradioquestion_change", args=[obj.id]
            ),
            edit=reverse(
                "admin:content_lessonradioquestion_change", args=[obj.id]
            ),
            view_title=_("View"),
            edit_title=_("Edit"),
        )

    @action(description=_("Activate questions ✅"), permissions=["change"])
    def activate_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} radio questions activated ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Deactivate questions ❌"), permissions=["change"])
    def deactivate_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} radio questions deactivated ❌"),
            messages.WARNING,
        )

    @action(description=_("Set points to 1"), permissions=["change"])
    def set_points_one(self, request, queryset):
        updated = queryset.update(points=1)
        self.message_user(
            request,
            _(f"{updated} questions updated to 1 point"),
            messages.SUCCESS,
        )

    @action(description=_("Set points to 5"), permissions=["change"])
    def set_points_five(self, request, queryset):
        updated = queryset.update(points=5)
        self.message_user(
            request,
            _(f"{updated} questions updated to 5 points"),
            messages.SUCCESS,
        )

    actions = [
        "activate_questions",
        "deactivate_questions",
        "set_points_one",
        "set_points_five",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "module", "module__course"
        ).prefetch_related("answers")


@admin.register(LessonCheckBoxQuestion)
class LessonCheckBoxQuestionAdmin(ModelAdmin):
    """Admin for checkbox questions"""

    list_display = (
        "title",
        "module_link",
        "course_link",
        "answers_count",
        "correct_answers_count",
        "points",
        "order_index",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "question_text",
        "explanation",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("question_stats", "created_info")
    icon = "check_box"

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "module",
                    "title",
                    "question_text",
                    "explanation",
                    "points",
                ),
            },
        ),
        (
            _("Order and status"),
            {
                "fields": (
                    "order_index",
                    "is_active",
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("question_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Additional information"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [CheckBoxAnswerOptionInline]

    @admin.display(description=_("Module"), ordering="module__title")
    def module_link(self, obj):
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Course"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Answers"))
    def answers_count(self, obj):
        count = obj.answers.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: 500;">⚠️ {}</span>',
                _("No answers"),
            )

        return format_html(
            '<span style="color: #0d6efd;">{} {}</span>', count, _("answers")
        )

    @admin.display(description=_("Correct"))
    def correct_answers_count(self, obj):
        correct = obj.answers.filter(is_correct=True).count()

        if correct == 0:
            return format_html('<span style="color: #dc3545;">❌ 0</span>')
        elif correct == 1:
            return format_html('<span style="color: #ffc107;">⚠️ 1</span>')

        return format_html(
            '<span style="color: #198754;">✅ {}</span>', correct
        )

    @admin.display(description=_("Statistics"))
    def question_stats(self, obj):
        total_answers = obj.answers.count()
        correct_answers = obj.answers.filter(is_correct=True).count()
        incorrect_answers = total_answers - correct_answers

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #0d6efd;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Total answers')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {total_answers}
                </span>
            </div>
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #198754;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">{_('Correct')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {correct_answers}
                </span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #dc3545;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Incorrect')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {incorrect_answers}
                </span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @admin.display(description=_("Information"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Course')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Module')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Actions"), label=True)
    def actions_column(self, obj):
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;" title="{view_title}">
                    👁️
                </a>
                <a href="{edit}" style="color: #198754;" title="{edit_title}">
                    ✏️
                </a>
            </div>
            """,
            view=reverse(
                "admin:content_lessoncheckboxquestion_change", args=[obj.id]
            ),
            edit=reverse(
                "admin:content_lessoncheckboxquestion_change", args=[obj.id]
            ),
            view_title=_("View"),
            edit_title=_("Edit"),
        )

    @action(description=_("Activate questions ✅"), permissions=["change"])
    def activate_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} checkbox questions activated ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Deactivate questions ❌"), permissions=["change"])
    def deactivate_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} checkbox questions deactivated ❌"),
            messages.WARNING,
        )

    actions = ["activate_questions", "deactivate_questions"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "module", "module__course"
        ).prefetch_related("answers")
