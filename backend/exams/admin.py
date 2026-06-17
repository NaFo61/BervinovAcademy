from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from exams.models import ExamAccessGrant, ExamAttempt, ExamFocusEvent
from unfold.admin import ModelAdmin
from unfold.decorators import display

from content.admin import (
    CodingChallengeInline,
    LessonCheckBoxQuestionInline,
    LessonRadioQuestionInline,
    LessonTheoryInline,
    _format_lesson_counts,
    _lesson_counts_for_exam,
    _open_link,
)
from content.container_lessons import iter_container_lessons
from content.models import Exam


class ExamLessonTheoryInline(LessonTheoryInline):

    fk_name = "exam"

    verbose_name = _("Теория")

    verbose_name_plural = _("Теория")


class ExamLessonRadioInline(LessonRadioQuestionInline):

    fk_name = "exam"

    verbose_name = _("Вопрос (один ответ)")

    verbose_name_plural = _("Вопросы (один ответ)")


class ExamLessonCheckboxInline(LessonCheckBoxQuestionInline):

    fk_name = "exam"

    verbose_name = _("Вопрос (несколько ответов)")

    verbose_name_plural = _("Вопросы (несколько ответов)")


class ExamCodingChallengeInline(CodingChallengeInline):

    fk_name = "exam"

    verbose_name = _("Задача с кодом")

    verbose_name_plural = _("Задачи с кодом")

    def save_new(self, form, commit=True):

        obj = super(CodingChallengeInline, self).save_new(form, commit=False)

        if obj.exam_id:

            obj.course_id = obj.exam.course_id

        if commit:

            obj.save()

            form.save_m2m()

        return obj


@admin.register(Exam)
class ExamAdmin(ModelAdmin):

    list_display = (
        "title",
        "course_link",
        "lessons_count",
        "duration_minutes",
        "navigation_mode",
        "tab_policy",
        "is_active",
        "actions_column",
    )

    list_filter = ("is_active", "course", "navigation_mode", "tab_policy")

    search_fields = ("title", "description", "course__title")

    list_per_page = 20

    ordering = ("course", "order_index")

    filter_horizontal = ("prerequisite_modules",)

    readonly_fields = ("exam_lessons_outline", "lessons_count_display")

    icon = "assignment"

    inlines = [
        ExamLessonTheoryInline,
        ExamLessonRadioInline,
        ExamLessonCheckboxInline,
        ExamCodingChallengeInline,
    ]

    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                    "is_active",
                    "prerequisite_modules",
                ),
            },
        ),
        (
            _("Правила КР"),
            {
                "fields": (
                    "duration_minutes",
                    "navigation_mode",
                    "tab_policy",
                    "tab_warn_limit",
                    "mentor_unlock_required",
                    "pass_score_percent",
                ),
            },
        ),
        (
            _("Порядок заданий"),
            {
                "fields": ("exam_lessons_outline", "lessons_count_display"),
                "description": _(
                    "Порядковый номер (#) задаётся в таблицах ниже и общий "
                    "для теории, тестов и задач с кодом."
                ),
            },
        ),
    )

    @admin.display(description=_("Курс"), ordering="course__title")
    def course_link(self, obj):

        url = reverse("admin:content_course_change", args=[obj.course.id])

        return format_html('<a href="{}">{}</a>', url, obj.course.title)

    @admin.display(description=_("Задания"))
    def lessons_count(self, obj):

        theory, radio, checkbox, coding = _lesson_counts_for_exam(obj)

        return _format_lesson_counts(theory, radio, checkbox, coding)

    @admin.display(description=_("Статистика заданий"))
    def lessons_count_display(self, obj):

        return self.lessons_count(obj)

    @admin.display(description=_("Порядок заданий"))
    def exam_lessons_outline(self, obj):

        if not obj.pk:

            return "—"

        labels = {
            "theory": _("Теория"),
            "radio": _("Один ответ"),
            "checkbox": _("Несколько ответов"),
            "coding": _("Код"),
        }

        rows = []

        for kind, lesson in iter_container_lessons(obj):

            rows.append(
                f"<li><strong>#{lesson.order_index}</strong> "
                f"[{labels.get(kind, kind)}] {lesson.title}</li>"
            )

        if not rows:

            return format_html(
                '<span style="color: #dc3545;">{}</span>',
                _("Нет заданий — добавьте в таблицах ниже"),
            )

        return format_html(
            "<ol style='margin:0;padding-left:1.25rem'>{}</ol>", "".join(rows)
        )

    @display(description=_("Открыть"), label=True)
    def actions_column(self, obj):

        return _open_link(reverse("admin:content_exam_change", args=[obj.id]))


@admin.register(ExamAttempt)
class ExamAttemptAdmin(ModelAdmin):

    list_display = (
        "user",
        "exam",
        "status",
        "score",
        "max_score",
        "passed",
        "started_at",
        "submitted_at",
    )

    list_filter = ("status", "passed", "exam__course")

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "exam__title",
    )

    readonly_fields = (
        "public_id",
        "started_at",
        "expires_at",
        "submitted_at",
        "score",
        "max_score",
        "passed",
        "focus_warn_count",
    )

    icon = "history"


@admin.register(ExamAccessGrant)
class ExamAccessGrantAdmin(ModelAdmin):

    list_display = (
        "user",
        "exam",
        "grant_type",
        "granted_by",
        "is_active",
        "created_at",
    )

    list_filter = ("grant_type", "is_active", "exam__course")

    icon = "key"


@admin.register(ExamFocusEvent)
class ExamFocusEventAdmin(ModelAdmin):

    list_display = ("attempt", "event_type", "created_at")

    list_filter = ("event_type",)

    icon = "visibility_off"
